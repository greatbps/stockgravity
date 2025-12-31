#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
재평가 로직 - Approved 종목 자동 재평가
- 3일 이상 보유 종목 대상
- 탈락 기준 체크 후 status 업데이트
- 최대 7일까지 보유
"""
import pandas as pd
from datetime import datetime, timedelta
from db_config import get_db_connection
from update_ai_report_status import sync_ai_report_status


def get_approved_stocks():
    """승인된 종목 조회 (approved_date, final_score 포함)"""
    query = """
    SELECT
        ticker,
        name,
        final_score,
        approved_date,
        EXTRACT(DAY FROM (NOW() - approved_date)) as days_held
    FROM stock_pool
    WHERE status = 'approved'
    ORDER BY approved_date ASC
    """
    with get_db_connection() as conn:
        df = pd.read_sql(query, conn)
    return df


def get_latest_rsi_ma5(ticker):
    """최신 RSI, close, MA5 조회"""
    query = """
    SELECT rsi, close, ma5
    FROM stock_monitoring_history
    WHERE ticker = %s AND rsi IS NOT NULL
    ORDER BY date DESC
    LIMIT 1
    """
    with get_db_connection() as conn:
        result = pd.read_sql(query, conn, params=(ticker,))

    if len(result) == 0:
        return None, None, None

    return result.iloc[0]['rsi'], result.iloc[0]['close'], result.iloc[0]['ma5']


def get_volume_averages(ticker):
    """3일 평균 거래량 vs 60일 평균 거래량"""
    query = """
    SELECT
        AVG(volume) FILTER (WHERE date >= CURRENT_DATE - INTERVAL '3 days') as avg_3d,
        AVG(volume) FILTER (WHERE date >= CURRENT_DATE - INTERVAL '60 days') as avg_60d
    FROM stock_monitoring_history
    WHERE ticker = %s
    """
    with get_db_connection() as conn:
        result = pd.read_sql(query, conn, params=(ticker,))

    if len(result) == 0:
        return None, None

    return result.iloc[0]['avg_3d'], result.iloc[0]['avg_60d']


def is_in_top_100(ticker):
    """현재 Stock Pool Top 100 내에 있는지 확인"""
    query = """
    SELECT COUNT(*) as rank
    FROM (
        SELECT ticker, ROW_NUMBER() OVER (ORDER BY final_score DESC) as rn
        FROM stock_pool
        WHERE status = 'monitoring'
        AND added_date = CURRENT_DATE
    ) ranked
    WHERE ticker = %s AND rn <= 100
    """
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(query, (ticker,))
        result = cur.fetchone()

    return result[0] > 0 if result else False


def get_initial_score(ticker, approved_date):
    """승인 당시의 final_score 조회 (stock_pool_history에서)"""
    query = """
    SELECT final_score
    FROM stock_pool_history
    WHERE ticker = %s
      AND snapshot_date = %s
    ORDER BY snapshot_date DESC
    LIMIT 1
    """
    with get_db_connection() as conn:
        result = pd.read_sql(query, conn, params=(ticker, approved_date.date()))

    if len(result) == 0:
        # history에 없으면 현재 stock_pool의 값 사용
        query2 = "SELECT final_score FROM stock_pool WHERE ticker = %s"
        with get_db_connection() as conn:
            result = pd.read_sql(query2, conn, params=(ticker,))

    return result.iloc[0]['final_score'] if len(result) > 0 else None


def evaluate_stock(ticker, name, current_score, initial_score, days_held):
    """종목 재평가 - 탈락 기준 체크"""
    drop_reasons = []

    # 1. 최대 보유 기간 (7일)
    if days_held >= 7:
        drop_reasons.append(f"최대 보유 기간 초과 ({days_held}일 >= 7일)")

    # 재평가 대상 (3일 이상)만 상세 평가
    if days_held < 3:
        return False, []  # 3일 미만은 재평가 제외

    # 2. final_score 20% 이상 하락
    if initial_score and current_score:
        score_change = ((current_score - initial_score) / initial_score) * 100
        if score_change < -20:
            drop_reasons.append(f"점수 20% 이상 하락 ({score_change:.1f}%)")

    # 3. RSI > 75 AND close < MA5
    rsi, close, ma5 = get_latest_rsi_ma5(ticker)
    if rsi and close and ma5:
        if rsi > 75 and close < ma5:
            drop_reasons.append(f"과매수 + 하락 신호 (RSI={rsi:.1f} > 75, 종가 < MA5)")

    # 4. 거래량 급감 (3일 평균 < 60일 평균 * 50%)
    avg_3d, avg_60d = get_volume_averages(ticker)
    if avg_3d and avg_60d:
        volume_ratio = (avg_3d / avg_60d) * 100
        if volume_ratio < 50:
            drop_reasons.append(f"거래량 급감 (3일 평균 = 60일 평균의 {volume_ratio:.1f}%)")

    # 5. Top 100 탈락
    if not is_in_top_100(ticker):
        drop_reasons.append("Stock Pool Top 100 탈락")

    # 탈락 여부 결정
    should_drop = len(drop_reasons) > 0

    return should_drop, drop_reasons


def update_stock_status(ticker, new_status, drop_reason=None):
    """종목 상태 업데이트"""
    with get_db_connection() as conn:
        cur = conn.cursor()

        if drop_reason:
            cur.execute(
                """
                UPDATE stock_pool
                SET status = %s, notes = COALESCE(notes, '') || %s
                WHERE ticker = %s
                """,
                (new_status, f"\n[재평가 탈락] {drop_reason}", ticker)
            )
        else:
            cur.execute(
                "UPDATE stock_pool SET status = %s WHERE ticker = %s",
                (new_status, ticker)
            )


def main():
    """재평가 메인 로직"""
    print("\n" + "="*60)
    print("🔄 Approved 종목 재평가 시작")
    print("="*60)
    print(f"실행 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # 승인된 종목 조회
    df = get_approved_stocks()

    if len(df) == 0:
        print("✅ 재평가 대상 종목이 없습니다.")
        return

    print(f"📊 총 {len(df)}개 종목 검토 중...\n")

    dropped_count = 0
    evaluated_count = 0

    for _, row in df.iterrows():
        ticker = row['ticker']
        name = row['name']
        current_score = row['final_score']
        approved_date = row['approved_date']
        days_held = int(row['days_held'])

        # 승인 당시 점수 조회
        initial_score = get_initial_score(ticker, approved_date)

        # 재평가 실행
        should_drop, drop_reasons = evaluate_stock(
            ticker, name, current_score, initial_score, days_held
        )

        # 3일 이상만 재평가 대상
        if days_held >= 3:
            evaluated_count += 1

        # 상태 표시
        status_icon = "⚠️" if days_held >= 3 else "⏳"
        print(f"{status_icon} {ticker} {name}")
        print(f"   보유 {days_held}일 | 점수: {initial_score:.1f} → {current_score:.1f}")

        if should_drop:
            # 탈락 처리
            drop_reason_str = " | ".join(drop_reasons)
            print(f"   ❌ 탈락: {drop_reason_str}")

            update_stock_status(ticker, 'rejected', drop_reason_str)
            dropped_count += 1
        else:
            if days_held >= 3:
                print(f"   ✅ 조건 유지 (계속 모니터링)")
            else:
                print(f"   ⏳ 재평가 대기 중 (3일 후 평가)")

        print()

    # 결과 요약
    print("="*60)
    print("📊 재평가 결과 요약")
    print("="*60)
    print(f"총 종목 수: {len(df)}개")
    print(f"재평가 대상 (3일 이상): {evaluated_count}개")
    print(f"탈락 처리: {dropped_count}개")
    print(f"계속 보유: {evaluated_count - dropped_count}개")
    print("="*60)

    # AI 리포트 상태 동기화 (탈락한 종목이 있을 경우)
    if dropped_count > 0:
        print("\n🔄 AI 리포트 상태 업데이트 중...")
        sync_ai_report_status()


if __name__ == "__main__":
    main()
