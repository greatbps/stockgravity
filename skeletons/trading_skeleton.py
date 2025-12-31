#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Trading Skeleton - V0 Design
주문 폼 (Left 65%) + 계좌 정보 (Right 35%)
"""
import streamlit as st

# ============================================================================
# Data Functions (Mock - 실제 API 연결로 교체 필요)
# ============================================================================

def get_account_balance():
    """계좌 잔고 정보"""
    return {
        'available_cash': 125_430_000,
        'buying_power': 501_720_000,
        'margin_used': 35
    }

def get_market_status():
    """시장 지수"""
    return {
        'kospi': {'value': 2647.35, 'change': +0.82},
        'kosdaq': {'value': 782.14, 'change': -0.39}
    }

def get_trading_limits():
    """거래 제한"""
    return {
        'max_position_size': 50_000_000,
        'max_daily_loss': 10_000_000,
        'max_leverage': 4
    }

def get_recent_orders():
    """최근 주문 내역"""
    # Empty list for now
    return []


# ============================================================================
# Render Functions
# ============================================================================

def render_new_order_form():
    """신규 주문 폼"""
    st.subheader("📝 New Order")

    # Stock search
    st.text_input("Stock", placeholder="Search ticker or company name...")

    # Buy/Sell toggle
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🟢 Buy", key="buy_btn", use_container_width=True, type="primary"):
            st.session_state['order_type'] = 'buy'
    with col2:
        if st.button("🔴 Sell", key="sell_btn", use_container_width=True):
            st.session_state['order_type'] = 'sell'

    # Order Type
    order_type = st.selectbox("Order Type", ["Market Order", "Limit Order", "Stop Loss"])

    # Quantity
    quantity = st.number_input("Quantity", min_value=0, value=0, step=1)

    st.divider()

    # Price calculation
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Estimated Total**")
        st.markdown("**Commission**")
        st.markdown("### Total Amount")
    with col2:
        st.markdown("₩0")
        st.markdown("₩0")
        st.markdown("### **₩0**")

    st.divider()

    # Submit buttons
    col1, col2 = st.columns([3, 1])
    with col1:
        if st.button("🟢 Buy", key="submit_buy", use_container_width=True, type="primary"):
            st.success("Order submitted successfully")
    with col2:
        if st.button("Reset", key="reset", use_container_width=True):
            st.rerun()


def render_recent_orders(orders):
    """최근 주문 내역"""
    st.subheader("📋 Recent Orders")

    if len(orders) == 0:
        st.info("No recent orders. Place your first order above.", icon="💡")
    else:
        # Display orders table
        for order in orders:
            st.markdown(f"**{order['ticker']}** - {order['type']} {order['quantity']} @ ₩{order['price']:,}")


def render_account_info():
    """계좌 정보 (오른쪽 패널)"""
    # Account Balance
    st.subheader("💰 Account Balance")

    balance = get_account_balance()

    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown("**Available Cash**")
    with col2:
        st.markdown(f"₩{balance['available_cash']:,}")

    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown("**Buying Power**")
    with col2:
        st.markdown(f"**:green[₩{balance['buying_power']:,}]**")

    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown("**Margin Used**")
    with col2:
        st.markdown(f"{balance['margin_used']}%")

    st.divider()

    # Market Status
    st.subheader("📊 Market Status")

    market = get_market_status()

    st.metric(
        "● KOSPI",
        f"{market['kospi']['value']:,.2f}",
        f"{market['kospi']['change']:+.2f}%",
        delta_color="normal"
    )

    st.metric(
        "● KOSDAQ",
        f"{market['kosdaq']['value']:,.2f}",
        f"{market['kosdaq']['change']:+.2f}%",
        delta_color="normal"
    )

    st.divider()

    # Trading Limits
    st.subheader("⚙️ Trading Limits")

    limits = get_trading_limits()

    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown("**Max Position Size**")
    with col2:
        st.markdown(f"₩{limits['max_position_size'] // 1_000_000}M")

    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown("**Max Daily Loss**")
    with col2:
        st.markdown(f"₩{limits['max_daily_loss'] // 1_000_000}M")

    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown("**Max Leverage**")
    with col2:
        st.markdown(f"{limits['max_leverage']}x")


# ============================================================================
# Main Render
# ============================================================================

def render():
    """메인 Trading 렌더링"""

    # Page Header
    st.title("💰 Trading")
    st.caption("Execute trades and manage orders")

    st.divider()

    # 2-column layout: Order Form (Left 65%) + Account Info (Right 35%)
    left_col, right_col = st.columns([2, 1])

    # ========== Left Panel: New Order + Recent Orders ==========
    with left_col:
        render_new_order_form()

        st.divider()

        orders = get_recent_orders()
        render_recent_orders(orders)

    # ========== Right Panel: Account Info ==========
    with right_col:
        render_account_info()


# ============================================================================
# 테스트 실행
# ============================================================================

if __name__ == "__main__":
    st.set_page_config(
        page_title="Trading - StockGravity",
        page_icon="💰",
        layout="wide"
    )
    render()
