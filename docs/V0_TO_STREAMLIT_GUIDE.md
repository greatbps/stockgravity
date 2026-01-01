# V0 → Streamlit 구현 가이드

## 🎯 목표
V0 디자인의 **정보 구조 + 레이아웃 + 사용자 흐름**을 Streamlit으로 재현

## ⚠️ 제약 조건
- ✅ Streamlit 기본 컴포넌트만 사용
- ✅ React, HTML, Tailwind 사용 금지
- ✅ Expander 사용 금지
- ✅ Dark theme 기준
- ✅ 트레이딩 툴다운 고밀도 정보 표시
- ✅ 좌측 사이드바 + 메인 콘텐츠 구조 유지

---

# 1️⃣ Dashboard

## 레이아웃 구조 분석

### 영역 분리 (상→하)
```
┌─────────────────────────────────────────────┐
│ Header: "Dashboard" + 설명                   │
├─────────────────────────────────────────────┤
│ Zone A: KPI 카드 4개 (동일 비중)              │  ← 시스템 현황 한눈에
│ [Stock Pool] [AI Reports] [Queue] [Trades]  │
├─────────────────────────────────────────────┤
│ Zone B: Workflow Progress (5단계)            │  ← 파이프라인 진행 상태
│ Filter → Pool → AI → Approval → Trading     │
├─────────────────────────────────────────────┤
│ Zone C: 2-column                             │
│ ┌─────────────────┬─────────────────────┐  │
│ │ Action Needed   │ Status Distribution │  │  ← 액션 + 통계
│ │ (우선순위 높음)  │ (현황 파악)          │  │
│ └─────────────────┴─────────────────────┘  │
└─────────────────────────────────────────────┘
```

### 정보 우선순위
1. **최우선**: KPI 카드 - 숫자로 시스템 상태 즉시 파악
2. **2순위**: Workflow Progress - 어디까지 진행됐는지
3. **3순위**: Action Needed - 내가 해야 할 일
4. **4순위**: Status Distribution - 세부 통계

### 왜 이렇게 배치되나?
- **상단 KPI**: 트레이더가 제일 먼저 보는 정보 = 숫자
- **중단 파이프라인**: 시스템이 자동으로 어디까지 처리했는지 → 안심감
- **하단 2-column**:
  - 왼쪽(넓음) = 내가 해야 할 일 (액션 유도)
  - 오른쪽(좁음) = 참고 정보 (통계)

### Streamlit 구현 핵심
```python
# Zone A: KPI Cards
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("📦 Stock Pool", "500")
# ... 반복

st.divider()

# Zone B: Workflow Progress
cols = st.columns(5)
for idx, step in enumerate(workflow_steps):
    with cols[idx]:
        st.markdown(f"### {step['icon']}")  # ✅ / ⏳ / ○
        st.markdown(f"**{step['name']}**")
        st.caption(step['count'])

st.divider()

# Zone C: 2-column
left, right = st.columns([2, 1])
with left:
    # Action items (st.warning, st.info)
with right:
    # Status distribution (st.progress)
```

---

# 2️⃣ Stock Pool

## 레이아웃 구조 분석

### 영역 분리
```
┌─────────────────────────────────────────────┐
│ Header: "Stock Pool" + "Monitoring 500..."  │
├─────────────────────────────────────────────┤
│ Zone A: 검색 + 필터 (3-column)                │
│ [Search...............] [Sector▼] [Status▼] │
├─────────────────────────────────────────────┤
│ Zone B: 데이터 테이블 (전체 높이의 80%)        │
│ ┌─────┬────────┬────────┬───────┬─────┐   │
│ │Tick │Company │Sector  │Price  │Score│   │
│ │STK01│Comp1   │Health  │33,371 │76   │   │
│ │STK02│Comp2   │Energy  │71,582 │54   │   │
│ │ ... │ ...    │ ...    │ ...   │ ... │   │
│ └─────┴────────┴────────┴───────┴─────┘   │
└─────────────────────────────────────────────┘
```

