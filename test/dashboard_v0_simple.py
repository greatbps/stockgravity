#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📊 Dashboard - v0 Design (Simplified)
Streamlit 네이티브 컴포넌트 사용
"""
import streamlit as st
import pandas as pd
from db_config import get_db_connection
from datetime import datetime


@st.cache_data(ttl=30)
def get_kpi_data():
    """KPI 데이터 조회"""
    with get_db_connection() as conn:
        cur = conn.cursor()

        # Stock Pool 상태별 카운트
        cur.execute("""
            SELECT status, COUNT(*) as count
            FROM stock_pool
            GROUP BY status
        """)
        pool_stats = dict(cur.fetchall())

        # AI Reports 카운트
        cur.execute("""
            SELECT
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE recommendation = 'STRONG_APPROVE') as strong_approve
            FROM ai_analysis_reports
            WHERE report_date >= CURRENT_DATE - INTERVAL '7 days'
        """)
        ai_stats = cur.fetchone()

        # 최근 업데이트 시간
        cur.execute("""
            SELECT MAX(added_date)
            FROM stock_pool
            WHERE status = 'monitoring'
        """)
        last_update = cur.fetchone()[0]

    return {
        'pool_size': pool_stats.get('monitoring', 0),
        'approved': pool_stats.get('approved', 0),
        'trading': pool_stats.get('trading', 0),
        'completed': pool_stats.get('completed', 0),
        'ai_total': ai_stats[0] if ai_stats else 0,
        'ai_strong': ai_stats[1] if ai_stats else 0,
        'last_update': last_update
    }


@st.cache_data(ttl=60)
def get_recent_ai_reports(limit=5):
    """최근 AI 추천 종목"""
    query = """
        SELECT
            a.ticker,
            COALESCE(s.name, a.ticker) as name,
            COALESCE(s.final_score, 0) as final_score,
            COALESCE(s.status, 'unknown') as stock_status,
            a.recommendation,
            a.confidence_score,
            a.summary
        FROM ai_analysis_reports a
        LEFT JOIN (
            SELECT DISTINCT ON (ticker) ticker, name, final_score, status
            FROM stock_pool
            ORDER BY ticker, added_date DESC
        ) s ON a.ticker = s.ticker
        WHERE a.recommendation = 'STRONG_APPROVE'
          AND a.report_date >= CURRENT_DATE - INTERVAL '7 days'
        ORDER BY COALESCE(s.final_score, 0) DESC
        LIMIT %s
    """

    with get_db_connection() as conn:
        df = pd.read_sql(query, conn, params=(limit,))
    return df


def render():
    """메인 렌더 함수"""
    st.title("📊 StockGravity Dashboard")
    st.caption("Korean Stock Filtering & AI Trading System")

    # 데이터 로드
    kpi_data = get_kpi_data()
    recent_reports = get_recent_ai_reports(5)

    # AI Engine 상태
    st.success(f"🤖 **AI Engine Active** • Gemini 2.5 Flash • Last update: {kpi_data['last_update'].strftime('%Y-%m-%d %H:%M') if kpi_data['last_update'] else 'N/A'}")

    st.divider()

    # KPI Metrics
    st.subheader("📈 Key Metrics")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="📦 Pool Size",
            value=f"{kpi_data['pool_size']:,}",
            delta=None
        )

    with col2:
        st.metric(
            label="🤖 AI Reports",
            value=f"{kpi_data['ai_total']}",
            delta=f"{kpi_data['ai_strong']} Strong Approve"
        )

    with col3:
        st.metric(
            label="✅ Approved",
            value=f"{kpi_data['approved']:,}",
            delta=None
        )

    with col4:
        st.metric(
            label="💰 Active Trades",
            value=f"{kpi_data['trading']:,}",
            delta=None
        )

    st.divider()

    # Workflow Progress (텍스트 버전)
    st.subheader("🔄 Pipeline Status")

    workflow_col1, workflow_col2, workflow_col3, workflow_col4, workflow_col5 = st.columns(5)

    with workflow_col1:
        st.markdown("**Filter**")
        st.markdown("✅ Complete")
        st.caption("2,790 stocks")

    with workflow_col2:
        st.markdown("**Pool**")
        st.markdown(f"✅ Complete")
        st.caption(f"{kpi_data['pool_size']} stocks")

    with workflow_col3:
        st.markdown("**AI Analysis**")
        st.markdown("⏳ Active")
        st.caption(f"{kpi_data['ai_total']} reports")

    with workflow_col4:
        st.markdown("**Approval**")
        st.markdown("⏸️ Pending")
        st.caption(f"{kpi_data['approved']} stocks")

    with workflow_col5:
        st.markdown("**Trading**")
        st.markdown("⏸️ Pending")
        st.caption(f"{kpi_data['trading']} active")

    st.divider()

    # 2 Columns
    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("⚡ Action Needed")

        # AI Reports 검토 필요
        if kpi_data['ai_strong'] > 0:
            st.info(f"📄 **{kpi_data['ai_strong']} AI Reports need review**\n\nTop stocks analyzed, awaiting approval decision", icon="📄")

        # 재평가 필요
        if kpi_data['approved'] >= 3:
            st.warning(f"🔄 **Stocks need re-evaluation**\n\nStocks held for 3+ days require review", icon="🔄")

        # 활성 거래
        if kpi_data['trading'] > 0:
            st.info(f"💰 **{kpi_data['trading']} Active trades to monitor**\n\nReview real-time positions and P/L", icon="💰")

        if kpi_data['ai_strong'] == 0 and kpi_data['approved'] < 3 and kpi_data['trading'] == 0:
            st.success("✅ No pending actions - all caught up!")

    with col_right:
        st.subheader("🌟 Top AI Recommendations")

        if len(recent_reports) > 0:
            for _, report in recent_reports.iterrows():
                with st.container():
                    cols = st.columns([3, 1])
                    with cols[0]:
                        st.markdown(f"**`{report['ticker']}`** {report['name']}")
                        st.caption(f"💚 STRONG_APPROVE • {report['stock_status'].upper()}")
                    with cols[1]:
                        st.metric("Score", f"{report['final_score']:.0f}")

            if st.button("→ View All AI Reports", use_container_width=True):
                st.switch_page("pages/2_🤖_AI_Reports.py")
        else:
            st.info("No AI reports available. Run analysis to generate reports.")

    st.divider()

    # Quick Actions
    st.subheader("🚀 Quick Actions")
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("📦 View Stock Pool", use_container_width=True):
            st.switch_page("pages/1_📦_Stock_Pool.py")

    with col2:
        if st.button("🤖 Review AI Reports", use_container_width=True, type="primary"):
            st.switch_page("pages/2_🤖_AI_Reports.py")

    with col3:
        if st.button("✅ Manage Trading", use_container_width=True):
            st.switch_page("pages/3_✅_Trading.py")
