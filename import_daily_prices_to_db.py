#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
daily_prices.csv를 DB로 일괄 임포트 (최초 1회)
"""
import pandas as pd
from db_config import get_db_connection
from datetime import datetime
import sys

def import_csv_to_db(csv_file='daily_prices.csv', batch_size=10000):
    """CSV 파일을 DB로 일괄 임포트"""
    print(f"\n{'='*60}")
    print(f"📥 {csv_file} → PostgreSQL 임포트 시작")
    print(f"{'='*60}\n")

    # CSV 로드
    print("1️⃣ CSV 파일 로딩...")
    try:
        df = pd.read_csv(csv_file, dtype={'ticker': str})
        print(f"   ✅ {len(df):,}행 로드 완료")
    except FileNotFoundError:
        print(f"   ❌ {csv_file} 파일을 찾을 수 없습니다")
        return False

    # 데이터 전처리
    print("\n2️⃣ 데이터 전처리...")
    df['ticker'] = df['ticker'].astype(str).str.zfill(6)
    df['date'] = pd.to_datetime(df['date'])

    # 중복 제거 (ticker, date 기준)
    before_count = len(df)
    df = df.drop_duplicates(subset=['ticker', 'date'], keep='last')
    after_count = len(df)
    if before_count != after_count:
        print(f"   ⚠️ 중복 제거: {before_count:,} → {after_count:,}행")

    # 정렬
    df = df.sort_values(['ticker', 'date'])
    print(f"   ✅ 전처리 완료: {len(df):,}행")
    print(f"   📅 날짜 범위: {df['date'].min()} ~ {df['date'].max()}")
    print(f"   📊 종목 수: {df['ticker'].nunique():,}개")

    # DB 저장
    print(f"\n3️⃣ DB 저장 중 (배치 크기: {batch_size:,})...")

    total_saved = 0
    total_updated = 0
    total_batches = (len(df) + batch_size - 1) // batch_size

    with get_db_connection() as conn:
        cur = conn.cursor()

        for i in range(0, len(df), batch_size):
            batch = df.iloc[i:i+batch_size]
            batch_num = i // batch_size + 1

            for _, row in batch.iterrows():
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
                    """, (
                        row['ticker'],
                        row['date'].date(),
                        float(row['open']) if pd.notna(row['open']) else None,
                        float(row['high']) if pd.notna(row['high']) else None,
                        float(row['low']) if pd.notna(row['low']) else None,
                        float(row['close']) if pd.notna(row['close']) else None,
                        int(row['volume']) if pd.notna(row['volume']) else None,
                        str(row['diff']) if pd.notna(row['diff']) else None
                    ))

                    if cur.rowcount == 1:
                        total_saved += 1
                    else:
                        total_updated += 1

                except Exception as e:
                    print(f"   ⚠️ {row['ticker']} {row['date'].date()} 저장 실패: {e}")
                    continue

            # 진행 상황 출력
            progress = (batch_num / total_batches) * 100
            print(f"   진행: {batch_num}/{total_batches} 배치 ({progress:.1f}%) | "
                  f"저장: {total_saved:,} | 업데이트: {total_updated:,}", end='\r')

        print()  # 줄바꿈
        conn.commit()

    print(f"\n{'='*60}")
    print(f"✅ 임포트 완료!")
    print(f"{'='*60}")
    print(f"   📝 신규 저장: {total_saved:,}행")
    print(f"   🔄 업데이트: {total_updated:,}행")
    print(f"   📊 총 처리: {total_saved + total_updated:,}행")

    # DB 통계 확인
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT
                COUNT(*) as total_rows,
                COUNT(DISTINCT ticker) as total_tickers,
                MIN(date) as min_date,
                MAX(date) as max_date
            FROM daily_prices
        """)
        stats = cur.fetchone()

        print(f"\n📊 DB 최종 통계:")
        print(f"   - 총 데이터: {stats[0]:,}행")
        print(f"   - 종목 수: {stats[1]:,}개")
        print(f"   - 기간: {stats[2]} ~ {stats[3]}")

    return True


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Import daily_prices.csv to PostgreSQL')
    parser.add_argument('--csv', default='daily_prices.csv', help='CSV file path')
    parser.add_argument('--batch', type=int, default=10000, help='Batch size')
    args = parser.parse_args()

    start_time = datetime.now()
    success = import_csv_to_db(args.csv, args.batch)

    if success:
        elapsed = (datetime.now() - start_time).total_seconds()
        print(f"\n⏱️  소요 시간: {elapsed:.1f}초")
    else:
        sys.exit(1)
