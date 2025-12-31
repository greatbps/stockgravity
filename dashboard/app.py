import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import utils
import sys
import os

# 모듈 경로 추가 (루트 디렉토리의 파일을 로드하기 위해)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

st.set_page_config(page_title="StockGravity Dashboard", layout="wide", page_icon="📊")

st.title("📊 StockGravity: Korean Stock Filtering System")

# 사이드바
st.sidebar.header("필터 조건")
st.sidebar.markdown("""
### 현재 적용 중:
- 거래대금: > 1억원
- 종가: > 5,000원
- 5일 등락률: > -5%
- 거래량 증가율: > 0.5배

### 자동 업데이트:
- **시간**: 평일 15:20 (장 마감 10분 전)
- **작업**: 필터링 → 실시간 수집 → AI 분석
- **목적**: 실시간 시세 데이터 수집
""")

st.sidebar.markdown("---")
if st.sidebar.button("🔄 새로고침", use_container_width=True):
    st.rerun()

# 데이터 로드
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
filtered_file_path = os.path.join(project_root, "filtered_stocks.csv")

# 데이터 업데이트 체크 및 자동 실행
import subprocess
from datetime import datetime
import time

def run_auto_update():
    """자동 업데이트 실행 (진행률 표시)"""

    status_container = st.empty()
    progress_container = st.empty()

    with status_container.container():
        st.info("🔄 데이터 자동 업데이트 중...")

        # 전체 진행률
        overall_progress = progress_container.progress(0)

        # 1단계: 필터링
        with st.status("📊 1/3 필터링 중... (2,790개 → 500개)", expanded=True) as status:
            progress_bar = st.progress(0)
            progress_text = st.empty()

            # subprocess를 Popen으로 실행하여 실시간 출력 캡처
            script_path = os.path.join(project_root, "quick_filter.py")
            process = subprocess.Popen(
                [sys.executable, script_path, "--top", "500"],
                cwd=project_root,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )

            # 실시간 출력 파싱
            for line in process.stdout:
                line = line.strip()
                # tqdm 진행률 파싱 (예: "50%|█████     | 1395/2790")
                if '%' in line and '|' in line:
                    try:
                        percent_str = line.split('%')[0].split()[-1]
                        percent = int(percent_str)
                        progress_bar.progress(percent)
                        progress_text.text(f"필터링 {percent}% 진행 중...")
                    except:
                        pass

            process.wait()

            if process.returncode == 0:
                progress_bar.progress(100)
                progress_text.text("✅ 필터링 100% 완료")
                status.update(label="✅ 1/3 필터링 완료", state="complete")
            else:
                st.error(f"❌ 필터링 실패")
                status.update(label="❌ 1/3 필터링 실패", state="error")
                return False

            overall_progress.progress(33)

        # 2단계: 실시간 수집
        with st.status("📡 2/3 실시간 데이터 수집 중... (500개 종목)", expanded=True) as status:
            progress_bar = st.progress(0)
            progress_text = st.empty()

            script_path = os.path.join(project_root, "collect_realtime_data.py")
            process = subprocess.Popen(
                [sys.executable, script_path, "--workers", "10"],
                cwd=project_root,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )

            # 실시간 출력 파싱
            total_stocks = 500
            for line in process.stdout:
                line = line.strip()
                # tqdm 진행률 파싱
                if '%' in line and '|' in line:
                    try:
                        percent_str = line.split('%')[0].split()[-1]
                        percent = int(percent_str)
                        progress_bar.progress(percent)
                        progress_text.text(f"실시간 수집 {percent}% 진행 중...")
                    except:
                        pass

            process.wait()

            if process.returncode == 0:
                progress_bar.progress(100)
                progress_text.text("✅ 실시간 수집 100% 완료")
                status.update(label="✅ 2/3 실시간 수집 완료", state="complete")
            else:
                progress_text.text("⚠️ 실시간 수집 실패 (장 마감 시간)")
                status.update(label="⚠️ 2/3 실시간 수집 건너뜀", state="running")

            overall_progress.progress(66)

        # 3단계: AI 분석
        with st.status("🤖 3/3 AI 분석 중... (상위 5개)", expanded=True) as status:
            progress_bar = st.progress(0)
            progress_text = st.empty()

            script_path = os.path.join(project_root, "generate_ai_report.py")
            process = subprocess.Popen(
                [sys.executable, script_path, "--top", "5"],
                cwd=project_root,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )

            # 실시간 출력 파싱
            total_stocks = 5
            current = 0
            for line in process.stdout:
                line = line.strip()
                # "[1/5]" 형식 파싱
                if '[' in line and '/' in line and ']' in line:
                    try:
                        bracket_content = line.split('[')[1].split(']')[0]
                        current = int(bracket_content.split('/')[0])
                        percent = int((current / total_stocks) * 100)
                        progress_bar.progress(percent)
                        progress_text.text(f"AI 분석 {percent}% 진행 중... ({current}/{total_stocks})")
                    except:
                        pass

            process.wait()

            if process.returncode == 0:
                progress_bar.progress(100)
                progress_text.text("✅ AI 분석 100% 완료")
                status.update(label="✅ 3/3 AI 분석 완료", state="complete")
            else:
                progress_text.text("⚠️ AI 분석 실패 (API 할당량 확인)")
                status.update(label="⚠️ 3/3 AI 분석 건너뜀", state="running")

            overall_progress.progress(100)

        st.success("✅ 모든 업데이트 완료!")
        time.sleep(2)

    status_container.empty()
    progress_container.empty()
    return True

