#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🤖 AI Reports - Compact Trading View
Master-Detail 압축 / 핵심 정보만
"""
import streamlit as st
import pandas as pd
from db_config import get_db_connection
from update_ai_report_status import sync_ai_report_status


@st.cache_data(ttl=60)
def get_ai_reports():
    """AI 리포트 조회"""
    query = """
        SELECT
            a.ticker,
            COALESCE(s.name, a.ticker) as name,
            COALESCE(s.final_score, 0) as score,
            COALESCE(s.status, 'unknown') as stock_status,
            a.recommendation,
            a.confidence_score,
            a.summary,
            a.momentum_analysis,
            a.risk_factors,
            COALESCE(s.change_5d, 0) as price_change
        FROM ai_analysis_reports a
        LEFT JOIN (
            SELECT DISTINCT ON (ticker) ticker, name, final_score, status, change_5d
            FROM stock_pool
            ORDER BY ticker, added_date DESC
        ) s ON a.ticker = s.ticker
        ORDER BY COALESCE(s.final_score, 0) DESC
        LIMIT 20
    """

    with get_db_connection() as conn:
        df = pd.read_sql(query, conn)
    return df


def update_status(ticker, new_status):
    """상태 업데이트"""
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

    sync_ai_report_status()
    st.success(f"{ticker} → {new_status}")


def render():
    """AI Reports 렌더링"""

    # ========== 헤더 ==========
    st.markdown("### 🤖 AI Reports | Top 20 Analyzed")

    # 데이터 로드
    df = get_ai_reports()

    if len(df) == 0:
        st.info("No AI reports. Run: `python3 generate_ai_report.py --top 20`")
        return

    # Session state
    if 'selected_idx' not in st.session_state:
        st.session_state.selected_idx = 0

    # ========== Master-Detail (1:2 비율) ==========
    left, right = st.columns([1, 2])

    # --- LEFT: Master List ---
    with left:
        st.markdown("**Top 20 Stocks**")

        for idx, (_, report) in enumerate(df.iterrows()):
            is_selected = (idx == st.session_state.selected_idx)

            # 추천 배지
            rec_badge = {'STRONG_APPROVE': '🟢', 'WATCH_MORE': '🟡', 'DO_NOT_APPROVE': '🔴'}.get(report['recommendation'], '⚪')

            # 가격 변동
            chg = report['price_change']
            chg_str = f"▲{chg:.1f}%" if chg >= 0 else f"▼{abs(chg):.1f}%"

            # 리스트 아이템
            if is_selected:
                st.info(f"**#{idx+1} {rec_badge} {report['ticker']}** {report['name'][:15]}  \n{report['score']:.0f} | {chg_str}", icon="📌")
            else:
                st.markdown(f"**#{idx+1} {rec_badge} {report['ticker']}** {report['name'][:15]}  \n{report['score']:.0f} | {chg_str}")

            if st.button(f"Select", key=f"sel_{idx}", use_container_width=True):
                st.session_state.selected_idx = idx
                st.rerun()

            if idx < len(df) - 1:
                st.markdown("---")

    # --- RIGHT: Detail Panel ---
    with right:
        selected = df.iloc[st.session_state.selected_idx]

        rec_badge = {'STRONG_APPROVE': '🟢', 'WATCH_MORE': '🟡', 'DO_NOT_APPROVE': '🔴'}.get(selected['recommendation'], '⚪')

        st.markdown(f"## {rec_badge} {selected['name']}")
        st.caption(f"`{selected['ticker']}` • {selected['recommendation'].replace('_', ' ')}")

        # 핵심 지표
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("AI Score", f"{selected['score']:.0f}")
        with col2:
            st.metric("Confidence", f"{selected['confidence_score']:.0f}%")
        with col3:
            st.metric("Price Chg", f"{selected['price_change']:+.2f}%")

        st.markdown("---")

        # 탭 (Summary / Momentum / Risk만)
        tab1, tab2, tab3 = st.tabs(["Summary", "Momentum", "Risk"])

        with tab1:
            st.markdown("**Analysis Summary**")
            st.write(selected['summary'] if pd.notna(selected['summary']) else "No summary")

        with tab2:
            st.markdown("**Momentum Analysis**")
            st.write(selected['momentum_analysis'] if pd.notna(selected['momentum_analysis']) else "No analysis")

        with tab3:
            st.markdown("**Risk Factors**")
            st.write(selected['risk_factors'] if pd.notna(selected['risk_factors']) else "No risk assessment")

        st.markdown("---")

        # 액션 버튼 (한 줄)
        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("✅ Approve", key="approve", use_container_width=True, type="primary"):
                update_status(selected['ticker'], "approved")
                st.cache_data.clear()
                st.rerun()

        with col2:
            if st.button("🔄 Monitor", key="monitor", use_container_width=True):
                st.info(f"Keeping {selected['ticker']} in monitoring")

        with col3:
            if st.button("❌ Reject", key="reject", use_container_width=True):
                update_status(selected['ticker'], "rejected")
                st.cache_data.clear()
                st.rerun()
