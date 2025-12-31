#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
오래된 가격 데이터 정리 (200일 이상 된 데이터 삭제)
"""
from db_config import get_db_connection
from datetime import datetime

def cleanup_old_data(keep_days=200):
    """200일 이상 된 데이터 삭제"""
    print(f"\n{'='*60}")
    print(f"🗑️  {keep_days}일 이상 된 데이터 정리 중...")
    print(f"{'='*60}\n")

    with get_db_connection() as conn:
        cur = conn.cursor()

        # 삭제 전 현황
        cur.execute("SELECT COUNT(*), MIN(date), MAX(date) FROM daily_prices")
        before = cur.fetchone()
        print(f"정리 전: {before[0]:,}행 ({before[1]} ~ {before[2]})")

        # 200일 이전 데이터 삭제
        cur.execute(f"""
            DELETE FROM daily_prices
            WHERE date < CURRENT_DATE - INTERVAL '{keep_days} days'
        """)
        deleted = cur.rowcount

        # 삭제 후 현황
        cur.execute("SELECT COUNT(*), MIN(date), MAX(date) FROM daily_prices")
        after = cur.fetchone()

        print(f"\n✅ 삭제 완료: {deleted:,}행")
        print(f"정리 후: {after[0]:,}행 ({after[1]} ~ {after[2]})")
        print(f"절감: {(deleted/before[0]*100):.1f}%")

    # VACUUM은 별도 연결에서 (autocommit 모드)
    print(f"\n🔧 디스크 공간 회수 중...")
    import psycopg2
    import os
    from dotenv import load_dotenv

    load_dotenv()
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        database=os.getenv("DB_NAME", "stockgravity"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "")
    )
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute("VACUUM ANALYZE daily_prices")
    cur.close()
    conn.close()
    print(f"✅ 완료\n")

    return deleted

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Cleanup old price data')
    parser.add_argument('--days', type=int, default=200, help='Keep last N days')
    args = parser.parse_args()

    cleanup_old_data(args.days)