# 데이터가 없거나 오래되었으면 자동 업데이트
if not os.path.exists(filtered_file_path):
    st.warning("📋 초기 데이터 수집 중...")
    if run_auto_update():
        st.rerun()
elif 'auto_update_done' not in st.session_state:
    # 세션 시작 시 한번만 업데이트
    st.session_state.auto_update_done = True
    if run_auto_update():
        st.rerun()

results_df = utils.load_filtered_stocks(filtered_file_path)

# 데이터 업데이트 시간 표시
if os.path.exists(filtered_file_path):
    import datetime
    last_modified = os.path.getmtime(filtered_file_path)
    last_modified_time = datetime.datetime.fromtimestamp(last_modified)
    st.sidebar.info(f"📅 최종 업데이트:\n{last_modified_time.strftime('%Y-%m-%d %H:%M:%S')}")

if results_df.empty:
    st.error("필터링 결과 파일이 없습니다. `quick_filter.py`를 먼저 실행해주세요.")
    st.info("사이드바의 '🔄 필터링 재실행' 버튼을 눌러 데이터를 생성하세요.")
else:
    # 통계 정보
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("전체 종목 수", len(results_df))
    with col2:
        avg_trading_value = results_df['trading_value'].mean() / 100000000
        st.metric("평균 거래대금", f"{avg_trading_value:.1f}억원")
    with col3:
        avg_change = results_df['change_5d'].mean()
        st.metric("평균 5일 등락률", f"{avg_change:.2f}%")
    with col4:
        avg_vol_ratio = results_df['vol_ratio'].mean()
        st.metric("평균 거래량비율", f"{avg_vol_ratio:.2f}x")

    # 탭 구성
    tab1, tab2, tab3 = st.tabs(["📊 필터링 결과", "📈 차트 뷰", "🤖 AI Report"])

    with tab1:
        st.subheader("필터링된 종목 (점수순)")

        # 정렬 옵션
        sort_by = st.selectbox("정렬 기준",
                              ["final_score", "trading_value", "change_5d", "vol_ratio"],
                              format_func=lambda x: {
                                  "final_score": "종합 점수",
                                  "trading_value": "거래대금",
                                  "change_5d": "5일 등락률",
                                  "vol_ratio": "거래량 증가율"
                              }[x])

        display_df = results_df.sort_values(sort_by, ascending=False)

        # 거래대금을 억원 단위로 표시
        display_df['거래대금(억)'] = (display_df['trading_value'] / 100000000).round(1)

        # 표시할 컬럼 선택
        show_columns = ['ticker', 'name', 'close', '거래대금(억)', 'change_5d', 'vol_ratio', 'final_score']
        st.dataframe(
            display_df[show_columns].style.background_gradient(subset=['final_score'], cmap="Greens"),
            use_container_width=True,
            height=600
        )

        st.markdown("""
        **점수 계산 방식:**
        - 거래대금 점수: 40%
        - 모멘텀 점수 (5일 등락률): 30%
        - 거래량 증가율 점수: 30%
        """)

    with tab2:
        st.subheader("종목 상세 차트")
        ticker_list = results_df['ticker'].astype(str).str.zfill(6) + " | " + results_df['name']
        selected_ticker_raw = st.selectbox("종목 선택", ticker_list)

        if selected_ticker_raw:
            selected_ticker = selected_ticker_raw.split(" | ")[0]
            stock_name = selected_ticker_raw.split(" | ")[1]

            # 선택된 종목 정보 표시
            stock_info = results_df[results_df['ticker'].astype(str).str.zfill(6) == selected_ticker].iloc[0]
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("현재가", f"{stock_info['close']:,}원")
            with col2:
                st.metric("5일 등락률", f"{stock_info['change_5d']:.2f}%")
            with col3:
                st.metric("거래량 비율", f"{stock_info['vol_ratio']:.2f}x")
            with col4:
                st.metric("종합 점수", f"{stock_info['final_score']:.1f}")

            price_data_path = os.path.join(project_root, "daily_prices.csv")
            df_price = utils.load_price_data(price_data_path, selected_ticker)

            if not df_price.empty:
                # 차트 그리기
                fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                                    vertical_spacing=0.03, subplot_titles=(f'{stock_name} ({selected_ticker}) 가격 차트', '거래량'),
                                    row_heights=[0.7, 0.3])

                # 1. 캔들차트
                fig.add_trace(go.Candlestick(x=df_price['date'],
                                open=df_price['open'], high=df_price['high'],
                                low=df_price['low'], close=df_price['close'], name='OHLC'), row=1, col=1)

                # 2. 이동평균선
                df_price['MA20'] = df_price['close'].rolling(window=20).mean()
                df_price['MA50'] = df_price['close'].rolling(window=50).mean()

                fig.add_trace(go.Scatter(x=df_price['date'], y=df_price['MA20'], line=dict(color='orange', width=1), name='MA20'), row=1, col=1)
                fig.add_trace(go.Scatter(x=df_price['date'], y=df_price['MA50'], line=dict(color='green', width=1), name='MA50'), row=1, col=1)

                # 3. 거래량
                colors = ['red' if row['open'] - row['close'] >= 0 else 'green' for index, row in df_price.iterrows()]
                fig.add_trace(go.Bar(x=df_price['date'], y=df_price['volume'], marker_color=colors, name='Volume'), row=2, col=1)

                fig.update_layout(xaxis_rangeslider_visible=False, height=600)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("가격 데이터가 없습니다.")

    with tab3:
        st.subheader("🤖 AI Analysis Report")
        report_content = utils.get_latest_report()
        if report_content:
            st.markdown(report_content)
        else:
            st.info("📄 생성된 AI 리포트가 없습니다.")
            st.markdown("""
            ### 🤖 AI 리포트 생성 방법

            사이드바의 **"🤖 AI 분석"** 버튼을 클릭하면 자동으로 생성됩니다.

            #### 생성 내용:
            - 필터링된 상위 5개 종목 선정
            - 각 종목의 최신 뉴스 수집
            - Google Gemini AI를 활용한 심층 분석
            - 투자 의견 및 전략 제시

            #### 필요 조건:
            - `.env` 파일에 `GOOGLE_API_KEY` 설정 필요
            - 필터링된 데이터(`filtered_stocks.csv`)가 있어야 함

            **소요 시간**: 약 2분 (종목당 20~30초)
            """)

            # 환경 체크
            env_file = os.path.join(project_root, ".env")
            if not os.path.exists(env_file):
                st.warning("⚠️ `.env` 파일이 없습니다. Google API Key를 설정해주세요.")
            else:
                st.success("✅ 환경 설정 완료. 사이드바에서 AI 분석을 실행하세요.")
