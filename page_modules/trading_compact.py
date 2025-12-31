#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
💰 Trading - Compact Trading View
주문 폼 압축 / 필수 정보만
"""
import streamlit as st


def get_account_info():
    """계좌 정보 (Mock)"""
    return {
        'cash': 125_430_000,
        'buying_power': 501_720_000,
        'margin': 35
    }


def get_market_status():
    """시장 지수 (Mock)"""
    return {
        'kospi': {'value': 2647.35, 'change': +0.82},
        'kosdaq': {'value': 782.14, 'change': -0.39}
    }


def render():
    """Trading 렌더링"""

    # ========== 헤더 ==========
    st.markdown("### 💰 Trading | Order Execution")

    # ========== 계좌 정보 (한 줄) ==========
    acct = get_account_info()
    market = get_market_status()

    st.markdown(f"""
    **Cash:** ₩{acct['cash']:,} | **Buying Power:** ₩{acct['buying_power']:,} | **Margin:** {acct['margin']}% |
    **KOSPI:** {market['kospi']['value']:,.2f} ({market['kospi']['change']:+.2f}%) |
    **KOSDAQ:** {market['kosdaq']['value']:,.2f} ({market['kosdaq']['change']:+.2f}%)
    """)

    st.markdown("---")

    # ========== 주문 폼 (2-column) ==========
    left, right = st.columns([2, 1])

    with left:
        st.markdown("**📝 New Order**")

        # Stock
        stock = st.text_input("Stock", placeholder="Ticker or Company Name")

        # Buy/Sell
        col1, col2 = st.columns(2)
        with col1:
            buy_clicked = st.button("🟢 BUY", use_container_width=True, type="primary")
        with col2:
            sell_clicked = st.button("🔴 SELL", use_container_width=True)

        # Order Type + Quantity (한 줄)
        col1, col2 = st.columns(2)
        with col1:
            order_type = st.selectbox("Order Type", ["Market Order", "Limit Order", "Stop Loss"])
        with col2:
            quantity = st.number_input("Quantity", min_value=0, value=0, step=1)

        # 예상 금액
        st.markdown("---")
        st.markdown(f"""
        **Estimated Total:** ₩0
        **Commission:** ₩0
        **Total Amount:** ₩0
        """)

        # 제출
        col1, col2 = st.columns([3, 1])
        with col1:
            if st.button("📤 Submit Order", use_container_width=True, type="primary"):
                st.success("Order submitted!")
        with col2:
            if st.button("Reset", use_container_width=True):
                st.rerun()

    with right:
        st.markdown("**⚙️ Trading Limits**")

        st.markdown(f"""
        **Max Position:** ₩50M
        **Max Daily Loss:** ₩10M
        **Max Leverage:** 4x
        """)

        st.markdown("---")

        st.markdown("**📋 Quick Stats**")
        st.markdown(f"""
        **Open Positions:** 0
        **Today's Trades:** 0
        **Today's P&L:** ₩0
        """)

    st.markdown("---")

    # ========== 최근 주문 ==========
    st.markdown("**📋 Recent Orders**")
    st.info("No recent orders. Place your first order above.")