### 정보 우선순위
1. **테이블** - 500개 종목을 빠르게 스캔
2. **필터** - 원하는 조건으로 좁히기
3. **검색** - 특정 종목 찾기

### 왜 이렇게 배치되나?
- **검색/필터 상단**: 사용 빈도 높음, 바로 접근
- **테이블 전체 공간**: 정보 밀도 최대화 (트레이딩 툴 특성)
- **컬럼 순서**: Ticker(식별) → Name(확인) → Sector(분류) → Price/Change(시장 정보) → Score(AI 판단) → Status(상태)

### Streamlit 구현 핵심
```python
# Zone A: Search + Filters
col1, col2, col3 = st.columns([3, 1, 1])
with col1:
    search = st.text_input("Search", label_visibility="collapsed")
with col2:
    sector = st.selectbox("Sector", sectors, label_visibility="collapsed")
with col3:
    status = st.selectbox("Status", statuses, label_visibility="collapsed")

# Zone B: Data Table
st.dataframe(
    df,
    use_container_width=True,
    height=600,  # 높이 고정으로 정보 밀도 확보
    hide_index=True,
    column_config={
        'Ticker': st.column_config.TextColumn('Ticker', width='small'),
        # ...
    }
)
```

---

# 3️⃣ AI Reports

## 레이아웃 구조 분석

### 영역 분리 (Master-Detail)
```
┌──────────┬────────────────────────────────┐
│ Master   │ Detail                          │
│ (30%)    │ (70%)                           │
│          │                                 │
│ [#1]     │ ┌─────────────────────────────┐│
│ 005930   │ │ Samsung Electronics    [BUY]││  ← Header
│ Score:92 │ │ AI Score: 92                 ││
│ ▲ +3.2%  │ └─────────────────────────────┘│
│ [Select] │                                 │
│          │ [Summary][Momentum][Liq][Risk] │  ← Tabs
├──────────┤                                 │
│ [#2]     │ ┌─────────────────────────────┐│
│ 035420   │ │ Analysis Summary             ││  ← Tab Content
│ Score:89 │ │ Strong momentum...           ││
│ ▲ +2.8%  │ │                              ││
│ [Select] │ │ Technical Rating: Strong     ││
│          │ │ ▬▬▬▬▬ 85%                   ││
├──────────┤ │                              ││
│ [#3]     │ │ Key Factors:                 ││
│ ...      │ │ ✓ Institutional buying       ││
│          │ └─────────────────────────────┘│
│          │                                 │
│          │ [Approve][Monitor][Reject]     │  ← Actions
└──────────┴────────────────────────────────┘
```

### 정보 우선순위
1. **리스트**: 20개 종목 빠르게 훑기
2. **선택**: 관심 종목 클릭
3. **상세 분석**: 4개 영역(Summary/Momentum/Liquidity/Risk)으로 체계적 검토
4. **의사결정**: Approve/Monitor/Reject

### 왜 이렇게 배치되나?
- **Master-Detail**: 트레이딩 툴의 정석 패턴 (리스트 → 상세 → 액션)
- **왼쪽 좁음**: 스캔만 하면 됨 (Ticker + Score + Badge)
- **오른쪽 넓음**: 의사결정에 필요한 모든 정보
- **탭 구조**: 정보 과부하 방지, 필요한 것만 펼쳐보기

