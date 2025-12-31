#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Stock Pool Skeleton - V0 Design
고밀도 데이터 테이블 (정보 밀도 우선)
"""
import streamlit as st
import pandas as pd
import numpy as np

# ============================================================================
# Data Functions (Mock - 실제 DB 연결로 교체 필요)
# ============================================================================

def get_stock_pool_data():
    """Stock Pool 전체 데이터 조회"""
    # Mock data - 실제로는 DB에서 조회
    np.random.seed(42)

    tickers = [f"STK{str(i).zfill(3)}" for i in range(1, 101)]
    companies = [f"Company {i}" for i in range(1, 101)]
    sectors = np.random.choice(['Healthcare', 'Technology', 'Energy', 'Consumer', 'Finance'], 100)
    prices = np.random.randint(10000, 200000, 100)
    changes = np.random.uniform(-5, 5, 100)
    volumes = np.random.uniform(1, 10, 100)
    ai_scores = np.random.randint(30, 100, 100)
    statuses = np.random.choice(['analyzing', 'rejected', 'watching', 'qualified'], 100)

    df = pd.DataFrame({
        'Ticker': tickers,
        'Company Name': companies,
        'Sector': sectors,
        'Price (KRW)': prices,
        'Change %': changes,
        'Volume (M)': volumes,
        'AI Score': ai_scores,
        'Status': statuses
    })

    return df


def filter_stock_pool(df, search_query, sector_filter, status_filter):
    """검색 및 필터링"""
    filtered = df.copy()

    # 검색어 필터링 (Ticker 또는 Company Name)
    if search_query:
        filtered = filtered[
            filtered['Ticker'].str.contains(search_query, case=False) |
            filtered['Company Name'].str.contains(search_query, case=False)
        ]

    # Sector 필터링
    if sector_filter != "All Sectors":
        filtered = filtered[filtered['Sector'] == sector_filter]

    # Status 필터링
    if status_filter != "All Status":
        filtered = filtered[filtered['Status'] == status_filter]

    return filtered


def style_dataframe(df):
    """데이터프레임 스타일링"""
    def color_change(val):
        """Change % 컬럼 색상"""
        if val > 0:
            return 'color: #65A150'  # Green
        elif val < 0:
            return 'color: #C75545'  # Red
        return ''

    def color_status(val):
        """Status 배지 색상"""
        colors = {
            'analyzing': 'background-color: #4D8FC7; color: white; padding: 2px 8px; border-radius: 4px',
            'rejected': 'background-color: #C75545; color: white; padding: 2px 8px; border-radius: 4px',
            'watching': 'background-color: #C5A940; color: white; padding: 2px 8px; border-radius: 4px',
            'qualified': 'background-color: #65A150; color: white; padding: 2px 8px; border-radius: 4px'
        }
        return colors.get(val, '')

    # Apply styling
    styled = df.style.applymap(color_change, subset=['Change %'])
    styled = styled.applymap(color_status, subset=['Status'])

    return styled


# ============================================================================
# Render Functions
# ============================================================================

def render():
    """메인 Stock Pool 렌더링"""

    # Page Header
    st.title("📦 Stock Pool")
    st.caption("Monitoring 500 of 500 stocks")

    st.divider()

    # Load data
    df = get_stock_pool_data()

    # ========== Search & Filters ==========
    col1, col2, col3 = st.columns([3, 1, 1])

    with col1:
        search_query = st.text_input(
            "Search by ticker or company name",
            placeholder="Search...",
            label_visibility="collapsed"
        )

    with col2:
        sectors = ["All Sectors"] + sorted(df['Sector'].unique().tolist())
        sector_filter = st.selectbox("Sector", sectors, label_visibility="collapsed")

    with col3:
        statuses = ["All Status"] + sorted(df['Status'].unique().tolist())
        status_filter = st.selectbox("Status", statuses, label_visibility="collapsed")

    # Apply filters
    filtered_df = filter_stock_pool(df, search_query, sector_filter, status_filter)

    st.caption(f"Showing {len(filtered_df):,} of {len(df):,} stocks")

    # ========== Data Table ==========
    # Format numeric columns
    display_df = filtered_df.copy()
    display_df['Price (KRW)'] = display_df['Price (KRW)'].apply(lambda x: f"₩{x:,}")
    display_df['Change %'] = display_df['Change %'].apply(lambda x: f"{x:+.2f}%")
    display_df['Volume (M)'] = display_df['Volume (M)'].apply(lambda x: f"{x:.1f}M")

    # Display with Streamlit dataframe (sortable)
    st.dataframe(
        display_df,
        use_container_width=True,
        height=600,
        hide_index=True,
        column_config={
            'Ticker': st.column_config.TextColumn('Ticker', width='small'),
            'Company Name': st.column_config.TextColumn('Company Name', width='medium'),
            'Sector': st.column_config.TextColumn('Sector', width='small'),
            'Price (KRW)': st.column_config.TextColumn('Price', width='small'),
            'Change %': st.column_config.TextColumn('Change %', width='small'),
            'Volume (M)': st.column_config.TextColumn('Volume', width='small'),
            'AI Score': st.column_config.NumberColumn('AI Score', width='small'),
            'Status': st.column_config.TextColumn('Status', width='small'),
        }
    )

    # ========== Advanced Filters Button ==========
    with st.sidebar:
        st.divider()
        st.markdown("### 🔍 Advanced Filters")

        # AI Score range
        score_range = st.slider("AI Score Range", 0, 100, (40, 100))

        # Price range
        min_price = int(df['Price (KRW)'].min())
        max_price = int(df['Price (KRW)'].max())
        price_range = st.slider("Price Range (KRW)", min_price, max_price, (min_price, max_price))

        if st.button("Apply Advanced Filters", use_container_width=True):
            st.info("Advanced filters applied")


# ============================================================================
# 테스트 실행
# ============================================================================

if __name__ == "__main__":
    st.set_page_config(
        page_title="Stock Pool - StockGravity",
        page_icon="📦",
        layout="wide"
    )
    render()
