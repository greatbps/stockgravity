#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
실시간 데이터 수집 (병렬 처리)
필터링된 500개 종목의 키움 API 데이터를 병렬로 수집
"""

import sys
import os
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any
import time
from datetime import datetime
from tqdm import tqdm

# kiwoom_trading 모듈 경로 추가
KIWOOM_PATH = '/home/greatbps/projects/kiwoom_trading'
if KIWOOM_PATH not in sys.path:
    sys.path.insert(0, KIWOOM_PATH)

try:
    from kiwoom_api import KiwoomAPI
except ImportError as e:
    print(f"❌ KiwoomAPI import 실패: {e}")
    print(f"경로 확인: {KIWOOM_PATH}")
    print("kiwoom_trading 프로젝트가 올바른 위치에 있는지 확인하세요.")
    sys.exit(1)


class RealtimeDataCollector:
    """실시간 데이터 병렬 수집기"""

    def __init__(self, max_workers: int = 10):
        """
        초기화

        Args:
            max_workers: 동시 실행 스레드 수 (기본 10개)
                        키움 API rate limit 고려하여 설정
        """
        self.max_workers = max_workers
        self.api = KiwoomAPI()
        self.results = []
        self.errors = []

    def fetch_stock_data(self, ticker: str, name: str) -> Dict[str, Any]:
        """
        단일 종목 데이터 조회

        Args:
            ticker: 종목코드 (6자리)
            name: 종목명

        Returns:
            종목 데이터 딕셔너리
        """
        try:
            # 현재가 조회
            price_data = self.api.get_stock_price(ticker)

            if price_data is None:
                return {
                    'ticker': ticker,
                    'name': name,
                    'status': 'failed',
                    'error': 'No data returned'
                }

            # 데이터 파싱
            result = {
                'ticker': ticker,
                'name': name,
                'timestamp': datetime.now(),
                'status': 'success'
            }

            # API 응답 구조에 따라 데이터 추출
            if isinstance(price_data, dict):
                # 주요 필드 추출 (실제 API 응답 구조에 맞게 조정 필요)
                result.update({
                    'current_price': price_data.get('stck_prpr', 0),  # 현재가
                    'open_price': price_data.get('stck_oprc', 0),     # 시가
                    'high_price': price_data.get('stck_hgpr', 0),     # 고가
                    'low_price': price_data.get('stck_lwpr', 0),      # 저가
                    'volume': price_data.get('acml_vol', 0),          # 누적거래량
                    'prev_close': price_data.get('stck_sdpr', 0),     # 전일종가
                    'change_rate': price_data.get('prdy_ctrt', 0),    # 전일대비율
                })

            return result

        except Exception as e:
            return {
                'ticker': ticker,
                'name': name,
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now()
            }

    def collect_parallel(self, stocks_df: pd.DataFrame) -> pd.DataFrame:
        """
        병렬로 여러 종목 데이터 수집

        Args:
            stocks_df: 필터링된 종목 DataFrame (ticker, name 컬럼 필수)

        Returns:
            실시간 데이터가 추가된 DataFrame
        """
        print(f"\n{'='*60}")
        print(f"실시간 데이터 수집 시작")
        print(f"대상 종목: {len(stocks_df)}개")
        print(f"병렬 처리: {self.max_workers} workers")
        print(f"{'='*60}\n")

        start_time = time.time()
        results = []
        errors = []

        # ThreadPoolExecutor로 병렬 처리
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 작업 제출
            future_to_stock = {
                executor.submit(
                    self.fetch_stock_data,
                    row['ticker'],
                    row['name']
                ): (row['ticker'], row['name'])
                for _, row in stocks_df.iterrows()
            }

            # 진행률 표시
            with tqdm(total=len(future_to_stock), desc="데이터 수집") as pbar:
                for future in as_completed(future_to_stock):
                    ticker, name = future_to_stock[future]
                    try:
                        result = future.result(timeout=10)

                        if result['status'] == 'success':
                            results.append(result)
                        else:
                            errors.append(result)

                    except Exception as e:
                        errors.append({
                            'ticker': ticker,
                            'name': name,
                            'status': 'exception',
                            'error': str(e)
                        })

                    pbar.update(1)

                    # Rate limit 방지: 100개마다 1초 대기
                    if pbar.n % 100 == 0:
                        time.sleep(1)

        elapsed_time = time.time() - start_time

        # 결과 요약
        print(f"\n{'='*60}")
        print(f"수집 완료!")
        print(f"  총 소요 시간: {elapsed_time:.1f}초")
        print(f"  성공: {len(results)}개")
        print(f"  실패: {len(errors)}개")
        print(f"  초당 처리: {len(stocks_df)/elapsed_time:.1f}개/초")
        print(f"{'='*60}\n")

        # DataFrame 생성
        if results:
            realtime_df = pd.DataFrame(results)

            # 원본 데이터와 병합
            merged_df = stocks_df.merge(
                realtime_df,
                on=['ticker', 'name'],
                how='left'
            )

            return merged_df
        else:
            print("⚠️ 수집된 데이터가 없습니다.")
            return stocks_df

    def save_results(self, df: pd.DataFrame, output_path: str = "realtime_stocks.csv"):
        """
        결과 저장

        Args:
            df: 저장할 DataFrame
            output_path: 출력 파일 경로
        """
        df.to_csv(output_path, index=False, encoding='utf-8-sig')
        print(f"✅ 실시간 데이터 저장: {output_path}")

        # 통계 출력
        if 'current_price' in df.columns:
            successful = df[df['status'] == 'success']
            if len(successful) > 0:
                print(f"\n📊 수집 통계:")
                print(f"  평균 현재가: {successful['current_price'].mean():,.0f}원")
                print(f"  평균 거래량: {successful['volume'].mean():,.0f}주")
                print(f"  평균 등락률: {successful['change_rate'].mean():.2f}%")


def main():
    """메인 실행 함수"""
    import argparse

    parser = argparse.ArgumentParser(description='실시간 데이터 수집 (병렬 처리)')
    parser.add_argument('--input', type=str, default='filtered_stocks.csv',
                       help='입력 파일 (필터링된 종목)')
    parser.add_argument('--output', type=str, default='realtime_stocks.csv',
                       help='출력 파일 (실시간 데이터 포함)')
    parser.add_argument('--workers', type=int, default=10,
                       help='병렬 처리 스레드 수 (기본: 10)')
    args = parser.parse_args()

    # 입력 파일 확인
    if not os.path.exists(args.input):
        print(f"❌ 입력 파일이 없습니다: {args.input}")
        print("먼저 quick_filter.py를 실행하여 종목을 필터링하세요.")
        return

    # 필터링된 종목 로드
    stocks_df = pd.read_csv(args.input)
    stocks_df['ticker'] = stocks_df['ticker'].astype(str).str.zfill(6)

    print(f"📂 입력 파일: {args.input}")
    print(f"📊 종목 수: {len(stocks_df)}개")

    # 데이터 수집
    collector = RealtimeDataCollector(max_workers=args.workers)

    try:
        result_df = collector.collect_parallel(stocks_df)
        collector.save_results(result_df, args.output)

        print(f"\n✅ 완료! 실시간 데이터가 추가된 파일: {args.output}")

    except KeyboardInterrupt:
        print("\n\n⚠️ 사용자에 의해 중단되었습니다.")
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