### Streamlit 구현 핵심
```python
# Master-Detail Layout
left, right = st.columns([1, 2])

# Session state로 선택 상태 유지
if 'selected_idx' not in st.session_state:
    st.session_state.selected_idx = 0

# Left: Master List
with left:
    for idx, report in enumerate(reports):
        is_selected = (idx == st.session_state.selected_idx)

        # 리스트 아이템 렌더링
        render_report_item(report, is_selected)

        # 선택 버튼
        if st.button(f"Select #{idx+1}", key=f"sel_{idx}"):
            st.session_state.selected_idx = idx
            st.rerun()

        st.divider()

# Right: Detail Panel
with right:
    selected = reports[st.session_state.selected_idx]

    # Header
    st.markdown(f"# {selected['name']}")
    st.metric("AI Score", selected['score'])

    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs(["Summary", "Momentum", "Liquidity", "Risk"])

    with tab1:
        st.markdown("### Analysis Summary")
        # ...

    # Actions
    col1, col2, col3 = st.columns(3)
    with col1:
        st.button("✅ Approve", type="primary")
```

---

# 4️⃣ Active Trades

## 레이아웃 구조 분석

### 영역 분리
```
┌─────────────────────────────────────────────┐
│ Header: "Active Trades" + "8 positions"     │
├─────────────────────────────────────────────┤
│ Zone A: Portfolio KPI (4-column)             │
│ [Total P&L] [Avg P&L] [Total Value] [Pos]   │
├─────────────────────────────────────────────┤
│ Zone B: Active Positions Table               │
│ ┌──────┬────────┬───────┬────────┬─────┐   │
│ │Ticker│Entry   │Current│Quantity│P&L  │   │
│ │STK023│68,500  │71,200 │150     │+405K│   │
│ │STK089│142,000 │138,500│80      │-280K│   │
│ │ ...  │ ...    │ ...   │ ...    │ ... │   │
│ └──────┴────────┴───────┴────────┴─────┘   │
└─────────────────────────────────────────────┘
```

### 정보 우선순위
1. **Portfolio KPI**: 전체 수익률 즉시 파악
2. **Positions Table**: 종목별 손익 모니터링
3. **P&L 색상**: 녹색(+) / 빨강(-) 구분 명확히

### 왜 이렇게 배치되나?
- **상단 KPI**: "얼마 벌었나?" = 트레이더의 최대 관심사
- **테이블**: 개별 종목 모니터링, 손절/익절 판단
- **P&L 강조**: 색상으로 즉시 인지

### Streamlit 구현 핵심
```python
# Zone A: Portfolio KPI
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total P&L", "₩816,000", "+1.03%", delta_color="normal")
# ...

st.divider()

# Zone B: Positions Table
# P&L 색상 구분
def format_pnl(row):
    pnl = row['pnl']
    if pnl >= 0:
        return f"+₩{pnl:,}"  # 녹색
    else:
        return f"-₩{abs(pnl):,}"  # 빨강

df['P&L'] = df.apply(format_pnl, axis=1)

st.dataframe(
    df,
    use_container_width=True,
    height=500,
    column_config={
        'P&L': st.column_config.TextColumn('P&L', width='medium'),
    }
)
```

---

# 🎨 색상/배지 규칙

## 추천 등급 (Recommendation)
```python
RECOMMENDATION_BADGES = {
    'BUY': {
        'emoji': '🟢',
        'color': 'success',  # st.success()
        'text': 'STRONG BUY'
    },
    'HOLD': {
        'emoji': '🟡',
        'color': 'warning',  # st.warning()
        'text': 'WATCH MORE'
    },
    'MONITOR': {
        'emoji': '🟡',
        'color': 'info',  # st.info()
        'text': 'KEEP MONITORING'
    },
    'REJECT': {
        'emoji': '🔴',
        'color': 'error',  # st.error()
        'text': 'DO NOT APPROVE'
    }
}

# 사용 예시
badge = RECOMMENDATION_BADGES[recommendation]
st.markdown(f"{badge['emoji']} **`{badge['text']}`**")
```

## 상태 (Status)
```python
STATUS_COLORS = {
    'analyzing': '🔵',  # 분석 중
    'watching': '🟡',   # 관찰 중
    'qualified': '🟢',  # 승인 대기
    'approved': '✅',   # 승인됨
    'rejected': '🔴',   # 거부됨
    'trading': '💰',    # 거래 중
    'completed': '✔️'   # 완료
}
```

