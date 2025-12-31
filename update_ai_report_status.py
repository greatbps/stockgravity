#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI 리포트 status 관리
- stock_pool 상태 변화에 따라 AI 리포트 status 업데이트
- ACTIVE: 현재 모니터링 중 (monitoring, approved)
- DROPPED: 재평가 탈락 또는 거부 (rejected)
- TRADED: 실제 거래 진행 중 (trading, completed)
"""
from datetime import datetime
from db_config import get_db_connection


def sync_ai_report_status():
    """stock_pool 상태와 AI 리포트 상태 동기화"""
    print("\n" + "="*60)
    print("🔄 AI 리포트 상태 동기화 시작")
    print("="*60)
    print(f"실행 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    with get_db_connection() as conn:
        cur = conn.cursor()

        # 1. ACTIVE → DROPPED (rejected 종목)
        print("1️⃣ ACTIVE → DROPPED (rejected 종목 처리)")
        cur.execute("""
            UPDATE ai_analysis_reports
            SET status = 'DROPPED',
                drop_reason = sp.notes,
                status_updated_at = NOW()
            FROM stock_pool sp
            WHERE ai_analysis_reports.ticker = sp.ticker
              AND ai_analysis_reports.status = 'ACTIVE'
              AND sp.status = 'rejected'
        """)
        dropped_count = cur.rowcount
        print(f"   ✅ {dropped_count}개 리포트 DROPPED 처리\n")

        # 2. ACTIVE → TRADED (trading, completed 종목)
        print("2️⃣ ACTIVE → TRADED (거래 시작 종목 처리)")
        cur.execute("""
            UPDATE ai_analysis_reports
            SET status = 'TRADED',
                status_updated_at = NOW()
            FROM stock_pool sp
            WHERE ai_analysis_reports.ticker = sp.ticker
              AND ai_analysis_reports.status = 'ACTIVE'
              AND sp.status IN ('trading', 'completed')
        """)
        traded_count = cur.rowcount
        print(f"   ✅ {traded_count}개 리포트 TRADED 처리\n")

        # 3. DROPPED/TRADED → ACTIVE (재진입 종목)
        print("3️⃣ DROPPED/TRADED → ACTIVE (재진입 종목 처리)")
        cur.execute("""
            UPDATE ai_analysis_reports
            SET status = 'ACTIVE',
                drop_reason = NULL,
                status_updated_at = NOW()
            FROM stock_pool sp
            WHERE ai_analysis_reports.ticker = sp.ticker
              AND ai_analysis_reports.status IN ('DROPPED', 'TRADED')
              AND sp.status IN ('monitoring', 'approved')
        """)
        reactivated_count = cur.rowcount
        print(f"   ✅ {reactivated_count}개 리포트 ACTIVE 재설정\n")

        # 상태별 통계 조회
        print("="*60)
        print("📊 AI 리포트 상태 통계")
        print("="*60)

        cur.execute("""
            SELECT
                status,
                COUNT(*) as count,
                COUNT(DISTINCT ticker) as unique_tickers
            FROM ai_analysis_reports
            WHERE report_date >= CURRENT_DATE - INTERVAL '7 days'
            GROUP BY status
            ORDER BY status
        """)

        stats = cur.fetchall()
        for row in stats:
            status, count, unique = row
            print(f"{status:12s}: {count:3d}개 리포트 ({unique}개 종목)")

        print("="*60)

    return dropped_count, traded_count, reactivated_count


def show_recent_status_changes():
    """최근 상태 변경 내역 조회"""
    print("\n📋 최근 상태 변경 내역 (7일 이내)")
    print("-" * 60)

    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT
                ticker,
                status,
                drop_reason,
                status_updated_at
            FROM ai_analysis_reports
            WHERE status_updated_at IS NOT NULL
              AND status_updated_at >= CURRENT_DATE - INTERVAL '7 days'
            ORDER BY status_updated_at DESC
            LIMIT 20
        """)

        results = cur.fetchall()

        if not results:
            print("   변경 내역 없음")
        else:
            for row in results:
                ticker, status, reason, updated = row
                updated_str = updated.strftime('%Y-%m-%d %H:%M') if updated else 'N/A'
                print(f"{ticker} → {status:8s} | {updated_str}")
                if reason:
                    print(f"   사유: {reason[:80]}...")

    print("-" * 60)


def cleanup_old_dropped_reports():
    """30일 이상 지난 DROPPED 리포트 삭제"""
    print("\n🗑️  오래된 DROPPED 리포트 정리")
    print("-" * 60)

    with get_db_connection() as conn:
        cur = conn.cursor()

        # 30일 이상 경과한 DROPPED 리포트 삭제
        cur.execute("""
            DELETE FROM ai_analysis_reports
            WHERE status = 'DROPPED'
              AND status_updated_at < CURRENT_DATE - INTERVAL '30 days'
        """)

        deleted_count = cur.rowcount
        print(f"   ✅ {deleted_count}개 오래된 리포트 삭제 완료")

    print("-" * 60)


def main():
    """메인 실행"""
    # 1. 상태 동기화
    dropped, traded, reactivated = sync_ai_report_status()

    # 2. 최근 변경 내역 표시
    if dropped > 0 or traded > 0 or reactivated > 0:
        show_recent_status_changes()

    # 3. 오래된 리포트 정리
    cleanup_old_dropped_reports()

    print("\n✅ AI 리포트 상태 관리 완료!\n")


if __name__ == "__main__":
    main()
