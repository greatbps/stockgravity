#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📦 Stock Pool - Compact Trading View
초고밀도 테이블 / 최대 정보량
"""
import streamlit as st
import pandas as pd
from db_config import get_db_connection
from datetime import datetime


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


def add_to_kiwoom_watchlist(ticker, name, source='stock_pool'):
    """키움 워치리스트에 종목 추가"""
    with get_db_connection() as conn:
        cur = conn.cursor()

        # 이미 추가되어 있는지 확인
        cur.execute("""
            SELECT id FROM kiwoom_watchlist
            WHERE ticker = %s AND status IN ('monitoring', 'trading')
        """, (ticker,))

        if cur.fetchone():
            return False, "이미 키움 모니터링 중입니다"

        # 워치리스트에 추가
        cur.execute("""
            INSERT INTO kiwoom_watchlist (ticker, name, source, status)
            VALUES (%s, %s, %s, 'monitoring')
        """, (ticker, name, source))

        # stock_pool 업데이트
        cur.execute("""
            UPDATE stock_pool
            SET sent_to_kiwoom_at = NOW(), kiwoom_status = 'monitoring'
            WHERE ticker = %s
        """, (ticker,))

        conn.commit()
        return True, f"'{name}' 키움 모니터링에 추가되었습니다"


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
    # 컬럼 포맷팅 (선택용 체크박스 추가)
    display_df = filtered.copy()
    display_df.insert(0, 'Select', False)  # 체크박스 컬럼
    display_df['price'] = display_df['price'].apply(lambda x: f"₩{x:,.0f}")
    display_df['change_pct'] = display_df['change_pct'].apply(lambda x: f"{x:+.2f}%")
    display_df['volume_b'] = display_df['volume_b'].apply(lambda x: f"{x:.1f}B")
    display_df['vol_ratio'] = display_df['vol_ratio'].apply(lambda x: f"{x:.1f}x")

    # 컬럼 순서 및 이름
    display_df = display_df[['Select', 'ticker', 'name', 'price', 'change_pct', 'volume_b', 'vol_ratio', 'score', 'status']]
    display_df.columns = ['✓', 'Ticker', 'Name', 'Price', 'Chg%', 'Vol(B)', 'VolR', 'Score', 'Status']

    # 테이블 표시 (편집 가능한 체크박스)
    edited_df = st.data_editor(
        display_df,
        use_container_width=True,
        height=550,
        hide_index=True,
        column_config={
            '✓': st.column_config.CheckboxColumn('✓', width='small', default=False),
            'Ticker': st.column_config.TextColumn('Ticker', width='small', disabled=True),
            'Name': st.column_config.TextColumn('Name', width='medium', disabled=True),
            'Price': st.column_config.TextColumn('Price', width='small', disabled=True),
            'Chg%': st.column_config.TextColumn('Chg%', width='small', disabled=True),
            'Vol(B)': st.column_config.TextColumn('Vol(B)', width='small', disabled=True),
            'VolR': st.column_config.TextColumn('VolR', width='small', disabled=True),
            'Score': st.column_config.NumberColumn('Score', width='small', disabled=True),
            'Status': st.column_config.TextColumn('Status', width='small', disabled=True),
        },
        disabled=['Ticker', 'Name', 'Price', 'Chg%', 'Vol(B)', 'VolR', 'Score', 'Status']
    )

    # ========== 액션 버튼 ==========
    selected = edited_df[edited_df['✓'] == True]

    if len(selected) > 0:
        st.markdown(f"**선택된 종목: {len(selected)}개**")

        col1, col2, col3 = st.columns([1, 1, 4])

        with col1:
            if st.button("🤖 AI 분석 요청", use_container_width=True, type="secondary"):
                st.info(f"AI 분석 기능은 `generate_ai_report.py` 스크립트를 사용하세요.\n\n선택된 종목: {', '.join(selected['Ticker'].tolist())}")

        with col2:
            if st.button("👀 키움 모니터링", use_container_width=True, type="primary"):
                success_count = 0
                for idx, row in selected.iterrows():
                    # 원본 데이터에서 ticker와 name 가져오기
                    ticker = filtered.iloc[idx]['ticker']
                    name = filtered.iloc[idx]['name']
                    success, msg = add_to_kiwoom_watchlist(ticker, name)
                    if success:
                        success_count += 1

                if success_count > 0:
                    st.success(f"✅ {success_count}개 종목이 키움 모니터링에 추가되었습니다!")
                    st.rerun()
                else:
                    st.warning("선택된 종목이 이미 모니터링 중입니다.")
    else:
        st.caption("종목을 선택하려면 왼쪽 체크박스를 클릭하세요.")
