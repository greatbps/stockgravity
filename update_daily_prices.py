#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
일별 증분 업데이트: 최신 거래일 데이터만 수집하여 DB 업데이트
"""
import pandas as pd
import requests
from io import StringIO
from datetime import datetime, timedelta
from db_config import get_db_connection
from tqdm import tqdm
import time

def get_latest_trading_date():
    """DB에서 가장 최근 거래일 조회"""
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT MAX(date) FROM daily_prices")
        result = cur.fetchone()
        return result[0] if result[0] else None


def get_stock_list():
    """DB에 있는 모든 종목 코드 조회"""
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT DISTINCT ticker FROM daily_prices ORDER BY ticker")
        return [row[0] for row in cur.fetchall()]


def fetch_latest_price(ticker, target_date=None):
    """
    특정 종목의 최신 1일 데이터 가져오기 (네이버 증권)
    target_date: None이면 최신 데이터, 지정하면 해당 날짜 찾기
    """
    url = f"https://finance.naver.com/item/sise_day.nhn?code={ticker}&page=1"
    headers = {'User-Agent': 'Mozilla/5.0'}

    try:
        response = requests.get(url, headers=headers, timeout=10)
        tables = pd.read_html(StringIO(response.text))

        if not tables:
            return None

        df = tables[0].dropna()
        if df.empty:
            return None

        df['ticker'] = ticker
        df = df.rename(columns={
            '날짜': 'date', '종가': 'close', '전일비': 'diff',
            '시가': 'open', '고가': 'high', '저가': 'low', '거래량': 'volume'
        })
        df['date'] = pd.to_datetime(df['date'])

        # 최신 1일만
        latest = df.iloc[0:1]
        return latest

    except Exception as e:
        print(f"   ⚠️ {ticker} 조회 실패: {e}")
        return None


def update_incremental(limit_stocks=None):
    """증분 업데이트: 최신 데이터만 가져와서 DB에 추가/업데이트"""
    print(f"\n{'='*60}")
    print(f"🔄 일별 증분 업데이트 시작")
    print(f"{'='*60}\n")

    # 1. DB 최신 날짜 확인
    latest_db_date = get_latest_trading_date()
    print(f"1️⃣ DB 최신 거래일: {latest_db_date}")

    # 2. 종목 목록 가져오기
    stock_list = get_stock_list()
    if limit_stocks:
        stock_list = stock_list[:limit_stocks]
    print(f"2️⃣ 업데이트 대상: {len(stock_list)}개 종목")

    # 3. 각 종목의 최신 데이터 가져오기
    print(f"\n3️⃣ 최신 데이터 수집 중...")

    new_count = 0
    updated_count = 0
    skipped_count = 0
    error_count = 0

    with get_db_connection() as conn:
        cur = conn.cursor()

        for ticker in tqdm(stock_list, desc="수집 진행"):
            latest_data = fetch_latest_price(ticker)

            if latest_data is None or latest_data.empty:
                error_count += 1
                continue

            row = latest_data.iloc[0]
            data_date = row['date'].date()

            # DB에 이미 최신 데이터가 있으면 스킵
            if latest_db_date and data_date <= latest_db_date:
                skipped_count += 1
                continue

            # DB에 저장 (INSERT or UPDATE)
            try:
                cur.execute("""
                    INSERT INTO daily_prices
                    (ticker, date, open, high, low, close, volume, diff)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (ticker, date) DO UPDATE SET
                        open = EXCLUDED.open,
                        high = EXCLUDED.high,
                        low = EXCLUDED.low,
                        close = EXCLUDED.close,
                        volume = EXCLUDED.volume,
                        diff = EXCLUDED.diff,
                        created_at = CURRENT_TIMESTAMP
                    RETURNING (xmax = 0) AS inserted
                """, (
                    ticker,
                    data_date,
                    float(row['open']) if pd.notna(row['open']) else None,
                    float(row['high']) if pd.notna(row['high']) else None,
                    float(row['low']) if pd.notna(row['low']) else None,
                    float(row['close']) if pd.notna(row['close']) else None,
                    int(row['volume']) if pd.notna(row['volume']) else None,
                    str(row['diff']) if pd.notna(row['diff']) else None
                ))

                result = cur.fetchone()
                if result and result[0]:
                    new_count += 1
                else:
                    updated_count += 1

            except Exception as e:
                error_count += 1
                continue

            # Rate limiting (네이버 차단 방지)
            time.sleep(0.1)

        conn.commit()

    print(f"\n{'='*60}")
    print(f"✅ 증분 업데이트 완료!")
    print(f"{'='*60}")
    print(f"   📝 신규 추가: {new_count}개")
    print(f"   🔄 업데이트: {updated_count}개")
    print(f"   ⏭️  스킵: {skipped_count}개 (이미 최신)")
    print(f"   ❌ 실패: {error_count}개")

    # 최종 DB 상태 확인
    new_latest = get_latest_trading_date()
    print(f"\n📅 업데이트 후 최신 거래일: {new_latest}")

    return new_count + updated_count


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Incremental update of daily prices')
    parser.add_argument('--limit', type=int, help='Limit number of stocks to update')
    parser.add_argument('--no-cleanup', action='store_true', help='Skip cleanup of old data')
    parser.add_argument('--keep-days', type=int, default=200, help='Keep last N days (default: 200)')
    args = parser.parse_args()

    start_time = datetime.now()
    updated = update_incremental(args.limit)

    elapsed = (datetime.now() - start_time).total_seconds()
    print(f"\n⏱️  소요 시간: {elapsed:.1f}초")

    if updated == 0:
        print("\n💡 모든 데이터가 이미 최신입니다. 업데이트 불필요.")

    # 자동 정리 (200일 이상 된 데이터 삭제)
    if not args.no_cleanup:
        print(f"\n{'='*60}")
        print(f"🗑️  오래된 데이터 정리 중 (최근 {args.keep_days}일만 유지)...")
        print(f"{'='*60}")

        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute(f"""
                DELETE FROM daily_prices
                WHERE date < CURRENT_DATE - INTERVAL '{args.keep_days} days'
            """)
            deleted = cur.rowcount

            if deleted > 0:
                print(f"✅ {deleted:,}행 삭제 완료")

        # VACUUM은 별도 연결에서 (autocommit 모드)
        if deleted > 0:
            print(f"🔧 디스크 공간 회수 중...")
            import psycopg2
            import os as os_env
            from dotenv import load_dotenv

            load_dotenv()
            vacuum_conn = psycopg2.connect(
                host=os_env.getenv("DB_HOST", "localhost"),
                port=os_env.getenv("DB_PORT", "5432"),
                database=os_env.getenv("DB_NAME", "stockgravity"),
                user=os_env.getenv("DB_USER", "postgres"),
                password=os_env.getenv("DB_PASSWORD", "")
            )
            vacuum_conn.autocommit = True
            vacuum_cur = vacuum_conn.cursor()
            vacuum_cur.execute("VACUUM ANALYZE daily_prices")
            vacuum_cur.close()
            vacuum_conn.close()
            print(f"✅ 완료")
        else:
            print(f"✅ 정리할 데이터 없음 (이미 최근 {args.keep_days}일만 유지 중)")
