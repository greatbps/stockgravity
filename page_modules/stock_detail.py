#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📌 Stock Detail - 종목 상세 페이지
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from db_config import get_db_connection
from approval_badge import (
    get_approval_badge,
    render_badge_html,
    should_enable_approval,
    get_badge_explanation
)


# =========================
# DB QUERY FUNCTIONS
# =========================
@st.cache_data(ttl=30)
def load_stock_info(ticker):
    """기본 종목 정보"""
    query = """
    SELECT *
    FROM stock_pool
    WHERE ticker = %s
    """
    with get_db_connection() as conn:
        return pd.read_sql(query, conn, params=(ticker,))


@st.cache_data(ttl=60)
def load_monitoring_history(ticker):
    """모니터링 히스토리"""
    query = """
    SELECT date, open, high, low, close, volume, ma5, ma20, rsi
    FROM stock_monitoring_history
    WHERE ticker = %s
    ORDER BY date
    """
    with get_db_connection() as conn:
        return pd.read_sql(query, conn, params=(ticker,))


@st.cache_data(ttl=300)
def load_ai_report(ticker):
    """AI 리포트"""
    query = """
    SELECT *
    FROM ai_analysis_reports
    WHERE ticker = %s
    ORDER BY report_date DESC
    LIMIT 1
    """
    with get_db_connection() as conn:
        return pd.read_sql(query, conn, params=(ticker,))


@st.cache_data(ttl=60)
def get_latest_rsi(ticker):
    """최근 RSI 값 조회"""
    query = """
    SELECT rsi
    FROM stock_monitoring_history
    WHERE ticker = %s AND rsi IS NOT NULL
    ORDER BY date DESC
    LIMIT 1
    """
    with get_db_connection() as conn:
        result = pd.read_sql(query, conn, params=(ticker,))
        if not result.empty:
            return result.iloc[0]['rsi']
        return None


# =========================
# ACTION HANDLERS
# =========================
def update_memo(ticker, memo):
    """메모 저장"""
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "UPDATE stock_pool SET notes=%s WHERE ticker=%s",
            (memo, ticker)
        )
    st.toast("메모 저장 완료", icon="📝")
    st.cache_data.clear()


def approve_stock(ticker):
    """종목 승인"""
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "UPDATE stock_pool SET status='approved', approved_date=NOW() WHERE ticker=%s",
            (ticker,)
        )
    st.toast("승인 완료", icon="✅")
    st.cache_data.clear()


def reject_stock(ticker):
    """종목 거부"""
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "UPDATE stock_pool SET status='rejected' WHERE ticker=%s",
            (ticker,)
        )
    st.toast("거부 처리됨", icon="❌")
    st.cache_data.clear()


