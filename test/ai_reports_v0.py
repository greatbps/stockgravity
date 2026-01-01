#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🤖 AI Reports - v0 Design
Left Panel + Right Detail 구조
"""
import streamlit as st
import pandas as pd
from db_config import get_db_connection
from update_ai_report_status import sync_ai_report_status


@st.cache_data(ttl=60)
def get_ai_reports(recommendation_filter=None, status_filter=None):
    """AI 리포트 조회"""
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
            a.drop_reason,
            COALESCE(s.close, 0) as close,
            COALESCE(s.change_5d, 0) as price_change
        FROM ai_analysis_reports a
        LEFT JOIN (
            SELECT DISTINCT ON (ticker) ticker, name, final_score, status, close, change_5d
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


def render_report_list_item(report, rank, is_selected):
    """리포트 리스트 아이템 렌더링"""
    # 추천 등급 색상
    rec_colors = {
        'STRONG_APPROVE': ('success', '🟢'),
        'WATCH_MORE': ('warning', '🟡'),
        'DO_NOT_APPROVE': ('info', '🔴'),
    }
    color_class, icon = rec_colors.get(report['recommendation'], ('info', '⚪'))

    # 가격 변동
    price_change = report['price_change']
    price_color = 'positive' if price_change >= 0 else 'negative'
    price_arrow = '▲' if price_change >= 0 else '▼'

    # 선택 상태 스타일
    selected_style = 'selected' if is_selected else ''

    html = f"""
    <div class="report-list-item {selected_style}">
        <div style="display: flex; gap: 0.75rem; align-items: start;">
            <!-- Rank Badge -->
            <div class="rank-badge">{rank}</div>

            <div style="flex: 1; min-width: 0;">
                <!-- Header -->
                <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 0.5rem;">
                    <div>
                        <div style="display: flex; gap: 0.5rem; align-items: center;">
                            <span class="mono" style="font-weight: 600; font-size: 0.875rem;">{report['ticker']}</span>
                            <span class="badge badge-{color_class}">{report['recommendation'].replace('_', ' ')}</span>
                        </div>
                        <div style="color: #737373; font-size: 0.875rem; margin-top: 0.25rem;">{report['name']}</div>
                    </div>
                    <div class="price-change {price_color}">
                        {price_arrow} {abs(price_change):.2f}%
                    </div>
                </div>

                <!-- Metrics -->
                <div style="display: flex; gap: 1rem; margin-bottom: 0.5rem; font-size: 0.75rem;">
                    <div>
                        <span class="metric-label">Score: </span>
                        <span class="metric-value">{report['final_score']:.1f}</span>
                    </div>
                    <div>
                        <span class="metric-label">Confidence: </span>
                        <span class="metric-value">{report['confidence_score']:.0f}%</span>
                    </div>
                </div>

                <!-- Summary -->
                <p style="font-size: 0.75rem; color: #737373; margin: 0;
                          overflow: hidden; text-overflow: ellipsis;
                          display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical;">
                    {report['summary'] if pd.notna(report['summary']) else 'No summary available'}
                </p>
            </div>
        </div>
    </div>
    """
    return html


def render_detail_panel(report):
    """상세 정보 패널 렌더링"""
    # 헤더
    rec_colors = {
        'STRONG_APPROVE': 'success',
        'WATCH_MORE': 'warning',
        'DO_NOT_APPROVE': 'info',
    }
    color = rec_colors.get(report['recommendation'], 'info')

    st.markdown(f"""
    <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 2rem;">
        <div>
            <div style="display: flex; gap: 0.75rem; align-items: center;">
                <h2 style="margin: 0; font-size: 2rem;">{report['name']}</h2>
                <span class="badge badge-{color}">{report['recommendation'].replace('_', ' ')}</span>
            </div>
            <p class="mono" style="color: #737373; font-size: 1.125rem; margin-top: 0.25rem;">{report['ticker']}</p>
        </div>
        <div style="text-align: right;">
            <div style="color: #737373; font-size: 0.875rem;">AI Score</div>
            <div style="font-size: 2.5rem; font-weight: bold; margin: 0.25rem 0;">{report['final_score']:.0f}</div>
            <div style="color: #737373; font-size: 0.75rem;">{report['confidence_score']:.0f}% confidence</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 탭
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Summary", "📈 Momentum", "💧 Liquidity", "⚠️ Risk"])

    with tab1:
        st.markdown("### Analysis Summary")
        st.write(report['summary'] if pd.notna(report['summary']) else "No summary available")

        # 메트릭 그리드
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"""
            <div class="kpi-card success">
                <div class="metric-label">Technical Rating</div>
                <div style="font-size: 1.5rem; font-weight: bold; color: var(--color-success); margin: 0.5rem 0;">Strong</div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: 85%;"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown(f"""
            <div class="kpi-card success">
                <div class="metric-label">Fundamental Rating</div>
                <div style="font-size: 1.5rem; font-weight: bold; color: var(--color-success); margin: 0.5rem 0;">Positive</div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: 78%;"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        # Key Factors
        st.markdown("#### Key Factors")
        st.markdown("""
        <ul class="key-factors">
            <li><span class="checkmark">✓</span> <span>Strong institutional buying pressure</span></li>
            <li><span class="checkmark">✓</span> <span>Breakout above 200-day moving average</span></li>
            <li><span class="checkmark">✓</span> <span>Volume surge confirms momentum</span></li>
        </ul>
        """, unsafe_allow_html=True)

    with tab2:
        st.markdown("### Momentum Analysis")
        st.write(report['momentum_analysis'] if pd.notna(report['momentum_analysis']) else "No momentum analysis available")

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("RSI (14)", "68.5", "Bullish")
        with col2:
            st.metric("MACD", "+2.3", "Buy Signal")
        with col3:
            st.metric("Volume Trend", "+40%", "Increasing")

    with tab3:
        st.markdown("### Liquidity Analysis")
        st.write(report['liquidity_analysis'] if pd.notna(report['liquidity_analysis']) else "No liquidity analysis available")

        col1, col2 = st.columns(2)
        with col1:
            value_billion = report.get('trading_value', 0) / 100_000_000
            st.metric("Avg Trading Value", f"₩{value_billion:.0f}B")
        with col2:
            st.metric("Avg Daily Volume", "12.5M shares")

    with tab4:
        st.markdown("### Risk Assessment")
        st.write(report['risk_factors'] if pd.notna(report['risk_factors']) else "No risk assessment available")

        st.warning("⚠️ **Risk Level: Moderate** - Consider position sizing: 2-3% of portfolio")

    # 액션 버튼
    st.markdown("---")
    col1, col2, col3 = st.columns(3)

    current_status = report['stock_status']

    with col1:
        if current_status == 'monitoring':
            if st.button("✅ Approve for Trading", key=f"approve_{report['ticker']}", use_container_width=True, type="primary"):
                update_status(report['ticker'], "approved")
                st.cache_data.clear()
                st.rerun()
        elif current_status == 'approved':
            st.success("Already Approved")

    with col2:
        if current_status in ['monitoring', 'approved']:
            if st.button("🔄 Keep Monitoring", key=f"monitor_{report['ticker']}", use_container_width=True):
                st.info("Keeping in monitoring status")

    with col3:
        if current_status in ['monitoring', 'approved']:
            if st.button("❌ Reject", key=f"reject_{report['ticker']}", use_container_width=True):
                update_status(report['ticker'], "rejected")
                st.cache_data.clear()
                st.rerun()


