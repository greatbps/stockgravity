#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
💼 Kiwoom Monitoring - 키움 트레이딩 모니터링 대시보드
키움에 전송된 종목 추적 및 매매 결과 확인
"""
import streamlit as st
import pandas as pd
from db_config import get_db_connection
from datetime import datetime, timedelta


@st.cache_data(ttl=30)
def get_kiwoom_stats():
    """키움 워치리스트 통계"""
    with get_db_connection() as conn:
        cur = conn.cursor()

        # 상태별 종목 수
        cur.execute("""
            SELECT status, COUNT(*) as count
            FROM kiwoom_watchlist
            GROUP BY status
        """)
        stats = dict(cur.fetchall())

        # 오늘 추가된 종목 수
        cur.execute("""
            SELECT COUNT(*)
            FROM kiwoom_watchlist
            WHERE DATE(added_to_kiwoom_at) = CURRENT_DATE
        """)
        today_added = cur.fetchone()[0]

        # 총 수익률 (completed만)
        cur.execute("""
            SELECT
                COUNT(*) as trades,
                COALESCE(AVG(profit_rate), 0) as avg_rate,
                COALESCE(SUM(profit_loss), 0) as total_pl
            FROM kiwoom_watchlist
            WHERE status = 'completed' AND profit_rate IS NOT NULL
        """)
        row = cur.fetchone()
        total_trades = row[0]
        avg_profit_rate = row[1]
        total_profit_loss = row[2]

        # 승률 계산
        cur.execute("""
            SELECT COUNT(*)
            FROM kiwoom_watchlist
            WHERE status = 'completed' AND profit_rate > 0
        """)
        winning_trades = cur.fetchone()[0]
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0

    return {
        'monitoring': stats.get('monitoring', 0),
        'trading': stats.get('trading', 0),
        'completed': stats.get('completed', 0),
        'cancelled': stats.get('cancelled', 0),
        'today_added': today_added,
        'total_trades': total_trades,
        'avg_profit_rate': avg_profit_rate,
        'total_profit_loss': total_profit_loss,
        'win_rate': win_rate
    }


@st.cache_data(ttl=30)
def get_active_watchlist():
    """활성 워치리스트 조회 (monitoring + trading)"""
    query = """
        SELECT
            ticker,
            name,
            source,
            status,
            added_to_kiwoom_at,
            entry_condition,
            target_price,
            stop_loss,
            order_price,
            executed_price
        FROM kiwoom_watchlist
        WHERE status IN ('monitoring', 'trading')
        ORDER BY added_to_kiwoom_at DESC
    """

    with get_db_connection() as conn:
        df = pd.read_sql(query, conn)

    return df


@st.cache_data(ttl=60)
def get_trading_results():
    """거래 결과 조회 (completed)"""
    query = """
        SELECT
            ticker,
            name,
            executed_at,
            executed_price,
            exit_price,
            profit_loss,
            profit_rate,
            completed_at
        FROM kiwoom_watchlist
        WHERE status = 'completed'
        ORDER BY completed_at DESC
        LIMIT 50
    """

    with get_db_connection() as conn:
        df = pd.read_sql(query, conn)

    return df


def update_watchlist_status(ticker, new_status, **kwargs):
    """워치리스트 상태 업데이트"""
    with get_db_connection() as conn:
        cur = conn.cursor()

        # 기본 업데이트
        update_fields = ['status = %s', 'updated_at = NOW()']
        params = [new_status]

        # 추가 필드 업데이트
        for key, value in kwargs.items():
            update_fields.append(f"{key} = %s")
            params.append(value)

        params.append(ticker)

        query = f"""
            UPDATE kiwoom_watchlist
            SET {', '.join(update_fields)}
            WHERE ticker = %s AND status IN ('monitoring', 'trading')
        """

        cur.execute(query, tuple(params))
        conn.commit()

        return cur.rowcount > 0


def render():
    """키움 모니터링 대시보드 렌더링"""

    # ========== 헤더 ==========
    st.markdown("### 💼 Kiwoom Monitoring | Trading Dashboard")

    # ========== KPI (한 줄) ==========
    stats = get_kiwoom_stats()

    st.markdown(f"""
**👀 모니터링 {stats['monitoring']}** | **💼 트레이딩 {stats['trading']}** |
**✅ 완료 {stats['completed']}** | **❌ 취소 {stats['cancelled']}** |
**📈 오늘 추가 {stats['today_added']}개**
""")

    # ========== 성과 지표 (한 줄) ==========
    if stats['total_trades'] > 0:
        pl_color = "🟢" if stats['total_profit_loss'] > 0 else "🔴"
        st.markdown(f"""
