# StockGravity V0 Design Implementation Guide

## 📁 디렉토리 구조

```
stockgravity/
├── 1231/                           # V0 디자인 참고 이미지
│   ├── dashboard.png
│   ├── AI report.png
│   ├── stockpool.png
│   ├── trading.png
│   ├── approval queue.png
│   └── active trades.png
│
├── skeletons/                      # Streamlit 스켈레톤 코드
│   ├── dashboard_skeleton.py
│   ├── ai_reports_skeleton.py
│   ├── stock_pool_skeleton.py
│   ├── trading_skeleton.py
│   ├── approval_queue_skeleton.py
│   └── active_trades_skeleton.py
│
├── V0_DESIGN_ANALYSIS.md          # 전체 디자인 분석 문서
└── IMPLEMENTATION_GUIDE.md        # 이 파일
```

---

## 🎯 구현 목표

**"보면 V0 디자인 기반이라는 게 느껴지는 Streamlit 화면"**

### 핵심 원칙
1. ✅ **레이아웃 구조 우선** - 색상/장식보다 정보 배치와 계층
2. ✅ **Streamlit 네이티브 컴포넌트만 사용** - HTML/CSS 최소화
3. ✅ **Expander 사용 금지** - 정보 밀도 우선, 접기/펼치기 없음
4. ✅ **Master-Detail 구조 유지** - 리스트 선택 → 상세 정보 흐름
5. ✅ **트레이딩 툴 느낌** - 정보 밀도 높게, 한 화면에 최대한 많은 정보

---

## 📋 구현 로드맵

### Phase 1: 스켈레톤 테스트 및 검증 (현재)

각 스켈레톤 파일을 개별적으로 실행하여 레이아웃 확인:

```bash
# Dashboard 테스트
streamlit run skeletons/dashboard_skeleton.py

# AI Reports 테스트
streamlit run skeletons/ai_reports_skeleton.py

# Stock Pool 테스트
streamlit run skeletons/stock_pool_skeleton.py

# Trading 테스트
streamlit run skeletons/trading_skeleton.py

# Approval Queue 테스트
streamlit run skeletons/approval_queue_skeleton.py

# Active Trades 테스트
streamlit run skeletons/active_trades_skeleton.py
```

**✅ 체크리스트:**
- [ ] 각 페이지가 독립적으로 실행됨
- [ ] 레이아웃이 V0 이미지와 유사함
- [ ] Mock 데이터가 제대로 표시됨
- [ ] 버튼 클릭 시 반응이 있음 (toast/rerun)

---

### Phase 2: 실제 데이터 연결

#### 2.1 Dashboard 구현

**파일:** `page_modules/dashboard_v0_final.py`

**변경 사항:**
1. `get_kpi_data()` - DB에서 실제 KPI 데이터 조회
2. `get_workflow_status()` - 실제 파이프라인 상태 조회
3. `get_action_items()` - 실제 액션 아이템 생성 로직
4. `get_status_distribution()` - 실제 상태별 분포 계산

**DB 쿼리 예시:**
```python
@st.cache_data(ttl=30)
def get_kpi_data():
    with get_db_connection() as conn:
        cur = conn.cursor()

        # Pool Size
        cur.execute("SELECT COUNT(*) FROM stock_pool WHERE status='monitoring'")
        pool_size = cur.fetchone()[0]

        # AI Reports (today)
        cur.execute("""
            SELECT COUNT(*)
            FROM ai_analysis_reports
            WHERE report_date >= CURRENT_DATE
        """)
        ai_reports = cur.fetchone()[0]

        # ... (나머지 KPI)

    return {
        'pool_size': pool_size,
        'ai_reports': ai_reports,
        # ...
    }
```

---

#### 2.2 AI Reports 구현

**파일:** `page_modules/ai_reports_v0_final.py`