## AI Score 구간
```python
def get_score_color(score):
    if score >= 80:
        return 'success'  # 녹색
    elif score >= 60:
        return 'warning'  # 노란색
    else:
        return 'error'    # 빨간색

# 사용 예시
if score >= 80:
    st.success(f"Score: {score}")
elif score >= 60:
    st.warning(f"Score: {score}")
else:
    st.error(f"Score: {score}")
```

## P&L (손익)
```python
def render_pnl(pnl, pnl_pct):
    if pnl >= 0:
        st.markdown(f"**:green[+₩{pnl:,} (+{pnl_pct:.2f}%)]**")
    else:
        st.markdown(f"**:red[-₩{abs(pnl):,} ({pnl_pct:.2f}%)]**")
```

## 우선순위 (Priority)
```python
def render_action_item(item):
    if item['priority'] == 'High':
        st.warning(f"{item['icon']} **{item['title']}** `High Priority`")
    else:
        st.info(f"{item['icon']} **{item['title']}**")
```

---

# 🚧 V0 vs Streamlit 차이점

## 1. Workflow Progress (파이프라인)

**V0**: SVG 선으로 연결된 5단계 진행 바
```
Filter ━━━━ Pool ━━━━ AI ········ Approval ········ Trading
  ✓         ✓         ⏳           ○            ○
```

**Streamlit 대안**: 5-column으로 단순화
```python
cols = st.columns(5)
for idx, step in enumerate(steps):
    with cols[idx]:
        st.markdown(f"### {step['icon']}")
        st.markdown(f"**{step['name']}**")
        st.caption(step['count'])
```

**차이**: 연결선 없음, 단계별 독립적 표시

---

## 2. Status Badge

**V0**: 커스텀 배지 (rounded corners, background color, padding)
```css
.badge-qualified {
  background: #65A150;
  color: white;
  padding: 2px 8px;
  border-radius: 4px;
}
```

**Streamlit 대안**: 이모지 + 백틱
```python
status_map = {
    'qualified': '🟢 `qualified`',
    'rejected': '🔴 `rejected`',
}
st.markdown(status_map[status])
```

**차이**: 패딩/배경색 세밀한 조정 불가, 이모지로 보완

---

## 3. Master-Detail 선택 하이라이트