**총 거래:** {stats['total_trades']}건 | **평균 수익률:** {stats['avg_profit_rate']:.2f}% |
**총 손익:** {pl_color} ₩{stats['total_profit_loss']:,.0f} | **승률:** {stats['win_rate']:.1f}%
""")

    st.markdown("---")

    # ========== 탭 구성 ==========
    tab1, tab2 = st.tabs(["📊 Active Watchlist", "📈 Trading Results"])

    with tab1:
        # 활성 워치리스트
        df = get_active_watchlist()

        if len(df) == 0:
            st.info("현재 모니터링 중인 종목이 없습니다. Stock Pool에서 종목을 추가하세요.")
        else:
            st.caption(f"총 {len(df)}개 종목")

            # 테이블 포맷팅
            display_df = df.copy()
            display_df['added_to_kiwoom_at'] = pd.to_datetime(display_df['added_to_kiwoom_at']).dt.strftime('%m-%d %H:%M')
            display_df['target_price'] = display_df['target_price'].apply(lambda x: f"₩{x:,.0f}" if pd.notna(x) else "-")
            display_df['stop_loss'] = display_df['stop_loss'].apply(lambda x: f"₩{x:,.0f}" if pd.notna(x) else "-")
            display_df['order_price'] = display_df['order_price'].apply(lambda x: f"₩{x:,.0f}" if pd.notna(x) else "-")
            display_df['executed_price'] = display_df['executed_price'].apply(lambda x: f"₩{x:,.0f}" if pd.notna(x) else "-")

            # 상태 아이콘
            status_icons = {
                'monitoring': '👀',
                'trading': '💼',
            }
            display_df['status'] = display_df['status'].apply(lambda x: f"{status_icons.get(x, '')} {x}")

            # 컬럼 선택
            display_df = display_df[['ticker', 'name', 'source', 'status', 'added_to_kiwoom_at',
                                     'target_price', 'stop_loss', 'order_price', 'executed_price']]
            display_df.columns = ['Ticker', 'Name', 'Source', 'Status', 'Added',
                                 'Target', 'Stop Loss', 'Order', 'Executed']

            # 테이블 표시
            st.dataframe(
                display_df,
                use_container_width=True,
                height=500,
                hide_index=True,
                column_config={
                    'Ticker': st.column_config.TextColumn('Ticker', width='small'),
                    'Name': st.column_config.TextColumn('Name', width='medium'),
                    'Source': st.column_config.TextColumn('Source', width='small'),
                    'Status': st.column_config.TextColumn('Status', width='small'),
                    'Added': st.column_config.TextColumn('Added', width='small'),
                    'Target': st.column_config.TextColumn('Target', width='small'),
                    'Stop Loss': st.column_config.TextColumn('Stop Loss', width='small'),
                    'Order': st.column_config.TextColumn('Order', width='small'),
                    'Executed': st.column_config.TextColumn('Executed', width='small'),
                }
            )

    with tab2:
        # 거래 결과
        df = get_trading_results()

        if len(df) == 0:
            st.info("아직 완료된 거래가 없습니다.")
        else:
            st.caption(f"최근 {len(df)}건의 거래")

            # 테이블 포맷팅
            display_df = df.copy()
            display_df['executed_at'] = pd.to_datetime(display_df['executed_at']).dt.strftime('%m-%d %H:%M')
            display_df['completed_at'] = pd.to_datetime(display_df['completed_at']).dt.strftime('%m-%d %H:%M')
            display_df['executed_price'] = display_df['executed_price'].apply(lambda x: f"₩{x:,.0f}" if pd.notna(x) else "-")
            display_df['exit_price'] = display_df['exit_price'].apply(lambda x: f"₩{x:,.0f}" if pd.notna(x) else "-")
            display_df['profit_loss'] = display_df['profit_loss'].apply(
                lambda x: f"₩{x:,.0f}" if pd.notna(x) else "-"
            )
            display_df['profit_rate'] = display_df['profit_rate'].apply(
                lambda x: f"{x:+.2f}%" if pd.notna(x) else "-"
            )

            # 컬럼 선택
            display_df = display_df[['ticker', 'name', 'executed_at', 'executed_price',
                                     'exit_price', 'profit_loss', 'profit_rate', 'completed_at']]
            display_df.columns = ['Ticker', 'Name', 'Entry Time', 'Entry',
                                 'Exit', 'P/L', 'P/L %', 'Exit Time']

            # 테이블 표시
            st.dataframe(
                display_df,
                use_container_width=True,
                height=500,
                hide_index=True,
                column_config={
                    'Ticker': st.column_config.TextColumn('Ticker', width='small'),
                    'Name': st.column_config.TextColumn('Name', width='medium'),
                    'Entry Time': st.column_config.TextColumn('Entry Time', width='small'),
                    'Entry': st.column_config.TextColumn('Entry', width='small'),
                    'Exit': st.column_config.TextColumn('Exit', width='small'),
                    'P/L': st.column_config.TextColumn('P/L', width='small'),
                    'P/L %': st.column_config.TextColumn('P/L %', width='small'),
                    'Exit Time': st.column_config.TextColumn('Exit Time', width='small'),
                }
            )