**변경 사항:**
1. `get_ai_reports()` - 실제 DB 조회 (이미 구현됨, 재사용)
2. `get_report_detail()` - 선택된 리포트의 상세 정보 조회
3. 액션 버튼 - `update_status()` 함수 연결

**기존 코드 재사용:**
```python
# ai_reports_v0_simple.py의 함수들을 재사용 가능
from page_modules.ai_reports_v0_simple import (
    get_ai_reports,
    update_status
)
```

---

#### 2.3 Stock Pool 구현

**파일:** `page_modules/stock_pool_v0_final.py`

**변경 사항:**
1. `get_stock_pool_data()` - 실제 DB 조회
2. 필터링 로직 - 검색/Sector/Status 필터 적용
3. 페이지네이션 (선택적) - 500개 이상일 경우

**DB 쿼리 예시:**
```python
@st.cache_data(ttl=60)
def get_stock_pool_data():
    query = """
        SELECT
            ticker,
            name as company_name,
            sector,
            close as price,
            change_5d as change_pct,
            volume_avg_20 / 1000000 as volume_m,
            final_score as ai_score,
            status
        FROM stock_pool
        ORDER BY final_score DESC
    """

    with get_db_connection() as conn:
        df = pd.read_sql(query, conn)

    return df
```

---

#### 2.4 Trading 구현

**파일:** `page_modules/trading_v0_final.py` (새로 생성)

**변경 사항:**
1. Kiwoom API 연결
2. 실시간 계좌 정보 조회
3. 실시간 시장 지수 조회
4. 주문 실행 로직

**주의사항:**
- Trading 페이지는 Kiwoom API 연동이 필요
- 기존에 구현된 Trading 페이지가 없으므로 새로 생성 필요
- 스켈레톤 코드를 기반으로 API 연결 추가

---

#### 2.5 Approval Queue 구현

**파일:** `page_modules/approval_queue_v0_final.py` (새로 생성)

**변경 사항:**
1. `get_pending_approvals()` - status='approved' 종목 조회
2. `get_quick_analysis()` - 기술적 지표 조회
3. 액션 버튼 - 상태 변경 (approved → trading)

**DB 쿼리 예시:**
```python
def get_pending_approvals():
    query = """
        SELECT
            sp.ticker,
            sp.name,
            sp.final_score as score,
            sp.close as price,
            sp.change_5d as change,
            sp.approved_date::date as date
        FROM stock_pool sp
        WHERE sp.status = 'approved'
        ORDER BY sp.final_score DESC
    """

    with get_db_connection() as conn:
        df = pd.read_sql(query, conn)

    return df
```

---

#### 2.6 Active Trades 구현

**파일:** `page_modules/active_trades_v0_final.py` (새로 생성)

**변경 사항:**
1. Kiwoom API에서 실시간 포지션 조회
2. P&L 계산
3. 포지션 추가/청산 로직

**주의사항:**
- 실제 거래 데이터는 Kiwoom API에서 조회
- 백테스트 모드일 경우 DB에서 조회 가능

---

### Phase 3: 페이지 통합

#### 3.1 기존 파일 백업

```bash
# 기존 page_modules 백업
cp -r page_modules page_modules_backup_$(date +%Y%m%d)
```

#### 3.2 새 파일 적용

```bash
# 스켈레톤 기반 새 파일 생성
# dashboard_v0_final.py → dashboard_v0_simple.py 대체
# ai_reports_v0_final.py → ai_reports_v0_simple.py 대체
# ... (나머지 페이지)
```

#### 3.3 app.py 및 pages/ 업데이트

**app.py:**
```python
from page_modules import dashboard_v0_final as dashboard
```

**pages/2_🤖_AI_Reports.py:**
```python
from page_modules import ai_reports_v0_final as ai_reports
```

**pages/1_📦_Stock_Pool.py:** (새로 생성)
```python
from page_modules import stock_pool_v0_final as stock_pool

st.set_page_config(
    page_title="Stock Pool - StockGravity",
    page_icon="📦",
    layout="wide"
)

stock_pool.render()
```

