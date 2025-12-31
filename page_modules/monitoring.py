#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📈 Monitoring History - 모니터링 히스토리
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from db_config import get_db_connection


@st.cache_data(ttl=60)
def get_tickers():
    """승인된 종목 목록 조회"""
    query = """
        SELECT DISTINCT ticker, name
        FROM stock_pool
        WHERE status = 'approved'
        ORDER BY ticker
    """
    with get_db_connection() as conn:
        df = pd.read_sql(query, conn)
    return df


@st.cache_data(ttl=60)
def get_monitoring_history(ticker):
    """모니터링 히스토리 조회"""
    query = """
    SELECT
        date, open, high, low, close, volume,
        price_change, volume_change, ma5, ma20, rsi
    FROM stock_monitoring_history
    WHERE ticker = %s
    ORDER BY date DESC
    LIMIT 100
    """
    with get_db_connection() as conn:
        df = pd.read_sql(query, conn, params=(ticker,))
    return df


def render():
    st.title("📈 Monitoring History")
    st.caption("종목별 일별 모니터링 데이터 및 차트")

    # 종목 선택
    tickers_df = get_tickers()

    if len(tickers_df) == 0:
        st.warning("승인된 종목이 없습니다.")
        st.info("💡 Stock Pool 페이지에서 종목을 먼저 승인(Approve)해주세요.")
        return

    ticker_options = [f"{row['ticker']} | {row['name']}" for _, row in tickers_df.iterrows()]

    selected = st.selectbox("🔍 종목 선택", ticker_options)
    ticker = selected.split("|")[0].strip()

    # 데이터 로드
    df = get_monitoring_history(ticker)

    if len(df) == 0:
        st.info("해당 종목의 모니터링 히스토리가 없습니다.")
        return

    # 차트 표시
    st.subheader("📊 Price Chart")

    fig = go.Figure()

    # 캔들스틱
    fig.add_trace(go.Candlestick(
        x=df['date'],
        open=df['open'],
        high=df['high'],
        low=df['low'],
        close=df['close'],
        name='OHLC'
    ))

    # 이동평균선
    if 'ma5' in df.columns and df['ma5'].notna().any():
        fig.add_trace(go.Scatter(
            x=df['date'],
            y=df['ma5'],
            name='MA5',
            line=dict(color='orange', width=1)
        ))

    if 'ma20' in df.columns and df['ma20'].notna().any():
        fig.add_trace(go.Scatter(
            x=df['date'],
            y=df['ma20'],
            name='MA20',
            line=dict(color='green', width=1)
        ))

    fig.update_layout(
        xaxis_rangeslider_visible=False,
        height=400
    )

    st.plotly_chart(fig, use_container_width=True)

    # 거래량 차트
    st.subheader("📊 Volume Chart")

    fig2 = go.Figure()
    fig2.add_trace(go.Bar(
        x=df['date'],
        y=df['volume'],
        name='Volume',
        marker_color='lightblue'
    ))

    fig2.update_layout(height=200)
    st.plotly_chart(fig2, use_container_width=True)

    # RSI 차트
    if 'rsi' in df.columns and df['rsi'].notna().any():
        st.subheader("📊 RSI")

        fig3 = go.Figure()
        fig3.add_trace(go.Scatter(
            x=df['date'],
            y=df['rsi'],
            name='RSI',
            line=dict(color='purple')
        ))

        fig3.add_hline(y=70, line_dash="dash", line_color="red", annotation_text="과매수")
        fig3.add_hline(y=30, line_dash="dash", line_color="green", annotation_text="과매도")

        fig3.update_layout(height=200)
        st.plotly_chart(fig3, use_container_width=True)

    # 데이터 테이블
    st.divider()
    st.subheader("📋 Daily OHLCV Data")

    display_df = df[['date', 'open', 'high', 'low', 'close', 'volume', 'price_change']].copy()
    display_df.columns = ['날짜', '시가', '고가', '저가', '종가', '거래량', '변화율']

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        height=400
    )
