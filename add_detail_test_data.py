#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""상세 페이지용 테스트 데이터 추가 (모니터링 히스토리 + AI 리포트)"""

from db_config import get_db_connection
from datetime import datetime, timedelta
import random

def add_monitoring_history():
    """모니터링 히스토리 테스트 데이터 추가"""

    # 삼성전자 (005930) 데이터
    ticker = '005930'
    base_price = 72000
    base_volume = 10000000

    with get_db_connection() as conn:
        cur = conn.cursor()

        # 최근 60일 데이터 생성
        for i in range(60, 0, -1):
            date = datetime.now() - timedelta(days=i)

            # 랜덤 가격 변동
            price_change = random.uniform(-0.03, 0.03)
            open_price = base_price * (1 + random.uniform(-0.02, 0.02))
            close_price = open_price * (1 + price_change)
            high_price = max(open_price, close_price) * (1 + random.uniform(0, 0.02))
            low_price = min(open_price, close_price) * (1 - random.uniform(0, 0.02))
            volume = base_volume * random.uniform(0.5, 1.5)

            # MA 계산 (간단히 현재가 기준 ±5%)
            ma5 = close_price * random.uniform(0.98, 1.02)
            ma20 = close_price * random.uniform(0.95, 1.05)

            # RSI (30~70 범위)
            rsi = random.uniform(30, 70)

            cur.execute("""
                INSERT INTO stock_monitoring_history
                (ticker, date, open, high, low, close, volume,
                 price_change, volume_change, ma5, ma20, rsi)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (ticker, date) DO UPDATE SET
                    open = EXCLUDED.open,
                    high = EXCLUDED.high,
                    low = EXCLUDED.low,
                    close = EXCLUDED.close,
                    volume = EXCLUDED.volume,
                    price_change = EXCLUDED.price_change,
                    volume_change = EXCLUDED.volume_change,
                    ma5 = EXCLUDED.ma5,
                    ma20 = EXCLUDED.ma20,
                    rsi = EXCLUDED.rsi
            """, (ticker, date.date(), open_price, high_price, low_price, close_price,
                  int(volume), price_change * 100, random.uniform(-20, 20),
                  ma5, ma20, rsi))

        print(f"✅ {ticker} 모니터링 히스토리 60일 추가")


def add_ai_reports():
    """AI 리포트 테스트 데이터 추가"""

    test_reports = [
        {
            'ticker': '005930',
            'summary': '삼성전자는 반도체 업황 회복과 함께 긍정적인 모멘텀을 보이고 있습니다. 최근 AI 칩 수요 증가로 실적 개선이 예상됩니다.',
            'recommendation': 'BUY',
            'confidence_score': 0.85,
            'momentum_analysis': '최근 5일간 상승 추세를 보이고 있으며, 거래량도 증가하고 있습니다. 기술적으로 MA5를 상향 돌파하며 강한 매수세를 나타냅니다.',
            'liquidity_analysis': '일평균 거래대금 8,500억원으로 충분한 유동성을 확보하고 있습니다. 외국인 매수세가 지속되고 있어 긍정적입니다.',
            'risk_factors': '환율 변동성과 글로벌 경기 둔화 우려가 리스크 요인입니다. 중국 반도체 산업 육성 정책도 모니터링이 필요합니다.'
        },
        {
            'ticker': '000660',
            'summary': 'SK하이닉스는 HBM 시장 선도 기업으로 AI 붐에 따른 수혜가 기대됩니다.',
            'recommendation': 'BUY',
            'confidence_score': 0.90,
            'momentum_analysis': '강한 상승 모멘텀과 함께 신고가를 경신하고 있습니다. 기관 및 외국인 동반 매수세가 강합니다.',
            'liquidity_analysis': '거래대금 4,500억원 수준으로 원활한 매매가 가능합니다.',
            'risk_factors': '높은 밸류에이션과 단기 과열 우려가 있습니다.'
        },
        {
            'ticker': '035420',
            'summary': 'NAVER는 검색광고 시장 정체와 경쟁 심화로 어려움을 겪고 있습니다.',
            'recommendation': 'HOLD',
            'confidence_score': 0.65,
            'momentum_analysis': '횡보 구간에서 방향성을 찾지 못하고 있습니다.',
            'liquidity_analysis': '충분한 유동성을 보유하고 있으나 매수세가 약합니다.',
            'risk_factors': '규제 리스크와 경쟁 심화가 주요 우려 사항입니다.'
        }
    ]

    with get_db_connection() as conn:
        cur = conn.cursor()

        for report in test_reports:
            cur.execute("""
                INSERT INTO ai_analysis_reports
                (ticker, report_date, summary, recommendation, confidence_score,
                 momentum_analysis, liquidity_analysis, risk_factors)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (ticker, report_date) DO UPDATE SET
                    summary = EXCLUDED.summary,
                    recommendation = EXCLUDED.recommendation,
                    confidence_score = EXCLUDED.confidence_score,
                    momentum_analysis = EXCLUDED.momentum_analysis,
                    liquidity_analysis = EXCLUDED.liquidity_analysis,
                    risk_factors = EXCLUDED.risk_factors
            """, (
                report['ticker'],
                datetime.now().date(),
                report['summary'],
                report['recommendation'],
                report['confidence_score'],
                report['momentum_analysis'],
                report['liquidity_analysis'],
                report['risk_factors']
            ))

        print(f"✅ {len(test_reports)}개 AI 리포트 추가")


if __name__ == "__main__":
    print("상세 페이지용 테스트 데이터 추가 중...")
    add_monitoring_history()
    add_ai_reports()
    print("\n✅ 모든 테스트 데이터 추가 완료!")
