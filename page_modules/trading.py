#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
✅ Approval & Trading - 승인 및 거래 관리
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from db_config import get_db_connection


@st.cache_data(ttl=10)
def get_stocks_by_status(status):
    """상태별 종목 조회"""
    query = """
    SELECT
        ticker, name, close, trading_value, final_score,
        realtime_price, entry_price, exit_price, profit_rate,
        approved_date, monitored_days, notes
    FROM stock_pool
    WHERE status = %s
    ORDER BY final_score DESC
    """
    with get_db_connection() as conn:
        df = pd.read_sql(query, conn, params=(status,))
    return df


@st.cache_data(ttl=60)
def get_monitoring_history(ticker):
    """종목 모니터링 히스토리 조회"""
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
    st.title("✅ Trading Management")
    st.caption("AI 승인 종목 모니터링 및 거래 관리")

    # 탭 구성 (재구성)
    tab1, tab2, tab3 = st.tabs([
        "📋 Approval Queue",
        "💰 Active Trades",
        "📊 Trade History"
    ])

    # ===== Approval Queue (AI 승인 + 매수 대기) =====
    with tab1:
        st.subheader("📋 Approval Queue - AI 승인 종목 모니터링")
        st.caption("✅ AI 추천 통과 종목 | 🔍 조건 재평가 중 | 💰 매수 대기")

        df = get_stocks_by_status('approved')

        if len(df) == 0:
            st.info("🔍 승인된 종목이 없습니다.")
            st.caption("AI Reports에서 STRONG_APPROVE 종목을 승인해주세요.")
        else:
            # 헤더 정보
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("📊 Queue 종목 수", f"{len(df)}개")
            with col2:
                # 재평가 예정 (3일 이상 경과)
                import pandas as pd
                from datetime import datetime, timedelta
                if 'approved_date' in df.columns:
                    df['days_held'] = (datetime.now() - pd.to_datetime(df['approved_date'])).dt.days
                    reeval_count = len(df[df['days_held'] >= 3])
                    st.metric("🔍 재평가 대상", f"{reeval_count}개")
                else:
                    st.metric("🔍 재평가 대상", "0개")
            with col3:
                avg_score = df['final_score'].mean() if len(df) > 0 else 0
                st.metric("📈 평균 점수", f"{avg_score:.1f}")

            st.divider()

            # 종목 테이블 (선택 가능)
            st.subheader("📊 승인 종목 리스트")

            # 표시용 데이터 준비
            display_df = df.copy()
            if 'approved_date' in display_df.columns:
                from datetime import datetime
                display_df['보유일'] = (datetime.now() - pd.to_datetime(display_df['approved_date'])).dt.days
            else:
                display_df['보유일'] = 0

            display_df['거래대금(억)'] = (display_df['trading_value'] / 100_000_000).round(1)

            # 표시할 컬럼만 선택
            table_df = display_df[['ticker', 'name', 'close', 'final_score', '거래대금(억)', '보유일']].copy()
            table_df.columns = ['종목코드', '종목명', '현재가', '점수', '거래대금(억)', '보유일']

            # Streamlit dataframe with selection
            event = st.dataframe(
                table_df,
                use_container_width=True,
                hide_index=True,
                height=300,
                selection_mode="single-row",
                on_select="rerun",
                key="approval_queue_table"
            )

            # 선택된 종목 처리
            if event.selection.rows:
                selected_idx = event.selection.rows[0]
                ticker = df.iloc[selected_idx]['ticker']
                stock_info = df.iloc[selected_idx]
            else:
                # 기본값: 첫 번째 종목
                ticker = df.iloc[0]['ticker']
                stock_info = df.iloc[0]
                st.info("💡 위 테이블에서 종목을 클릭하여 선택하세요.")

            st.divider()

            # 종목 상세 정보
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("종목명", stock_info['name'])
            with col2:
                st.metric("현재가", f"{stock_info['close']:,.0f}원")
            with col3:
                st.metric("종합 점수", f"{stock_info['final_score']:.1f}")
            with col4:
                approved_str = str(stock_info['approved_date']).split()[0] if pd.notna(stock_info['approved_date']) else "N/A"
                days_held = (datetime.now() - pd.to_datetime(stock_info['approved_date'])).days if pd.notna(stock_info['approved_date']) else 0
                st.metric("보유 일수", f"{days_held}일", delta=f"승인: {approved_str}")

            st.divider()

            # 모니터링 데이터 조회
            history_df = get_monitoring_history(ticker)

            if len(history_df) == 0:
                st.warning("⚠️ 모니터링 데이터가 없습니다. populate_monitoring_history.py를 실행해주세요.")
            else:
                # 차트 탭
                chart_tab1, chart_tab2, chart_tab3 = st.tabs(["📈 가격 차트", "📊 거래량", "📉 RSI 신호"])

                with chart_tab1:
                    # 캔들스틱 차트
                    fig = go.Figure()
                    fig.add_trace(go.Candlestick(
                        x=history_df['date'],
                        open=history_df['open'],
                        high=history_df['high'],
                        low=history_df['low'],
                        close=history_df['close'],
                        name='OHLC'
                    ))

                    # 이동평균선
                    if 'ma5' in history_df.columns and history_df['ma5'].notna().any():
                        fig.add_trace(go.Scatter(
                            x=history_df['date'],
                            y=history_df['ma5'],
                            name='MA5',
                            line=dict(color='orange', width=1.5)
                        ))

                    if 'ma20' in history_df.columns and history_df['ma20'].notna().any():
                        fig.add_trace(go.Scatter(
                            x=history_df['date'],
                            y=history_df['ma20'],
                            name='MA20',
                            line=dict(color='green', width=1.5)
                        ))

                    fig.update_layout(
                        xaxis_rangeslider_visible=False,
                        height=400,
                        title=f"{stock_info['name']} 가격 차트"
                    )
                    st.plotly_chart(fig, use_container_width=True)

                with chart_tab2:
                    # 거래량 차트
                    fig2 = go.Figure()
                    fig2.add_trace(go.Bar(
                        x=history_df['date'],
                        y=history_df['volume'],
                        name='거래량',
                        marker_color='lightblue'
                    ))
                    fig2.update_layout(height=250, title="거래량")
                    st.plotly_chart(fig2, use_container_width=True)

                with chart_tab3:
                    # RSI 차트 + 재평가 신호
                    if 'rsi' in history_df.columns and history_df['rsi'].notna().any():
                        fig3 = go.Figure()
                        fig3.add_trace(go.Scatter(
                            x=history_df['date'],
                            y=history_df['rsi'],
                            name='RSI',
                            line=dict(color='purple', width=2)
                        ))
                        fig3.add_hline(y=75, line_dash="dash", line_color="red", annotation_text="탈락 기준(75)")
                        fig3.add_hline(y=70, line_dash="dot", line_color="orange", annotation_text="과매수(70)")
                        fig3.add_hline(y=30, line_dash="dot", line_color="green", annotation_text="과매도(30)")
                        fig3.update_layout(height=250, title="RSI (Relative Strength Index)")
                        st.plotly_chart(fig3, use_container_width=True)

                        # RSI 재평가 신호
                        latest_rsi = history_df['rsi'].iloc[0] if len(history_df) > 0 else None
                        latest_close = history_df['close'].iloc[0] if len(history_df) > 0 else None
                        latest_ma5 = history_df['ma5'].iloc[0] if len(history_df) > 0 and 'ma5' in history_df.columns else None

                        if latest_rsi and latest_close and latest_ma5:
                            # 탈락 조건 체크
                            if latest_rsi > 75 and latest_close < latest_ma5:
                                st.error(f"🚨 탈락 위험: RSI {latest_rsi:.1f} > 75 AND 종가 < MA5")
                                st.caption("조건: RSI 과열 + 가격 하락 → 즉시 재평가 필요")
                            elif latest_rsi > 70:
                                st.warning(f"⚠️ 과매수 주의: RSI {latest_rsi:.1f} (탈락 기준: 75)")
                            elif latest_rsi < 30:
                                st.success(f"✅ 매수 기회: RSI {latest_rsi:.1f} (과매도 구간)")
                            else:
                                st.info(f"⚪ 정상 범위: RSI {latest_rsi:.1f}")
                    else:
                        st.warning("RSI 데이터가 없습니다.")

            st.divider()

            # 액션 버튼
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("💰 매매 시작", type="primary", use_container_width=True, key="start_trading"):
                    st.success(f"✅ {stock_info['name']} 매매 시작 (Kiwoom 연동 예정)")
                    st.caption("status: approved → trading")
            with col2:
                if st.button("🔄 재평가 실행", use_container_width=True, key="reevaluate"):
                    st.info("📊 재평가 로직 실행 (구현 예정)")
                    st.caption("final_score, RSI, 거래량 체크")
            with col3:
                if st.button("❌ Queue 제거", use_container_width=True, key="remove_queue"):
                    st.warning(f"⚠️ {stock_info['name']} Queue에서 제거 (구현 예정)")
                    st.caption("status: approved → rejected")

    # ===== Active Trades (실제 거래 중) =====
    with tab2:
        st.subheader("💰 Active Trades - 실시간 거래 현황")
        st.caption("📈 실제 주문/보유 중인 종목 | 💵 실시간 PnL")

        df = get_stocks_by_status('trading')

        if len(df) == 0:
            st.info("🔍 거래 중인 종목이 없습니다.")
            st.caption("Approval Queue에서 '매매 시작' 버튼을 눌러 거래를 시작하세요.")
        else:
            # 거래 현황 요약
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("📊 거래 중", f"{len(df)}개")
            with col2:
                # 평균 수익률 계산
                if 'entry_price' in df.columns and 'realtime_price' in df.columns:
                    df['current_pnl'] = ((df['realtime_price'] - df['entry_price']) / df['entry_price'] * 100).fillna(0)
                    avg_pnl = df['current_pnl'].mean()
                    st.metric("💰 평균 수익률", f"{avg_pnl:+.2f}%")
                else:
                    st.metric("💰 평균 수익률", "N/A")
            with col3:
                # 승률 (양수 수익률 비율)
                if 'current_pnl' in df.columns:
                    win_rate = (df['current_pnl'] > 0).sum() / len(df) * 100 if len(df) > 0 else 0
                    st.metric("✅ 승률", f"{win_rate:.1f}%")
                else:
                    st.metric("✅ 승률", "N/A")

            st.divider()

            # 거래 현황 테이블
            if 'current_pnl' not in df.columns:
                df['current_pnl'] = 0

            display_df = df[['ticker', 'name', 'entry_price', 'realtime_price', 'current_pnl']].copy()
            display_df.columns = ['종목코드', '종목명', '진입가', '현재가', '수익률(%)']

            st.dataframe(
                display_df,
                use_container_width=True,
                hide_index=True,
                height=400
            )

            st.caption("💡 Kiwoom API 연동 시 실시간 가격 업데이트됩니다.")

    # ===== Trade History (거래 완료) =====
    with tab3:
        st.subheader("📊 Trade History - 거래 이력")

        st.caption("✔️ 체결 완료된 거래 내역 | 📈 수익률 통계")

        df = get_stocks_by_status('completed')

        if len(df) == 0:
            st.info("🔍 완료된 거래가 없습니다.")
            st.caption("거래가 완료되면 여기에 이력이 누적됩니다.")
        else:
            # 통계 요약
            if 'profit_rate' in df.columns and len(df) > 0:
                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    st.metric("📊 총 거래", f"{len(df)}개")

                with col2:
                    win_rate = (df['profit_rate'] > 0).sum() / len(df) * 100
                    st.metric("✅ 승률", f"{win_rate:.1f}%")

                with col3:
                    avg_profit = df['profit_rate'].mean()
                    st.metric("💰 평균 수익률", f"{avg_profit:+.2f}%")

                with col4:
                    total_profit = df['profit_rate'].sum()
                    st.metric("💵 누적 수익률", f"{total_profit:+.2f}%")

            st.divider()

            # 거래 이력 테이블
            display_df = df[['ticker', 'name', 'entry_price', 'exit_price', 'profit_rate']].copy()
            display_df.columns = ['종목코드', '종목명', '진입가', '청산가', '수익률(%)']

            st.dataframe(
                display_df,
                use_container_width=True,
                hide_index=True,
                height=400
            )

            st.caption("💡 거래 이력은 30일간 보관됩니다.")
