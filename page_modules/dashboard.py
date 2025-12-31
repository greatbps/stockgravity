#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📊 Dashboard - 홈 화면
"""
import streamlit as st
import pandas as pd
from db_config import get_db_connection
from datetime import datetime


@st.cache_data(ttl=30)
def get_stats():
    """전체 통계 조회"""
    query = """
    SELECT
        status,
        COUNT(*) as count
    FROM stock_pool
    GROUP BY status
    """
    with get_db_connection() as conn:
        df = pd.read_sql(query, conn)
    return df


@st.cache_data(ttl=30)
def get_top_stocks(limit=10):
    """상위 종목 조회"""
    query = """
    SELECT
        ticker, name, close, trading_value,
        change_5d, final_score, status
    FROM stock_pool
    WHERE status = 'monitoring'
    ORDER BY final_score DESC
    LIMIT %s
    """
    with get_db_connection() as conn:
        df = pd.read_sql(query, conn, params=(limit,))
    return df


def render():
    st.title("📊 StockGravity Dashboard")
    st.caption("시스템 개요 및 주요 지표")

    # 자동 업데이트 상태
    st.info("🕐 다음 자동 업데이트: 평일 15:20 | 상태: 대기 중")

    # 통계 카드
    stats_df = get_stats()

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        monitoring_count = stats_df[stats_df['status'] == 'monitoring']['count'].sum()
        st.metric("📡 Monitoring", f"{monitoring_count:,}")

    with col2:
        approved_count = stats_df[stats_df['status'] == 'approved']['count'].sum()
        st.metric("✅ Approved", f"{approved_count:,}")

    with col3:
        trading_count = stats_df[stats_df['status'] == 'trading']['count'].sum()
        st.metric("💰 Trading", f"{trading_count:,}")

    with col4:
        completed_count = stats_df[stats_df['status'] == 'completed']['count'].sum()
        st.metric("✔ Completed", f"{completed_count:,}")

    st.divider()

    # Top 10 종목
    st.subheader("📌 Top 10 Filtered Stocks")

    top_df = get_top_stocks(10)

    if len(top_df) > 0:
        # 표시용 데이터 준비
        display_df = top_df.copy()
        display_df['거래대금(억)'] = (display_df['trading_value'] / 100_000_000).round(1)
        display_df = display_df[['ticker', 'name', 'close', '거래대금(억)', 'change_5d', 'final_score']]
        display_df.columns = ['종목코드', '종목명', '종가', '거래대금(억)', '5일변화율', '점수']

        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("데이터가 없습니다. 자동 업데이트를 기다려주세요.")

    st.divider()

    # 시스템 정보
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📋 System Info")
        st.markdown("""
        - **Database**: PostgreSQL 16
        - **Auto Update**: 평일 15:20
        - **Filter Criteria**:
          - 거래대금 > 1억원
          - 종가 > 5,000원
          - 5일 변화율 > -5%
          - 거래량 비율 > 0.5x
        """)

    with col2:
        st.subheader("🔄 Recent Activity")
        st.info("최근 활동 내역은 개발 중입니다.")
