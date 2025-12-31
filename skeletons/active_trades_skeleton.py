#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Active Trades Skeleton - V0 Design
KPI Cards (4개) + 고밀도 포지션 테이블
"""
import streamlit as st
import pandas as pd
import numpy as np

# ============================================================================
# Data Functions (Mock - 실제 DB/API 연결로 교체 필요)
# ============================================================================

def get_portfolio_summary():
    """포트폴리오 요약 (KPI)"""
    return {
        'total_pnl': 816_000,
        'total_pnl_pct': 1.03,
        'average_pnl_pct': 1.03,
        'total_value': 87_300_000,
        'positions': 8
    }


def get_active_positions():
    """활성 포지션 리스트"""
    positions = [
        {
            'ticker': 'STK023',
            'company': 'Samsung Electronics',
            'entry_price': 68_500,
            'current_price': 71_200,
            'quantity': 150,
            'position_value': 10_680_000,
            'pnl': 405_000,
            'pnl_pct': 3.94,
            'open_date': '2025-12-28'
        },
        {
            'ticker': 'STK089',
            'company': 'SK Hynix',
            'entry_price': 142_000,
            'current_price': 138_500,
            'quantity': 80,
            'position_value': 11_080_000,
            'pnl': -280_000,
            'pnl_pct': -2.46,
            'open_date': '2025-12-27'
        },
        {
            'ticker': 'STK156',
            'company': 'Hyundai Motor',
            'entry_price': 187_000,
            'current_price': 194_300,
            'quantity': 50,
            'position_value': 9_715_000,
            'pnl': 365_000,
            'pnl_pct': 3.90,
            'open_date': '2025-12-29'
        },
        {
            'ticker': 'STK234',
            'company': 'POSCO Holdings',
            'entry_price': 365_000,
            'current_price': 372_400,
            'quantity': 30,
            'position_value': 11_172_000,
            'pnl': 222_000,
            'pnl_pct': 2.03,
            'open_date': '2025-12-26'
        },
        {
            'ticker': 'STK345',
            'company': 'LG Energy Solution',
            'entry_price': 425_000,
            'current_price': 418_200,
            'quantity': 25,
            'position_value': 10_455_000,
            'pnl': -170_000,
            'pnl_pct': -1.60,
            'open_date': '2025-12-30'
        },
        {
            'ticker': 'STK412',
            'company': 'Naver Corp',
            'entry_price': 198_000,
            'current_price': 205_600,
            'quantity': 60,
            'position_value': 12_336_000,
            'pnl': 456_000,
            'pnl_pct': 3.84,
            'open_date': '2025-12-28'
        },
        {
            'ticker': 'STK478',
            'company': 'Kakao Corp',
            'entry_price': 56_700,
            'current_price': 54_200,
            'quantity': 200,
            'position_value': 10_840_000,
            'pnl': -500_000,
            'pnl_pct': -4.41,
            'open_date': '2025-12-29'
        },
        {
            'ticker': 'STK501',
            'company': 'Samsung Biologics',
            'entry_price': 892_000,
            'current_price': 918_500,
            'quantity': 12,
            'position_value': 11_022_000,
            'pnl': 318_000,
            'pnl_pct': 2.97,
            'open_date': '2025-12-27'
        },
    ]

    return pd.DataFrame(positions)


# ============================================================================
# Render Functions
# ============================================================================

def render_kpi_cards(summary):
    """포트폴리오 KPI 카드 4개"""
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        pnl_color = 'normal' if summary['total_pnl'] >= 0 else 'inverse'
        st.metric(
            label="💰 Total P&L",
            value=f"₩{abs(summary['total_pnl']):,}",
            delta=f"{summary['total_pnl_pct']:+.2f}%",
            delta_color=pnl_color
        )

    with col2:
        st.metric(
            label="📊 Average P&L",
            value=f"{summary['average_pnl_pct']:+.2f}%",
            help="Average P&L percentage across all positions"
        )

    with col3:
        st.metric(
            label="💼 Total Value",
            value=f"₩{summary['total_value']:,}",
            help="Total market value of all positions"
        )

    with col4:
        st.metric(
            label="📍 Positions",
            value=f"{summary['positions']}",
            help="Number of active positions"
        )


def render_positions_table(df):
    """활성 포지션 테이블"""
    st.subheader("📊 Active Positions")

    # Format DataFrame for display
    display_df = df.copy()

    display_df['Entry Price'] = display_df['entry_price'].apply(lambda x: f"₩{x:,}")
    display_df['Current Price'] = display_df['current_price'].apply(lambda x: f"₩{x:,}")
    display_df['Position Value'] = display_df['position_value'].apply(lambda x: f"₩{x:,}")

    # P&L with color
    def format_pnl(row):
        pnl = row['pnl']
        pnl_pct = row['pnl_pct']
        if pnl >= 0:
            return f"+₩{pnl:,} (+{pnl_pct:.2f}%)"
        else:
            return f"-₩{abs(pnl):,} ({pnl_pct:.2f}%)"

    display_df['P&L'] = df.apply(format_pnl, axis=1)

    # Select columns for display
    display_cols = [
        'ticker', 'company', 'Entry Price', 'Current Price',
        'quantity', 'Position Value', 'P&L', 'open_date'
    ]

    # Rename for display
    column_mapping = {
        'ticker': 'Ticker',
        'company': 'Company',
        'quantity': 'Qty',
        'open_date': 'Open Date'
    }

    display_df = display_df[display_cols].rename(columns=column_mapping)

    # Display table
    st.dataframe(
        display_df,
        use_container_width=True,
        height=500,
        hide_index=True,
        column_config={
            'Ticker': st.column_config.TextColumn('Ticker', width='small'),
            'Company': st.column_config.TextColumn('Company', width='medium'),
            'Entry Price': st.column_config.TextColumn('Entry Price', width='small'),
            'Current Price': st.column_config.TextColumn('Current Price', width='small'),
            'Qty': st.column_config.NumberColumn('Qty', width='small'),
            'Position Value': st.column_config.TextColumn('Position Value', width='medium'),
            'P&L': st.column_config.TextColumn('P&L', width='medium'),
            'Open Date': st.column_config.TextColumn('Open Date', width='small'),
        }
    )

    # Action buttons (시뮬레이션)
    st.caption("💡 Click on a row to add more or close the position")


# ============================================================================
# Main Render
# ============================================================================

def render():
    """메인 Active Trades 렌더링"""

    # Page Header
    st.title("📈 Active Trades")
    st.caption("Monitoring 8 open positions")

    st.divider()

    # 1. Portfolio Summary (KPI Cards)
    summary = get_portfolio_summary()
    render_kpi_cards(summary)

    st.divider()

    # 2. Active Positions Table
    df = get_active_positions()
    render_positions_table(df)

    # 3. Quick Actions
    st.divider()
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("➕ New Position", key="new_position", use_container_width=True, type="primary"):
            st.info("Navigate to Trading page to open new position")

    with col2:
        if st.button("🔄 Refresh Prices", key="refresh", use_container_width=True):
            st.success("Prices refreshed")

    with col3:
        if st.button("📊 Export to CSV", key="export", use_container_width=True):
            st.info("Exporting positions to CSV")


# ============================================================================
# 테스트 실행
# ============================================================================

if __name__ == "__main__":
    st.set_page_config(
        page_title="Active Trades - StockGravity",
        page_icon="📈",
        layout="wide"
    )
    render()