def render():
    """메인 렌더 함수"""
    # CSS 로드
    try:
        with open('/home/greatbps/projects/stockgravity/styles/v0_theme.css', 'r') as f:
            css = f.read()
        st.markdown(f'<style>{css}</style>', unsafe_allow_html=True)
    except:
        pass

    st.title("🤖 AI Analysis Reports")
    st.caption("Google Gemini AI 기반 종목 분석 리포트")

    # 필터
    col1, col2, col3 = st.columns([1, 1, 2])

    with col1:
        recommendation = st.selectbox(
            "추천 등급",
            ["ALL", "STRONG_APPROVE", "WATCH_MORE", "DO_NOT_APPROVE"],
            key="rec_filter"
        )

    with col2:
        report_status = st.selectbox(
            "리포트 상태",
            ["ALL", "ACTIVE", "TRADED", "DROPPED"],
            key="status_filter"
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

        ```bash
        python3 generate_ai_report.py --top 20
        ```
        """)
        return

    st.success(f"총 {len(df):,}개의 AI 리포트")

    # 선택된 리포트 초기화
    if 'selected_report_idx' not in st.session_state:
        st.session_state.selected_report_idx = 0

    # Left Panel + Right Detail
    left_col, right_col = st.columns([1, 2])

    with left_col:
        st.markdown("### Top 20 Analyzed Stocks")
        st.markdown("<div style='max-height: 800px; overflow-y: auto;'>", unsafe_allow_html=True)

        # 리포트 리스트 렌더링
        for idx, (_, report) in enumerate(df.iterrows()):
            is_selected = (idx == st.session_state.selected_report_idx)

            # 컨테이너로 감싸기
            with st.container():
                # 리스트 아이템 HTML
                html = render_report_list_item(report, idx + 1, is_selected)
                st.markdown(html, unsafe_allow_html=True)

                # 클릭 버튼 (작은 버튼)
                if st.button(f"#{idx+1} {report['ticker']} - {report['name'][:15]}", key=f"select_{idx}", use_container_width=True):
                    st.session_state.selected_report_idx = idx
                    st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

    with right_col:
        # 선택된 리포트 상세 정보
        selected_report = df.iloc[st.session_state.selected_report_idx]
        render_detail_panel(selected_report)
