#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI Reports Skeleton - V0 Design
Master-Detail 레이아웃 (Left 30% + Right 70%)
"""
import streamlit as st
import pandas as pd

# ============================================================================
# Data Functions (Mock - 실제 DB 연결로 교체 필요)
# ============================================================================

def get_ai_reports():
    """AI 리포트 리스트 조회 (Top 20)"""
    # Mock data
    reports = []
    tickers = [
        ('005930', 'Samsung Electronics', 92, 88, 'BUY', '+3.2%'),
        ('035420', 'NAVER', 89, 85, 'BUY', '+2.8%'),
        ('000660', 'SK Hynix', 84, 78, 'HOLD', '+1.5%'),
        ('051910', 'LG Chem', 78, 72, 'MONITOR', '-0.8%'),
        ('035720', 'Kakao', 86, 81, 'BUY', '+4.1%'),
    ]

    for i, (ticker, name, score, confidence, recommendation, change) in enumerate(tickers, 1):
        reports.append({
            'rank': i,
            'ticker': ticker,
            'name': name,
            'score': score,
            'confidence': confidence,
            'recommendation': recommendation,
            'price_change': change,
            'summary': f'Strong momentum with institutional buying. Technical breakout confirmed with volume support.',
        })

    return pd.DataFrame(reports)


def get_report_detail(ticker):
    """선택된 리포트의 상세 정보"""
    # Mock data - 실제로는 DB에서 조회
    return {
        'ticker': ticker,
        'name': 'Samsung Electronics',
        'score': 92,
        'confidence': 88,
        'price': '₩68,500',
        'recommendation': 'BUY',
        'summary': 'Strong momentum with institutional buying. Technical breakout confirmed with volume support.',
        'momentum_analysis': '''
**Trend Analysis**
- 200-day MA: Bullish breakout
- 50-day MA: Strong uptrend
- Volume: +40% above average

**Indicators**
- RSI (14): 68.5 (Bullish but approaching overbought)
- MACD: Positive crossover with expanding histogram
- Stochastic: 75 (Moderate overbought)
        ''',
        'liquidity_analysis': '''
**Trading Volume**
- Average Daily Volume: 12.5M shares
- Average Trading Value: ₩850B per day
- Bid-Ask Spread: 0.03% (Very liquid)

**Market Depth**
- Institutional ownership: 65%
- Foreign ownership: 52%
        ''',
        'risk_factors': '''
**Risk Assessment: Moderate**

⚠️ Potential Risks:
- High market correlation (Beta: 1.2)
- Semiconductor sector volatility
- Global supply chain dependencies

💡 Suggested Position Sizing: 2-3% of portfolio
        ''',
        'technical_rating': 85,
        'fundamental_rating': 78,
        'key_factors': [
            'Strong institutional buying pressure (15% increase)',
            'Breakout above 200-day moving average',
            'Volume surge confirms momentum (+40%)'
        ]
    }


# ============================================================================
# Render Functions
# ============================================================================

def render_report_list_item(report, is_selected=False):
    """리스트 아이템 렌더링 (왼쪽 패널)"""

    # 추천 등급별 배지
    badge_map = {
        'BUY': '🟢',
        'HOLD': '🟡',
        'MONITOR': '🟡',
        'SELL': '🔴'
    }
    badge = badge_map.get(report['recommendation'], '⚪')

    with st.container():
        # 3-column layout: Rank | Info | Price Change
        col1, col2, col3 = st.columns([0.5, 3, 1])

        with col1:
            st.markdown(f"**{report['rank']}**")

        with col2:
            st.markdown(f"{badge} **`{report['ticker']}`** {report['name'][:20]}")
            st.caption(f"Score: {report['score']} • Confidence: {report['confidence']}%")

        with col3:
            # 가격 변동 (색상 구분)
            if '+' in report['price_change']:
                st.markdown(f"**:green[{report['price_change']}]**")
            else:
                st.markdown(f"**:red[{report['price_change']}]**")

        # 선택 표시
        if is_selected:
            st.info("📌 Selected", icon="📌")


def render_detail_panel(detail):
    """상세 정보 패널 렌더링 (오른쪽 패널)"""

    # Header
    badge_map = {'BUY': '🟢', 'HOLD': '🟡', 'MONITOR': '🟡', 'SELL': '🔴'}
    badge = badge_map.get(detail['recommendation'], '⚪')

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown(f"# {badge} {detail['name']}")
        st.caption(f"`{detail['ticker']}` • {detail['recommendation']}")

    with col2:
        st.metric(
            "AI Score",
            f"{detail['score']}",
            f"{detail['confidence']}% confidence"
        )

    st.divider()

    # 4 Tabs: Summary / Momentum / Liquidity / Risk
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Summary", "📈 Momentum", "💧 Liquidity", "⚠️ Risk"])

    with tab1:
        st.markdown("### Analysis Summary")
        st.write(detail['summary'])

        st.divider()

        # 2-column ratings
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Technical Rating**")
            st.success("Strong")
            st.progress(detail['technical_rating'] / 100)

        with col2:
            st.markdown("**Fundamental Rating**")
            st.success("Positive")
            st.progress(detail['fundamental_rating'] / 100)

        st.markdown("#### Key Factors")
        for factor in detail['key_factors']:
            st.markdown(f"- ✓ {factor}")

    with tab2:
        st.markdown("### Momentum Analysis")
        st.markdown(detail['momentum_analysis'])

        # 3-column metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("RSI (14)", "68.5", "Bullish")
        with col2:
            st.metric("MACD", "+2.3", "Buy Signal")
        with col3:
            st.metric("Volume Trend", "+40%", "Increasing")

    with tab3:
        st.markdown("### Liquidity Analysis")
        st.markdown(detail['liquidity_analysis'])

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Avg Trading Value", "₩850B")
        with col2:
            st.metric("Avg Daily Volume", "12.5M shares")

    with tab4:
        st.markdown("### Risk Assessment")
        st.markdown(detail['risk_factors'])

        st.warning("⚠️ **Risk Level: Moderate** - Consider position sizing: 2-3% of portfolio")

    st.divider()

    # Action Buttons (3개)
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("✅ Approve for Trading", key="approve", use_container_width=True, type="primary"):
            st.success(f"Approved {detail['ticker']} for trading")

    with col2:
        if st.button("🔄 Keep Monitoring", key="monitor", use_container_width=True):
            st.info(f"Keeping {detail['ticker']} in monitoring")

    with col3:
        if st.button("❌ Reject", key="reject", use_container_width=True):
            st.error(f"Rejected {detail['ticker']}")


# ============================================================================
# Main Render
# ============================================================================

def render():
    """메인 AI Reports 렌더링"""

    # Page Header
    st.title("🤖 AI Reports")
    st.caption("Top 20 analyzed stocks")

    st.divider()

    # Load data
    df = get_ai_reports()

    if len(df) == 0:
        st.info("No AI reports available. Run analysis to generate reports.")
        return

    # Session state for selected report
    if 'selected_report_idx' not in st.session_state:
        st.session_state.selected_report_idx = 0

    # Master-Detail Layout (Left 30% + Right 70%)
    left_col, right_col = st.columns([1, 2])

    # ========== Left Panel: Master List ==========
    with left_col:
        st.markdown("### Top 20 Analyzed Stocks")

        for idx, (_, report) in enumerate(df.iterrows()):
            is_selected = (idx == st.session_state.selected_report_idx)

            render_report_list_item(report, is_selected)

            # Selection button
            if st.button(f"Select #{report['rank']}", key=f"select_{idx}", use_container_width=True):
                st.session_state.selected_report_idx = idx
                st.rerun()

            st.divider()

    # ========== Right Panel: Detail ==========
    with right_col:
        selected_report = df.iloc[st.session_state.selected_report_idx]
        detail = get_report_detail(selected_report['ticker'])
        render_detail_panel(detail)


# ============================================================================
# 테스트 실행
# ============================================================================

if __name__ == "__main__":
    st.set_page_config(
        page_title="AI Reports - StockGravity",
        page_icon="🤖",
        layout="wide"
    )
    render()
