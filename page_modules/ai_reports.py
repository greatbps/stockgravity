#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🤖 AI Reports - AI 분석 리포트
"""
import streamlit as st
import pandas as pd
from db_config import get_db_connection
from update_ai_report_status import sync_ai_report_status


@st.cache_data(ttl=60)
def get_ai_reports(recommendation_filter=None, status_filter=None):
    """AI 리포트 조회 (종목명 및 점수 포함, final_score 순 정렬)"""
    query = """
        SELECT
            a.ticker,
            COALESCE(s.name, a.ticker) as name,
            COALESCE(s.final_score, 0) as final_score,
            COALESCE(s.status, 'unknown') as stock_status,
            COALESCE(a.status, 'ACTIVE') as report_status,
            a.report_date, a.summary, a.recommendation,
            a.confidence_score, a.momentum_analysis,
            a.liquidity_analysis, a.risk_factors,
            a.drop_reason
        FROM ai_analysis_reports a
        LEFT JOIN (
            SELECT DISTINCT ON (ticker) ticker, name, final_score, status
            FROM stock_pool
            ORDER BY ticker, added_date DESC
        ) s ON a.ticker = s.ticker
        WHERE 1=1
    """

    conditions = []
    params = []

    if recommendation_filter and recommendation_filter != "ALL":
        conditions.append("a.recommendation = %s")
        params.append(recommendation_filter)

    if status_filter and status_filter != "ALL":
        conditions.append("COALESCE(a.status, 'ACTIVE') = %s")
        params.append(status_filter)

    if conditions:
        query += " AND " + " AND ".join(conditions)

    query += " ORDER BY COALESCE(s.final_score, 0) DESC, a.report_date DESC"

    with get_db_connection() as conn:
        if params:
            df = pd.read_sql(query, conn, params=tuple(params))
        else:
            df = pd.read_sql(query, conn)
    return df


def update_status(ticker, new_status):
    """종목 상태 업데이트"""
    with get_db_connection() as conn:
        cur = conn.cursor()
        if new_status == 'approved':
            cur.execute(
                "UPDATE stock_pool SET status=%s, approved_date=NOW() WHERE ticker=%s",
                (new_status, ticker)
            )
        else:
            cur.execute(
                "UPDATE stock_pool SET status=%s WHERE ticker=%s",
                (new_status, ticker)
            )

    # AI 리포트 상태 동기화
    sync_ai_report_status()

    st.toast(f"{ticker} → {new_status}", icon="✅")


def render():
    st.title("🤖 AI Analysis Reports")
    st.caption("Google Gemini AI 기반 종목 분석 리포트")

    # 필터
    col1, col2, col3 = st.columns([1, 1, 2])

    with col1:
        recommendation = st.selectbox(
            "추천 등급",
            ["ALL", "STRONG_APPROVE", "WATCH_MORE", "DO_NOT_APPROVE"]
        )

    with col2:
        report_status = st.selectbox(
            "리포트 상태",
            ["ALL", "ACTIVE", "TRADED", "DROPPED"]
        )

    # 데이터 로드
    df = get_ai_reports(
        recommendation if recommendation != "ALL" else None,
        report_status if report_status != "ALL" else None
    )

    if len(df) == 0:
        st.info("생성된 AI 리포트가 없습니다.")
        st.markdown("""
        ### 📝 AI 리포트 생성 방법

        1. Stock Pool에서 종목 필터링
        2. 자동 업데이트 시 상위 5개 종목 AI 분석
        3. 여기서 결과 확인

        **필요 조건**:
        - Google API Key 설정 (.env 파일)
        - 필터링된 종목 존재
        """)
        return

    st.success(f"총 {len(df):,}개의 AI 리포트")

    # 리포트 카드 표시
    for idx, row in df.iterrows():
        # 추천 등급별 색상
        rec_colors = {
            'STRONG_APPROVE': '🟢',
            'WATCH_MORE': '🟡',
            'DO_NOT_APPROVE': '🔴',
            'BUY': '🟢',
            'HOLD': '🟡',
            'SELL': '🔴'
        }
        rec_icon = rec_colors.get(row['recommendation'], '⚪')

        # 리포트 상태 아이콘
        report_status_icon = {
            'ACTIVE': '🟢',
            'TRADED': '💰',
            'DROPPED': '🔴'
        }.get(row['report_status'], '⚪')

        with st.expander(
            f"{rec_icon} **{row['name']}** ({row['ticker']}) {report_status_icon} - 점수: {row['final_score']:.1f} - "
            f"{row['recommendation']} (신뢰도: {row['confidence_score']:.1f}%) - {row['report_date']}"
        ):
            col1, col2 = st.columns([2, 1])

            with col1:
                st.subheader("📊 분석 요약")
                st.write(row['summary'] if pd.notna(row['summary']) else "요약 없음")

            with col2:
                st.metric("종합 점수", f"{row['final_score']:.1f}")
                st.metric("추천", row['recommendation'])
                st.metric("신뢰도", f"{row['confidence_score']:.1f}%")

                # 리포트 상태 표시
                report_status_emoji = {
                    'ACTIVE': '🟢',
                    'TRADED': '💰',
                    'DROPPED': '🔴'
                }
                st.caption(f"리포트 상태: {report_status_emoji.get(row['report_status'], '⚪')} {row['report_status']}")

                # 종목 상태 표시
                stock_status_emoji = {
                    'monitoring': '👀',
                    'approved': '✅',
                    'rejected': '❌',
                    'trading': '💰',
                    'completed': '✔️',
                    'unknown': '❓'
                }
                st.caption(f"종목 상태: {stock_status_emoji.get(row['stock_status'], '❓')} {row['stock_status']}")

                # 탈락 사유 표시
                if row['report_status'] == 'DROPPED' and pd.notna(row['drop_reason']):
                    st.warning(f"탈락 사유: {row['drop_reason']}")

            st.divider()

            # 상세 분석
            tab1, tab2, tab3 = st.tabs(["📈 모멘텀", "💧 유동성", "⚠️ 리스크"])

            with tab1:
                st.write(row['momentum_analysis'] if pd.notna(row['momentum_analysis']) else "데이터 없음")

            with tab2:
                st.write(row['liquidity_analysis'] if pd.notna(row['liquidity_analysis']) else "데이터 없음")

            with tab3:
                st.write(row['risk_factors'] if pd.notna(row['risk_factors']) else "데이터 없음")

            # 액션 버튼
            st.divider()
            action_col1, action_col2, action_col3 = st.columns(3)

            ticker = row['ticker']
            current_status = row['stock_status']

            with action_col1:
                if current_status == 'monitoring':
                    if st.button("✅ Approve", key=f"approve_{ticker}", use_container_width=True, type="primary"):
                        update_status(ticker, "approved")
                        st.cache_data.clear()
                        st.rerun()
                elif current_status == 'approved':
                    st.success("이미 승인됨")

            with action_col2:
                if current_status in ['monitoring', 'approved']:
                    if st.button("❌ Reject", key=f"reject_{ticker}", use_container_width=True):
                        update_status(ticker, "rejected")
                        st.cache_data.clear()
                        st.rerun()
                elif current_status == 'rejected':
                    st.error("이미 거부됨")

            with action_col3:
                if current_status == 'monitoring' and st.button("🔄 Monitoring 유지", key=f"keep_{ticker}", use_container_width=True):
                    st.info("Monitoring 상태 유지")
