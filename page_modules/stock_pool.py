#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📦 Stock Pool - 필터링된 종목 관리
"""
import streamlit as st
import pandas as pd
from datetime import date, timedelta
from db_config import get_db_connection
from approval_badge import get_approval_badge

PAGE_SIZE = 30


# =========================
# DB QUERY
# =========================
@st.cache_data(ttl=10)
def load_stock_pool(status, score_min, score_max, value_min, value_max, start_date, end_date):
    """Stock Pool 데이터 로드"""
    query = """
        SELECT
            ticker,
            name,
            close,
            trading_value,
            change_5d,
            vol_ratio,
            final_score,
            status,
            realtime_price,
            realtime_volume,
            realtime_updated_at,
            notes,
            added_date
        FROM stock_pool
        WHERE status = %s
          AND final_score BETWEEN %s AND %s
          AND trading_value BETWEEN %s AND %s
          AND added_date::date BETWEEN %s AND %s
        ORDER BY final_score DESC
    """

    with get_db_connection() as conn:
        df = pd.read_sql(
            query,
            conn,
            params=(
                status,
                score_min,
                score_max,
                value_min,
                value_max,
                start_date,
                end_date
            )
        )
    return df


@st.cache_data(ttl=60)
def load_rsi_batch(tickers):
    """여러 종목의 최근 RSI 값 조회"""
    if not tickers:
        return {}

    query = """
    SELECT DISTINCT ON (ticker) ticker, rsi
    FROM stock_monitoring_history
    WHERE ticker = ANY(%s) AND rsi IS NOT NULL
    ORDER BY ticker, date DESC
    """

    with get_db_connection() as conn:
        result = pd.read_sql(query, conn, params=(list(tickers),))

    return dict(zip(result['ticker'], result['rsi']))


@st.cache_data(ttl=300)
def load_ai_reports_batch(tickers):
    """여러 종목의 AI 리포트 조회"""
    if not tickers:
        return {}

    query = """
    SELECT DISTINCT ON (ticker) ticker, recommendation, confidence_score
    FROM ai_analysis_reports
    WHERE ticker = ANY(%s)
    ORDER BY ticker, report_date DESC
    """

    with get_db_connection() as conn:
        result = pd.read_sql(query, conn, params=(list(tickers),))

    return {row['ticker']: row for _, row in result.iterrows()}


# =========================
# ACTION HANDLERS
# =========================
def update_status(ticker, new_status):
    """종목 상태 업데이트"""
    with get_db_connection() as conn:
        cur = conn.cursor()
        if new_status == 'approved':
            cur.execute(
                "UPDATE stock_pool SET status=%s, approved_date=NOW() WHERE ticker=%s",
                (new_status, ticker)
            )
        else:
            cur.execute(
                "UPDATE stock_pool SET status=%s WHERE ticker=%s",
                (new_status, ticker)
            )
    st.toast(f"{ticker} → {new_status}", icon="✅")


def update_memo(ticker, memo):
    """종목 메모 업데이트"""
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "UPDATE stock_pool SET notes=%s WHERE ticker=%s",
            (memo, ticker)
        )
    st.toast(f"{ticker} 메모 저장", icon="📝")


# =========================
# MAIN RENDER
# =========================
def render():
    st.title("📦 Stock Pool")
    st.caption("필터링된 종목을 검토하고 승인/관리합니다")

    # -------------------------
    # SIDEBAR FILTERS
    # -------------------------
    with st.sidebar:
        st.subheader("🔍 Filters")

        status = st.selectbox(
            "Status",
            ["monitoring", "approved", "rejected", "trading", "completed"],
            index=0
        )

        score = st.slider("Final Score", 0.0, 100.0, (0.0, 100.0))

        value = st.slider(
            "Trading Value (억원)",
            1.0, 5000.0, (1.0, 5000.0),
            help="거래대금 범위 (억원 단위)"
        )
        value_min = int(value[0] * 100_000_000)
        value_max = int(value[1] * 100_000_000)

        # 날짜 범위
        end_date = date.today()
        start_date = end_date - timedelta(days=7)

        period = st.date_input(
            "Added Date Range",
            (start_date, end_date),
            help="종목 추가 날짜 범위"
        )

        st.divider()

        if st.button("🔄 Refresh Data", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

    # -------------------------
    # LOAD DATA
    # -------------------------
    if len(period) == 2:
        period_start, period_end = period
    else:
        period_start = period_end = period[0]

    df = load_stock_pool(
        status,
        score[0], score[1],
        value_min, value_max,
        period_start, period_end
    )

    total = len(df)

    # 상태별 통계
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("총 종목 수", f"{total:,}")
    with col2:
        if total > 0:
            avg_score = df['final_score'].mean()
            st.metric("평균 점수", f"{avg_score:.1f}")
        else:
            st.metric("평균 점수", "-")
    with col3:
        if total > 0:
            avg_value = df['trading_value'].mean() / 100_000_000
            st.metric("평균 거래대금", f"{avg_value:.1f}억")
        else:
            st.metric("평균 거래대금", "-")

    if total == 0:
        st.warning("조건에 맞는 종목이 없습니다.")
        st.info("💡 필터 조건을 조정하거나, 자동 업데이트가 실행되었는지 확인하세요.")
        return

    # -------------------------
    # PAGINATION
    # -------------------------
    if "page" not in st.session_state:
        st.session_state.page = 1

    max_page = (total - 1) // PAGE_SIZE + 1

    st.divider()

    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        if st.button("⬅ Prev", disabled=(st.session_state.page <= 1)):
            st.session_state.page -= 1
            st.rerun()
    with col2:
        st.markdown(
            f"<div style='text-align:center; padding-top:8px;'>Page {st.session_state.page} / {max_page}</div>",
            unsafe_allow_html=True
        )
    with col3:
        if st.button("Next ➡", disabled=(st.session_state.page >= max_page)):
            st.session_state.page += 1
            st.rerun()

    start = (st.session_state.page - 1) * PAGE_SIZE
    end = start + PAGE_SIZE
    page_df = df.iloc[start:end].copy()

    # -------------------------
    # APPROVAL BADGES (배지 계산)
    # -------------------------
    # RSI와 AI 리포트 배치 로드
    tickers = page_df['ticker'].tolist()
    rsi_map = load_rsi_batch(tickers)
    ai_map = load_ai_reports_batch(tickers)

    # 각 종목에 대해 배지 계산
    def calculate_badge(row):
        ticker = row['ticker']
        rsi = rsi_map.get(ticker)
        ai_report = ai_map.get(ticker)

        badge_name, badge_icon, badge_score = get_approval_badge(row, rsi, ai_report)
        return badge_icon

    page_df['배지'] = page_df.apply(calculate_badge, axis=1)

    # -------------------------
    # DATA TABLE WITH FORMATTING
    # -------------------------
    # 표시용 데이터프레임 준비
    display_df = page_df.copy()
    display_df['거래대금(억)'] = (display_df['trading_value'] / 100_000_000).round(1)
    display_df['점수'] = display_df['final_score'].round(1)
    display_df['변화율'] = display_df['change_5d'].round(2)
    display_df['거래량비'] = display_df['vol_ratio'].round(2)

    # 실시간 가격 비교
    display_df['실시간가'] = display_df['realtime_price'].fillna(display_df['close'])

    # 표시할 컬럼만 선택 (배지 추가)
    show_cols = ['배지', 'ticker', 'name', 'close', '실시간가', '거래대금(억)', '변화율', '거래량비', '점수', 'status']

    # 컬럼명 변경
    display_df = display_df[show_cols].rename(columns={
        'ticker': '종목코드',
        'name': '종목명',
        'close': '종가',
        'status': '상태'
    })

    # 선택 가능한 테이블로 표시
    event = st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        height=500,
        selection_mode="single-row",
        on_select="rerun",
        key="stock_pool_table"
    )

    # -------------------------
    # ROW ACTIONS
    # -------------------------
    st.divider()
    st.subheader("⚙️ Stock Actions")

    if total > 0:
        # 선택된 종목 처리
        if event.selection.rows:
            selected_idx = event.selection.rows[0]
            ticker = page_df.iloc[selected_idx]['ticker']
            row = page_df.iloc[selected_idx]
        else:
            # 기본값: 첫 번째 종목
            ticker = page_df.iloc[0]['ticker']
            row = page_df.iloc[0]
            st.info("💡 위 테이블에서 종목을 클릭하여 선택하세요.")

        col1, col2, col3 = st.columns([2, 1, 1])

        with col1:
            memo = st.text_area(
                "📝 Memo",
                row['notes'] if pd.notna(row['notes']) else "",
                height=120,
                key="memo_input"
            )

        with col2:
            st.metric("Final Score", f"{row['final_score']:.1f}")
            st.metric("5D Change", f"{row['change_5d']:.2f}%")

            if pd.notna(row['realtime_price']):
                price_change = ((row['realtime_price'] - row['close']) / row['close'] * 100)
                st.metric(
                    "실시간 변동",
                    f"{price_change:+.2f}%",
                    delta=f"{row['realtime_price']:,.0f}원"
                )

        with col3:
            # 상세보기 버튼
            if st.button("🔍 상세보기", use_container_width=True, type="primary"):
                st.session_state.selected_ticker = ticker
                st.switch_page("pages/stock_detail.py")

            st.divider()

            if status == "monitoring":
                if st.button("✅ Approve", use_container_width=True):
                    update_status(ticker, "approved")
                    st.cache_data.clear()
                    st.rerun()

            if status in ["monitoring", "approved"]:
                if st.button("❌ Reject", use_container_width=True):
                    update_status(ticker, "rejected")
                    st.cache_data.clear()
                    st.rerun()

            if st.button("💾 Save Memo", use_container_width=True):
                update_memo(ticker, memo)
                st.cache_data.clear()
                st.rerun()

        # 종목 정보 표시
        with st.expander("📊 상세 정보", expanded=False):
            info_col1, info_col2 = st.columns(2)
            with info_col1:
                st.write(f"**종목코드**: {row['ticker']}")
                st.write(f"**종목명**: {row['name']}")
                st.write(f"**종가**: {row['close']:,.0f}원")
                st.write(f"**거래대금**: {row['trading_value']:,.0f}원")
            with info_col2:
                st.write(f"**5일 변화율**: {row['change_5d']:.2f}%")
                st.write(f"**거래량 비율**: {row['vol_ratio']:.2f}x")
                st.write(f"**최종 점수**: {row['final_score']:.1f}")
                st.write(f"**추가일**: {row['added_date']}")