**pages/3_✅_Trading.py:** (기존 파일 수정)
```python
from page_modules import trading_v0_final as trading

trading.render()
```

**pages/4_📋_Approval_Queue.py:** (새로 생성)
```python
from page_modules import approval_queue_v0_final as approval_queue

st.set_page_config(
    page_title="Approval Queue - StockGravity",
    page_icon="✅",
    layout="wide"
)

approval_queue.render()
```

**pages/5_📈_Active_Trades.py:** (새로 생성)
```python
from page_modules import active_trades_v0_final as active_trades

st.set_page_config(
    page_title="Active Trades - StockGravity",
    page_icon="📈",
    layout="wide"
)

active_trades.render()
```

---

### Phase 4: 사이드바 통합

**sidebar_utils.py 업데이트:**

V0 디자인에 맞춰 이미 업데이트 완료 (2-column 레이아웃 + AI Engine Status)

---

## 🚧 Streamlit 한계 및 대안 (재확인)

### 1. Workflow Progress (파이프라인 시각화)

**V0**: 연결선이 있는 5단계 파이프라인

**Streamlit 대안:**
```python
cols = st.columns(5)
for idx, step in enumerate(workflow_steps):
    with cols[idx]:
        st.markdown(f"### {step['icon']}")  # ✅/⏳/○
        st.markdown(f"**{step['name']}**")
        st.caption(f"{step['count']}")
```

### 2. 상태 배지 (Status Badges)

**V0**: 커스텀 배지 (색상 + 텍스트)

**Streamlit 대안:**
- DataFrame 내: 이모지 조합 (🟢 BUY, 🟡 HOLD, 🔴 SELL)
- 독립 위젯: `st.success()`, `st.warning()`, `st.error()`
- 백틱 강조: `BUY`, `STRONG_APPROVE`

### 3. Master-Detail 하이라이트

**V0**: 선택된 항목에 파란 테두리

**Streamlit 대안:**
```python
if is_selected:
    st.info("📌 Selected", icon="📌")
```

### 4. P&L 색상 (손익)

**V0**: 녹색(+) / 빨간색(-)

**Streamlit 대안:**
```python
# DataFrame 컬럼
if pnl >= 0:
    st.markdown(f"**:green[+₩{pnl:,}]**")
else:
    st.markdown(f"**:red[-₩{abs(pnl):,}]**")

# Metric delta
st.metric("P&L", value, delta=f"{pnl_pct:+.2f}%", delta_color="normal")
```

---

## ✅ 완성 체크리스트

### Dashboard
- [ ] KPI 카드 4개 (실제 DB 데이터)
- [ ] Workflow Progress (5단계 상태)
- [ ] Action Needed (동적 생성)
- [ ] Status Distribution (차트 2개)

### AI Reports
- [ ] Top 20 리스트 (왼쪽 패널)
- [ ] 상세 정보 (오른쪽 패널, 4 탭)
- [ ] 선택 상태 유지 (session_state)
- [ ] 액션 버튼 (Approve/Monitor/Reject)

### Stock Pool
- [ ] 검색 + 2 필터 (Sector, Status)
- [ ] 고밀도 데이터 테이블 (500개)
- [ ] 정렬 가능한 컬럼
- [ ] 상태 배지 색상 구분

### Trading
- [ ] 주문 폼 (Stock 검색, Buy/Sell, Order Type, Quantity)
- [ ] 계좌 정보 (Available Cash, Buying Power, Margin)
- [ ] 시장 지수 (KOSPI, KOSDAQ)
- [ ] Trading Limits

### Approval Queue
- [ ] Pending Approvals 리스트 (왼쪽)
- [ ] Quick Analysis (오른쪽)
- [ ] Technical Indicators
- [ ] 3 액션 버튼

### Active Trades
- [ ] Portfolio KPI 4개
- [ ] Active Positions 테이블
- [ ] P&L 색상 구분 (녹색/빨간색)
- [ ] Quick Actions (New Position, Refresh, Export)