# =========================
# MAIN RENDER
# =========================
def render(ticker: str = None):
    """종목 상세 페이지 렌더링"""

    # 종목 선택 확인
    if ticker is None:
        ticker = st.session_state.get("selected_ticker")

    if not ticker:
        st.warning("선택된 종목이 없습니다.")
        st.info("Stock Pool 페이지에서 종목을 선택해주세요.")
        if st.button("📦 Stock Pool로 이동"):
            st.switch_page("pages/1_📦_Stock_Pool.py")
        return

    # 데이터 로드
    info_df = load_stock_info(ticker)

    if info_df.empty:
        st.error(f"종목 정보를 찾을 수 없습니다: {ticker}")
        if st.button("← 돌아가기"):
            st.switch_page("pages/1_📦_Stock_Pool.py")
        return

    info = info_df.iloc[0]
    history = load_monitoring_history(ticker)
    ai = load_ai_report(ticker)
    latest_rsi = get_latest_rsi(ticker)

    # =============================
    # APPROVAL BADGE 계산
    # =============================
    badge_name, badge_icon, badge_score = get_approval_badge(
        info,
        rsi=latest_rsi,
        ai_report=ai if not ai.empty else None
    )

    # =============================
    # HEADER
    # =============================
    col_back, col_title = st.columns([1, 9])

    with col_back:
        if st.button("← 뒤로"):
            st.switch_page("pages/1_📦_Stock_Pool.py")

    with col_title:
        st.title(f"📌 {info['name']} ({info['ticker']})")

    # 승인 추천 배지 표시
    st.markdown(
        render_badge_html(badge_name, badge_icon, badge_score),
        unsafe_allow_html=True
    )
    st.caption(get_badge_explanation(badge_name, badge_score))

    # 주요 지표 카드
    c1, c2, c3, c4 = st.columns(4)

    with c1:
        current_price = info['realtime_price'] if pd.notna(info['realtime_price']) else info['close']
        st.metric("현재가", f"{current_price:,.0f}원")

    with c2:
        st.metric("Final Score", f"{info['final_score']:.1f}")

    with c3:
        change_value = info['change_5d']
        st.metric("5일 변화율", f"{change_value:.2f}%", delta=f"{change_value:.2f}%")

    with c4:
        status_emoji = {
            'monitoring': '📡',
            'approved': '✅',
            'rejected': '❌',
            'trading': '💰',
            'completed': '✔️'
        }
        emoji = status_emoji.get(info['status'], 'ℹ️')
        st.metric("상태", f"{emoji} {info['status']}")

    st.divider()

    # =============================
    # TABS
    # =============================
    tab1, tab2, tab3 = st.tabs([
        "📈 Price & Indicators",
        "🤖 AI Analysis",
        "📝 Notes & Actions"
    ])

    # =============================
    # TAB 1: Price & Indicators
    # =============================
    with tab1:
        if history.empty:
            st.info("모니터링 히스토리 데이터가 없습니다.")
        else:
            # 캔들스틱 + 이동평균선
            st.subheader("📊 Price Chart")

            fig = go.Figure()

            # 캔들스틱
            fig.add_trace(go.Candlestick(
                x=history["date"],
                open=history["open"],
                high=history["high"],
                low=history["low"],
                close=history["close"],
                name="Price"
            ))

            # 이동평균선 MA5
            if 'ma5' in history.columns and history['ma5'].notna().any():
                fig.add_trace(go.Scatter(
                    x=history["date"],
                    y=history["ma5"],
                    name="MA5",
                    line=dict(color="orange", width=1.5)
                ))

            # 이동평균선 MA20
            if 'ma20' in history.columns and history['ma20'].notna().any():
                fig.add_trace(go.Scatter(
                    x=history["date"],
                    y=history["ma20"],
                    name="MA20",
                    line=dict(color="blue", width=1.5)
                ))

            fig.update_layout(
                height=500,
                margin=dict(l=20, r=20, t=30, b=20),
                xaxis_rangeslider_visible=False,
                xaxis_title="Date",
                yaxis_title="Price (₩)"
            )

            st.plotly_chart(fig, use_container_width=True)

            # 거래량
            st.subheader("📊 Volume")
            fig_volume = go.Figure()
            fig_volume.add_trace(go.Bar(
                x=history["date"],
                y=history["volume"],
                name="Volume",
                marker_color="lightblue"
            ))
            fig_volume.update_layout(
                height=200,
                margin=dict(l=20, r=20, t=10, b=20),
                xaxis_title="Date",
                yaxis_title="Volume"
            )
            st.plotly_chart(fig_volume, use_container_width=True)

            # RSI
            if 'rsi' in history.columns and history['rsi'].notna().any():
                st.subheader("📊 RSI (Relative Strength Index)")

                fig_rsi = go.Figure()
                fig_rsi.add_trace(go.Scatter(
                    x=history["date"],
                    y=history["rsi"],
                    name="RSI",
                    line=dict(color="purple", width=2)
                ))

                # 과매수/과매도 라인
                fig_rsi.add_hline(y=70, line_dash="dash", line_color="red",
                                  annotation_text="과매수", annotation_position="right")
                fig_rsi.add_hline(y=30, line_dash="dash", line_color="green",
                                  annotation_text="과매도", annotation_position="right")

                fig_rsi.update_layout(
                    height=200,
                    margin=dict(l=20, r=20, t=10, b=20),
                    xaxis_title="Date",
                    yaxis_title="RSI",
                    yaxis_range=[0, 100]
                )
                st.plotly_chart(fig_rsi, use_container_width=True)

            # 데이터 테이블
            st.divider()
            st.subheader("📋 Recent Data")

            display_history = history[['date', 'open', 'high', 'low', 'close', 'volume']].tail(10).copy()
            display_history.columns = ['날짜', '시가', '고가', '저가', '종가', '거래량']

            st.dataframe(
                display_history,
                use_container_width=True,
                hide_index=True
            )

    # =============================
    # TAB 2: AI Analysis
    # =============================
    with tab2:
        if ai.empty:
            st.warning("AI 분석 리포트가 없습니다.")
            st.info("자동 업데이트 시 상위 종목에 대해 AI 분석이 생성됩니다.")
        else:
            report = ai.iloc[0]

            # 추천 등급 색상
            rec_color = {
                "BUY": "🟢",
                "HOLD": "🟡",
                "SELL": "🔴"
            }

            emoji = rec_color.get(report['recommendation'], 'ℹ️')

            st.subheader(f"{emoji} Recommendation: **{report['recommendation']}**")

            # 신뢰도 점수
            st.write("**신뢰도 점수:**")
            if pd.notna(report['confidence_score']):
                st.progress(float(report['confidence_score']))
                st.caption(f"{report['confidence_score']:.0%}")
            else:
                st.caption("신뢰도 정보 없음")

            st.divider()

            # 2단 레이아웃
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("### 🧠 Summary")
                if pd.notna(report['summary']):
                    st.info(report['summary'])
                else:
                    st.caption("요약 없음")

                st.markdown("### 📈 Momentum Analysis")
                if pd.notna(report['momentum_analysis']):
                    st.write(report['momentum_analysis'])
                else:
                    st.caption("모멘텀 분석 없음")

            with col2:
                st.markdown("### 💧 Liquidity Analysis")
                if pd.notna(report['liquidity_analysis']):
                    st.write(report['liquidity_analysis'])
                else:
                    st.caption("유동성 분석 없음")

                st.markdown("### ⚠️ Risk Factors")
                if pd.notna(report['risk_factors']):
                    st.warning(report['risk_factors'])
                else:
                    st.caption("리스크 요인 없음")

            # 리포트 날짜
            if pd.notna(report['report_date']):
                st.caption(f"📅 분석 일자: {report['report_date']}")

    # =============================
    # TAB 3: Notes & Actions
    # =============================
    with tab3:
        st.subheader("📝 종목 메모")

        memo = st.text_area(
            "메모 입력",
            value=info['notes'] if pd.notna(info['notes']) else "",
            height=150,
            help="종목에 대한 메모나 관찰 내용을 기록하세요"
        )

        st.divider()

        st.subheader("⚙️ Actions")

        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("💾 메모 저장", use_container_width=True):
                update_memo(ticker, memo)
                st.rerun()

        with col2:
            # 승인 버튼 - 배지 기반 조건부 활성화
            approval_enabled = should_enable_approval(badge_name) and info['status'] == 'monitoring'

            if st.button(
                "✅ 승인",
                use_container_width=True,
                type="primary" if approval_enabled else "secondary",
                disabled=not approval_enabled
            ):
                approve_stock(ticker)
                st.rerun()

            # 비활성화 이유 표시
            if not approval_enabled and info['status'] == 'monitoring':
                st.caption("⛔ 배지 점수 미달로 승인 불가")

        with col3:
            if info['status'] in ['monitoring', 'approved']:
                if st.button("❌ 거부", use_container_width=True):
                    reject_stock(ticker)
                    st.rerun()
            else:
                st.button("❌ 거부", use_container_width=True, disabled=True)

        # 종목 상세 정보
        st.divider()
        st.subheader("📊 상세 정보")

        info_col1, info_col2, info_col3 = st.columns(3)

        with info_col1:
            st.write("**기본 정보**")
            st.write(f"종목코드: {info['ticker']}")
            st.write(f"종목명: {info['name']}")
            st.write(f"종가: {info['close']:,.0f}원")

        with info_col2:
            st.write("**거래 정보**")
            st.write(f"거래대금: {info['trading_value']:,.0f}원")
            st.write(f"거래량 비율: {info['vol_ratio']:.2f}x")
            if pd.notna(info['realtime_volume']):
                st.write(f"실시간 거래량: {info['realtime_volume']:,.0f}")

        with info_col3:
            st.write("**모니터링 정보**")
            st.write(f"추가일: {info['added_date']}")
            st.write(f"모니터링 일수: {info['monitored_days']}일")
            if pd.notna(info['approved_date']):
                st.write(f"승인일: {info['approved_date']}")
