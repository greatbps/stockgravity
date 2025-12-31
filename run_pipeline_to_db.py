#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
StockGravity 파이프라인 - DB 저장 통합
"""
import subprocess
import sys
import pandas as pd
from datetime import datetime
from db_config import get_db_connection


def run_filtering(top_n=500):
    """1단계: 종목 필터링"""
    print("\n" + "="*60)
    print("1️⃣ 종목 필터링 (2,790개 → {}개)".format(top_n))
    print("="*60)

    result = subprocess.run(
        [sys.executable, "quick_filter.py", "--top", str(top_n)],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print("❌ 필터링 실패")
        print(result.stderr)
        return False

    print(result.stdout)
    print("✅ 필터링 완료")
    return True


def save_to_database():
    """필터링 결과를 DB에 저장 (일일 갱신 방식)"""
    print("\n" + "="*60)
    print("📊 DB 저장 중...")
    print("="*60)

    # CSV 파일 읽기
    try:
        df = pd.read_csv('filtered_stocks.csv')
        print(f"읽은 종목 수: {len(df)}")
    except FileNotFoundError:
        print("❌ filtered_stocks.csv 파일이 없습니다")
        return False

    # DB에 저장
    saved_count = 0
    with get_db_connection() as conn:
        cur = conn.cursor()

        # 1. 기존 stock_pool을 history로 백업
        print("\n1️⃣ 기존 stock_pool 백업 중...")
        cur.execute("""
            INSERT INTO stock_pool_history
            (ticker, name, close, trading_value, change_5d, vol_ratio,
             final_score, status, realtime_price, realtime_volume,
             realtime_updated_at, notes, added_date, snapshot_date)
            SELECT
                ticker, name, close, trading_value, change_5d, vol_ratio,
                final_score, status, realtime_price, realtime_volume,
                realtime_updated_at, notes, added_date, CURRENT_DATE
            FROM stock_pool
            ON CONFLICT (ticker, added_date, snapshot_date) DO NOTHING
        """)
        backup_count = cur.rowcount
        print(f"   ✅ {backup_count}행 백업 완료")

        # 2. monitoring 상태 종목만 삭제 (approved/trading/completed는 유지)
        print("\n2️⃣ monitoring 종목 삭제 중 (approved/trading/completed 유지)...")
        cur.execute("DELETE FROM stock_pool WHERE status = 'monitoring'")
        deleted_count = cur.rowcount
        print(f"   ✅ {deleted_count}행 삭제 완료 (approved/trading/completed 종목은 유지됨)")

        print("\n3️⃣ 새로운 500개 종목 저장 중...")

        for _, row in df.iterrows():
            try:
                cur.execute("""
                    INSERT INTO stock_pool
                    (ticker, name, close, trading_value, change_5d, vol_ratio, final_score, status, added_date)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, 'monitoring', CURRENT_DATE)
                    ON CONFLICT (ticker, added_date) DO UPDATE SET
                        name = EXCLUDED.name,
                        close = EXCLUDED.close,
                        trading_value = EXCLUDED.trading_value,
                        change_5d = EXCLUDED.change_5d,
                        vol_ratio = EXCLUDED.vol_ratio,
                        final_score = EXCLUDED.final_score
                        -- status는 유지 (approved 종목이 다시 필터링되어도 status 유지)
                """, (
                    str(row['ticker']).zfill(6),
                    row['name'],
                    float(row['close']),
                    int(row['trading_value']),
                    float(row['change_5d']),
                    float(row['vol_ratio']),
                    float(row['final_score'])
                ))
                saved_count += 1
            except Exception as e:
                print(f"⚠️ {row['ticker']} 저장 실패: {e}")
                continue

    print(f"✅ {saved_count}개 종목 DB 저장 완료")
    return True


def show_summary():
    """결과 요약 표시"""
    print("\n" + "="*60)
    print("📊 결과 요약")
    print("="*60)

    with get_db_connection() as conn:
        cur = conn.cursor()

        # 전체 종목 수
        cur.execute("SELECT COUNT(*) FROM stock_pool WHERE status='monitoring'")
        total = cur.fetchone()[0]
        print(f"✅ 모니터링 중인 종목: {total}개")

        # 점수 분포
        cur.execute("""
            SELECT
                MIN(final_score) as min_score,
                AVG(final_score) as avg_score,
                MAX(final_score) as max_score
            FROM stock_pool
            WHERE status='monitoring'
        """)
        scores = cur.fetchone()
        print(f"📈 점수 범위: {scores[0]:.1f} ~ {scores[2]:.1f} (평균 {scores[1]:.1f})")

        # Top 10
        cur.execute("""
            SELECT ticker, name, final_score, trading_value
            FROM stock_pool
            WHERE status='monitoring'
            ORDER BY final_score DESC
            LIMIT 10
        """)

        print("\n🏆 Top 10 종목:")
        print("-" * 60)
        for row in cur.fetchall():
            print(f"  {row[0]} {row[1]}: {row[2]:.1f}점 (거래대금 {row[3]/100000000:.0f}억)")


def run_ai_analysis(top_n=20):
    """AI 분석 자동 실행"""
    print("\n" + "="*60)
    print(f"4️⃣ AI 분석 시작 (Top {top_n}개 종목)")
    print("="*60)

    result = subprocess.run(
        [sys.executable, "generate_ai_report.py", "--top", str(top_n)],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print("⚠️ AI 분석 실패 (선택사항이므로 계속 진행)")
        print(result.stderr)
        return False

    print(result.stdout)
    print("✅ AI 분석 완료")
    return True


def main():
    """메인 파이프라인 실행"""
    print("\n" + "="*60)
    print("🚀 StockGravity 파이프라인 시작")
    print("="*60)
    print(f"시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 1. 필터링
    if not run_filtering(500):
        sys.exit(1)

    # 2. DB 저장
    if not save_to_database():
        sys.exit(1)

    # 3. 요약
    show_summary()

    # 4. AI 분석 (자동 실행)
    run_ai_analysis(20)

    print("\n" + "="*60)
    print("✅ 전체 파이프라인 완료!")
    print("="*60)
    print(f"종료 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\n다음 단계:")
    print("  - 대시보드에서 종목 확인: ./run.sh")
    print("  - AI 리포트 확인: AI Reports 페이지")
    print("  - 승인 종목 모니터링: Trading 페이지")


if __name__ == "__main__":
    main()