---

## 🎨 디자인 일관성 체크

### 공통 요소
- [ ] 모든 페이지 `layout="wide"`
- [ ] Page Title + Caption 일관성
- [ ] `st.divider()` 적절한 사용
- [ ] KPI Cards: `st.metric()` 통일
- [ ] 액션 버튼: `use_container_width=True`
- [ ] Primary 버튼: `type="primary"` 사용

### Master-Detail 페이지
- [ ] 비율: 왼쪽 30-55% / 오른쪽 45-70%
- [ ] 선택 메커니즘: `st.session_state` 사용
- [ ] 선택 표시: `st.info("📌 Selected")`
- [ ] 버튼: `st.button(f"Select #{idx}")`

### 데이터 테이블
- [ ] `st.dataframe()` 사용
- [ ] `use_container_width=True`
- [ ] `hide_index=True`
- [ ] `column_config` 설정
- [ ] 적절한 height 설정 (400-600px)

---

## 🔄 테스트 시나리오

### 1. 전체 워크플로우 테스트

```
Dashboard → AI Reports → Approval Queue → Active Trades
```

1. Dashboard에서 "5 AI Reports need review" 확인
2. AI Reports 페이지로 이동
3. Top 1 종목 선택 → 상세 정보 확인
4. "Approve for Trading" 클릭
5. Approval Queue에서 승인된 종목 확인
6. "Start Trading" 클릭
7. Active Trades에서 포지션 확인

### 2. 필터링 테스트

**Stock Pool:**
- 검색어 입력: "Samsung"
- Sector 필터: "Technology"
- Status 필터: "qualified"
- 결과 개수 확인

### 3. 반응형 테스트

- 브라우저 폭 조절 (Wide → Normal → Narrow)
- 2-column 레이아웃이 적절히 조정되는지 확인

---

## 📝 다음 단계

1. **스켈레톤 테스트** - 각 파일을 독립적으로 실행하여 레이아웃 검증
2. **Mock 데이터 조정** - 실제 데이터와 유사하게 Mock 데이터 수정
3. **DB 연결** - 실제 PostgreSQL 쿼리로 교체
4. **API 연결** - Kiwoom API 연동 (Trading, Active Trades)
5. **통합 테스트** - 전체 워크플로우 테스트
6. **UI 미세 조정** - 간격, 폰트 크기, 색상 등 조정
7. **성능 최적화** - 캐싱 전략 검토

---

## 💡 팁

### 빠른 프로토타이핑
```bash
# 여러 페이지를 동시에 테스트하려면 포트 변경
streamlit run skeletons/dashboard_skeleton.py --server.port 8501
streamlit run skeletons/ai_reports_skeleton.py --server.port 8502
```

### 실시간 데이터 업데이트
```python
# Auto-refresh (선택적)
st_autorefresh(interval=30000)  # 30초마다 자동 새로고침
```

### 디버깅
```python
# 데이터 확인
with st.expander("🐛 Debug Data"):  # 개발 중에만 사용
    st.json(kpi_data)
    st.dataframe(df)
```

---

## 📚 참고 자료

- **V0 디자인 이미지**: `1231/` 폴더
- **디자인 분석**: `V0_DESIGN_ANALYSIS.md`
- **스켈레톤 코드**: `skeletons/` 폴더
- **Streamlit 문서**: https://docs.streamlit.io/

---

## 🎯 최종 목표 달성 기준

**"보면 V0 디자인 기반이라는 게 느껴지는 Streamlit 화면"**

✅ 레이아웃이 V0 이미지와 90% 이상 유사
✅ 정보 밀도가 높고 트레이딩 툴 느낌
✅ Master-Detail 구조가 자연스러움
✅ 모든 기능이 Streamlit 네이티브 컴포넌트로 구현됨
✅ Expander 없이 한 화면에 모든 정보 표시
