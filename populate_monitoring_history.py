#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
모니터링 히스토리 데이터 생성 (실제 가격 데이터 기반)
"""
import pandas as pd
import numpy as np
from datetime import datetime
from db_config import get_db_connection


def calculate_rsi(prices, period=14):
    """RSI 계산"""
    deltas = np.diff(prices)
    seed = deltas[:period+1]
    up = seed[seed >= 0].sum() / period
    down = -seed[seed < 0].sum() / period
    rs = up / down if down != 0 else 0
    rsi = np.zeros_like(prices)
    rsi[:period] = 100. - 100. / (1. + rs)

    for i in range(period, len(prices)):
        delta = deltas[i - 1]
        if delta > 0:
            upval = delta
            downval = 0.
        else:
            upval = 0.
            downval = -delta

        up = (up * (period - 1) + upval) / period
        down = (down * (period - 1) + downval) / period
        rs = up / down if down != 0 else 0
        rsi[i] = 100. - 100. / (1. + rs)

    return rsi


def populate_history():
    """모니터링 히스토리 채우기"""
    print("\n" + "="*60)
    print("📊 모니터링 히스토리 생성 중...")
    print("="*60)

    # 1. stock_pool에서 종목 목록 가져오기
    with get_db_connection() as conn:
        pool_df = pd.read_sql(
            "SELECT ticker FROM stock_pool WHERE status='monitoring' ORDER BY final_score DESC LIMIT 100",
            conn
        )

    print(f"처리할 종목 수: {len(pool_df)}개")

    # 2. 가격 데이터 로드 (DB에서)
    print("가격 데이터 로드 중 (DB, 최근 90일)...")
    with get_db_connection() as conn:
        prices_df = pd.read_sql("""
            SELECT ticker, date, open, high, low, close, volume
            FROM daily_prices
            WHERE date >= CURRENT_DATE - INTERVAL '90 days'
            AND ticker IN (SELECT ticker FROM stock_pool WHERE status='monitoring')
            ORDER BY ticker, date
        """, conn)

    prices_df['date'] = pd.to_datetime(prices_df['date'])
    prices_df['ticker'] = prices_df['ticker'].astype(str).str.zfill(6)
    print(f"   ✅ {len(prices_df):,}행 로드")

    # 3. 각 종목별로 처리
    total_saved = 0

    with get_db_connection() as conn:
        cur = conn.cursor()

        for idx, row in pool_df.iterrows():
            ticker = row['ticker']

            # 해당 종목의 가격 데이터 필터링
            stock_data = prices_df[prices_df['ticker'] == ticker].copy()

            if len(stock_data) < 20:
                print(f"⚠️ {ticker}: 데이터 부족 (스킵)")
                continue

            # 최근 60일만
            stock_data = stock_data.sort_values('date').tail(60)

            # RSI 계산
            close_prices = stock_data['close'].values
            rsi_values = calculate_rsi(close_prices)

            # MA 계산
            stock_data['ma5'] = stock_data['close'].rolling(window=5).mean()
            stock_data['ma20'] = stock_data['close'].rolling(window=20).mean()
            stock_data['rsi'] = rsi_values

            # 변화율 계산
            stock_data['price_change'] = stock_data['close'].pct_change() * 100
            stock_data['volume_change'] = stock_data['volume'].pct_change() * 100

            # DB에 저장
            saved_days = 0
            for _, day_data in stock_data.iterrows():
                if pd.isna(day_data['rsi']) or pd.isna(day_data['ma20']):
                    continue

                try:
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
                    """, (
                        ticker,
                        day_data['date'].date(),
                        float(day_data['open']),
                        float(day_data['high']),
                        float(day_data['low']),
                        float(day_data['close']),
                        int(day_data['volume']),
                        float(day_data['price_change']) if pd.notna(day_data['price_change']) else None,
                        float(day_data['volume_change']) if pd.notna(day_data['volume_change']) else None,
                        float(day_data['ma5']) if pd.notna(day_data['ma5']) else None,
                        float(day_data['ma20']) if pd.notna(day_data['ma20']) else None,
                        float(day_data['rsi']) if pd.notna(day_data['rsi']) else None
                    ))
                    saved_days += 1
                except Exception as e:
                    print(f"⚠️ {ticker} {day_data['date'].date()} 저장 실패: {e}")
                    continue

            if saved_days > 0:
                total_saved += 1
                print(f"✅ {ticker}: {saved_days}일 저장")

    print(f"\n✅ 총 {total_saved}개 종목의 히스토리 생성 완료")
    return total_saved


if __name__ == "__main__":
    populate_history()