**V0**: 선택된 아이템에 파란 테두리 (border: 2px solid #5560C7)

**Streamlit 대안**: `st.info()` 메시지 추가
```python
if is_selected:
    st.info("📌 Selected", icon="📌")
```

**차이**: 테두리 대신 추가 위젯으로 표시

---

## 4. Inline Actions (테이블 내 버튼)

**V0**: 각 row에 "Add" / "Close" 버튼

**Streamlit 대안**: `st.data_editor()` 사용 또는 별도 액션 영역
```python
# 방법 1: st.data_editor (Streamlit 1.29+)
edited_df = st.data_editor(
    df,
    column_config={
        'actions': st.column_config.ButtonColumn('Actions')
    }
)

# 방법 2: 테이블 하단에 액션 버튼
st.dataframe(df)
col1, col2 = st.columns(2)
with col1:
    st.button("Add to Position")
with col2:
    st.button("Close Position")
```

**차이**: 인라인 버튼 제한적, 테이블 외부 배치 필요

---

## 5. Toggle Button (Buy/Sell)

**V0**: 세그먼트 컨트롤 (하나만 선택 가능한 토글)

**Streamlit 대안**: `st.radio()` 또는 2개 버튼
```python
# 방법 1: st.radio (horizontal)
order_side = st.radio("", ["Buy", "Sell"], horizontal=True)

# 방법 2: 2 버튼 + session_state
col1, col2 = st.columns(2)
with col1:
    if st.button("🟢 Buy", use_container_width=True):
        st.session_state.order_side = 'buy'
with col2:
    if st.button("🔴 Sell", use_container_width=True):
        st.session_state.order_side = 'sell'
```

**차이**: 시각적으로 V0와 약간 다름, 기능은 동일

---

## 6. Dark Theme

**V0**: 완전한 커스텀 다크 테마 (블랙 배경 + 고대비)

**Streamlit**: `.streamlit/config.toml` 설정
```toml
[theme]
primaryColor = "#5560C7"
backgroundColor = "#0E1117"
secondaryBackgroundColor = "#262730"
textColor = "#FAFAFA"
font = "sans serif"
```

**차이**: Streamlit의 기본 다크 테마 사용, 세밀한 조정 제한적

---

## 7. Progress Bar (Status Distribution)

**V0**: 커스텀 가로 막대 (높이, 색상, 라벨 위치 조정)

**Streamlit**: `st.progress()` 사용
```python
st.markdown("Approved")
st.progress(0.40)  # 40%
st.caption("40%")
```

**차이**: 높이/두께 조정 불가, Streamlit 기본 스타일 사용

---

## 8. Sortable Table

**V0**: 모든 컬럼 클릭으로 정렬 가능

**Streamlit**: `st.dataframe()`은 기본 정렬 지원
```python
st.dataframe(df)  # 컬럼 헤더 클릭 → 자동 정렬
```

**차이**: 기능은 동일, UI 스타일만 다름

---

# ✅ 테스트 방법

## 개별 페이지 테스트
```bash
# Dashboard
streamlit run skeletons/dashboard_skeleton.py

# AI Reports
streamlit run skeletons/ai_reports_skeleton.py

# Stock Pool
streamlit run skeletons/stock_pool_skeleton.py

# Trading
streamlit run skeletons/trading_skeleton.py

# Approval Queue
streamlit run skeletons/approval_queue_skeleton.py

# Active Trades
streamlit run skeletons/active_trades_skeleton.py
```

## 체크리스트

### Dashboard
- [ ] KPI 4개가 동일 비중으로 배치됨
- [ ] Workflow Progress 5단계가 명확히 구분됨
- [ ] Action Needed와 Status Distribution이 2:1 비율

### AI Reports
- [ ] Master(30%) - Detail(70%) 비율 유지
- [ ] 리스트 클릭 시 선택 상태 변경
- [ ] 선택된 항목에 "📌 Selected" 표시
- [ ] 4개 탭(Summary/Momentum/Liquidity/Risk) 작동
- [ ] 액션 버튼 3개 하단 배치

### Stock Pool
- [ ] 검색 + 2 필터가 3:1:1 비율
- [ ] 테이블이 화면의 80% 차지
- [ ] Status 배지가 이모지로 구분
- [ ] 컬럼 정렬 가능

### Active Trades
- [ ] Portfolio KPI 4개 상단 배치
- [ ] P&L이 녹색(+) / 빨강(-) 구분
- [ ] 테이블이 정보 밀도 높게 표시

---

# 🎯 최종 목표

**"이 화면이 V0 디자인을 기반으로 한 StockGravity Streamlit UI라는 것이 바로 느껴지는 결과물"**

## 달성 기준
1. ✅ 레이아웃 구조가 V0와 90% 일치
2. ✅ 정보 우선순위가 명확히 유지됨
3. ✅ Master-Detail 패턴이 자연스러움
4. ✅ 트레이딩 툴다운 정보 밀도
5. ✅ 색상/배지 규칙이 일관성 있게 적용됨
6. ✅ Streamlit 네이티브 컴포넌트만 사용

## 실제 적용 순서
1. 스켈레톤 파일 테스트
2. Mock 데이터를 실제 DB 쿼리로 교체
3. 색상/배지 규칙 적용
4. 실제 사용자 피드백으로 미세 조정
