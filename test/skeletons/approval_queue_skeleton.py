#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Approval Queue Skeleton - V0 Design
Master-Detail 구조 (Left 55% + Right 45%)
"""
import streamlit as st
import pandas as pd

# ============================================================================
# Data Functions (Mock - 실제 DB 연결로 교체 필요)
# ============================================================================

def get_pending_approvals():
    """승인 대기 종목 리스트"""
    approvals = [
        {
            'ticker': '005930',
            'name': 'Samsung Electronics',
            'score': 92,
            'price': 68_500,
            'change': +3.2,
            'date': '2025-01-15'
        },
        {
            'ticker': '035420',
            'name': 'NAVER',
            'score': 89,
            'price': 185_000,
            'change': +2.8,
            'date': '2025-01-15'
        },
        {
            'ticker': '035720',
            'name': 'Kakao',
            'score': 86,
            'price': 45_200,
            'change': +4.1,
            'date': '2025-01-14'
        },
    ]
    return pd.DataFrame(approvals)


def get_quick_analysis(ticker):
    """선택 종목의 빠른 분석"""
    return {
        'ticker': ticker,
        'name': 'Samsung Electronics',
        'current_price': 68_500,
        'ai_score': 92,
        'price_change': +3.2,
        'rsi': 68.5,
        'rsi_signal': 'Bullish',
        'macd_signal': 'Bullish',
        'volume_trend': 'High',
        'risk_level': 'Moderate',
        'risk_description': 'Moderate volatility. Suggested position: 2-3% of portfolio'
    }


# ============================================================================
# Render Functions
# ============================================================================

def render_approval_list_item(approval, is_selected=False):
    """승인 대기 리스트 아이템"""
    with st.container():
        # Ticker + Score + Name
        col1, col2 = st.columns([1, 3])

        with col1:
            st.markdown(f"**`{approval['ticker']}`**")
            st.caption(f"Score: {approval['score']}")

        with col2:
            st.markdown(f"**{approval['name']}**")

            # Price + Change
            change_color = 'green' if approval['change'] >= 0 else 'red'
            st.markdown(
                f"₩{approval['price']:,} "
                f"**:{change_color}[{approval['change']:+.2f}%]**  •  {approval['date']}"
            )

        if is_selected:
            st.info("📌 Selected", icon="📌")


def render_quick_analysis_panel(analysis):
    """빠른 분석 패널 (오른쪽)"""
    st.subheader("⚡ Quick Analysis")

    # Header
    st.markdown(f"## {analysis['ticker']}")
    st.markdown(f"**{analysis['name']}**")

    st.divider()

    # Price info (3-column)
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Current Price", f"₩{analysis['current_price']:,}")

    with col2:
        st.metric("AI Score", f"{analysis['ai_score']}")

    with col3:
        st.metric("Price Change", f"{analysis['price_change']:+.2f}%")

    st.divider()

    # Technical Indicators
    st.markdown("### 📊 Technical Indicators")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("RSI", f"{analysis['rsi']}", analysis['rsi_signal'])

    with col2:
        st.metric("MACD", analysis['macd_signal'])

    with col3:
        st.metric("Volume", analysis['volume_trend'])

    st.divider()

    # Risk Assessment
    st.markdown("### ⚠️ Risk Assessment")
    st.warning(
        f"**Risk Level: {analysis['risk_level']}**\n\n"
        f"{analysis['risk_description']}"
    )

    st.divider()

    # Action Buttons (3개)
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("✅ Start Trading", key="start_trading", use_container_width=True, type="primary"):
            st.success(f"Started trading {analysis['ticker']}")

    with col2:
        if st.button("🔄 Re-evaluate", key="reevaluate", use_container_width=True):
            st.info(f"Re-evaluating {analysis['ticker']}")

    with col3:
        if st.button("❌ Remove from Queue", key="remove", use_container_width=True):
            st.error(f"Removed {analysis['ticker']} from queue")


# ============================================================================
# Main Render
# ============================================================================

def render():
    """메인 Approval Queue 렌더링"""

    # Page Header
    st.title("✅ Approval Queue")
    st.caption("Review and approve stocks for trading")

    st.divider()

    # Load data
    df = get_pending_approvals()

    if len(df) == 0:
        st.info("No stocks in approval queue.")
        return

    # Session state for selected approval
    if 'selected_approval_idx' not in st.session_state:
        st.session_state.selected_approval_idx = 0

    # Master-Detail Layout (Left 55% + Right 45%)
    left_col, right_col = st.columns([1.2, 1])

    # ========== Left Panel: Pending Approvals ==========
    with left_col:
        st.markdown(f"### Pending Approvals ({len(df)})")

        for idx, (_, approval) in enumerate(df.iterrows()):
            is_selected = (idx == st.session_state.selected_approval_idx)

            render_approval_list_item(approval, is_selected)

            # Selection button
            if st.button(f"Select {approval['ticker']}", key=f"select_{idx}", use_container_width=True):
                st.session_state.selected_approval_idx = idx
                st.rerun()

            st.divider()

    # ========== Right Panel: Quick Analysis ==========
    with right_col:
        selected_approval = df.iloc[st.session_state.selected_approval_idx]
        analysis = get_quick_analysis(selected_approval['ticker'])
        render_quick_analysis_panel(analysis)


# ============================================================================
# 테스트 실행
# ============================================================================

if __name__ == "__main__":
    st.set_page_config(
        page_title="Approval Queue - StockGravity",
        page_icon="✅",
        layout="wide"
    )
    render()
