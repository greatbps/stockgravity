#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📦 Stock Pool - Compact Trading View
초고밀도 테이블 / 최대 정보량
"""
import streamlit as st
import pandas as pd
from db_config import get_db_connection


@st.cache_data(ttl=60)
def get_stock_pool_data():
    """Stock Pool 전체 데이터"""
    query = """
        SELECT
            ticker,
            name,
            close as price,
            change_5d as change_pct,
            trading_value / 1000000000.0 as volume_b,
            vol_ratio,
            final_score as score,
            status
        FROM stock_pool
        WHERE status IN ('monitoring', 'approved', 'rejected')
        ORDER BY final_score DESC
        LIMIT 100
    """

    with get_db_connection() as conn:
        df = pd.read_sql(query, conn)

    return df


def render():
    """Stock Pool 렌더링"""

    # ========== 헤더 (한 줄) ==========
    st.markdown("### 📦 Stock Pool | Monitoring & Filtering")

    # ========== 필터 (한 줄) ==========
    col1, col2, col3 = st.columns([4, 1, 1])

    with col1:
        search = st.text_input("🔍 Search", placeholder="Ticker or Name", label_visibility="collapsed")

    # 데이터 로드
    df = get_stock_pool_data()

    with col2:
        statuses = ["All"] + sorted(df['status'].unique().tolist())
        status = st.selectbox("Status", statuses, label_visibility="collapsed")

    with col3:
        st.markdown(f"**Total: {len(df)}**")

    # ========== 필터링 ==========
    filtered = df.copy()

    if search:
        filtered = filtered[
            filtered['ticker'].str.contains(search, case=False) |
            filtered['name'].str.contains(search, case=False)
        ]

    if status != "All":
        filtered = filtered[filtered['status'] == status]

    st.caption(f"Showing {len(filtered)} stocks")

    # ========== 고밀도 테이블 ==========
    # 컬럼 포맷팅
    display_df = filtered.copy()
    display_df['price'] = display_df['price'].apply(lambda x: f"₩{x:,.0f}")
    display_df['change_pct'] = display_df['change_pct'].apply(lambda x: f"{x:+.2f}%")
    display_df['volume_b'] = display_df['volume_b'].apply(lambda x: f"{x:.1f}B")
    display_df['vol_ratio'] = display_df['vol_ratio'].apply(lambda x: f"{x:.1f}x")

    # 컬럼 순서 및 이름
    display_df = display_df[['ticker', 'name', 'price', 'change_pct', 'volume_b', 'vol_ratio', 'score', 'status']]
    display_df.columns = ['Ticker', 'Name', 'Price', 'Chg%', 'Vol(B)', 'VolR', 'Score', 'Status']

    # 테이블 표시 (height를 크게 설정)
    st.dataframe(
        display_df,
        use_container_width=True,
        height=600,
        hide_index=True,
        column_config={
            'Ticker': st.column_config.TextColumn('Ticker', width='small'),
            'Name': st.column_config.TextColumn('Name', width='medium'),
            'Price': st.column_config.TextColumn('Price', width='small'),
            'Chg%': st.column_config.TextColumn('Chg%', width='small'),
            'Vol(B)': st.column_config.TextColumn('Vol(B)', width='small'),
            'VolR': st.column_config.TextColumn('VolR', width='small'),
            'Score': st.column_config.NumberColumn('Score', width='small'),
            'Status': st.column_config.TextColumn('Status', width='small'),
        }
    )
