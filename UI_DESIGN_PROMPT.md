# StockGravity UI 디자인 리뷰 프롬프트

## 시스템 개요
StockGravity는 한국 주식 시장의 자동 분석 및 투자 지원 시스템입니다. Streamlit 기반 웹 대시보드로 구성되어 있습니다.

---

## 현재 페이지 구조

### 1. 📊 Dashboard (app.py)
**목적**: 전체 시스템 현황 한눈에 보기
**주요 기능**:
- 시스템 상태 요약 (총 종목 수, AI 분석 현황)
- Quick Stats 카드
- 최근 활동 로그

**현재 상태**: 기본 구조만 있음

---

### 2. 📦 Stock Pool (pages/1_📦_Stock_Pool.py)
**목적**: 매일 필터링된 500개 종목 관리
**주요 UI 요소**:

**사이드바 필터**:
- Status 선택: monitoring / approved / rejected / trading / completed
- Final Score 슬라이더: 0~100
- Trading Value 슬라이더: 1~5000억
- Added Date Range: 날짜 범위 선택
- 🔄 Refresh Data 버튼

**메인 영역**:
- 상단 메트릭 (3개 컬럼):
  - 총 종목 수
  - 평균 점수
  - 평균 거래대금
- 페이지네이션 (30개씩)
- **종목 테이블** (클릭 선택 방식):
  - 배지 | 종목코드 | 종목명 | 종가 | 실시간가 | 거래대금(억) | 변화율 | 거래량비 | 점수 | 상태

**선택된 종목 액션 영역** (3 컬럼):
- 왼쪽: 메모 입력창 (text_area)
- 중간: 메트릭 (Final Score, 5D Change, 실시간 변동)
- 오른쪽: 버튼 영역
  - 🔍 상세보기 (stock_detail 페이지로 이동)
  - ✅ Approve (monitoring → approved)
  - ❌ Reject (monitoring/approved → rejected)
  - 💾 Save Memo

**문제점**:
- 페이지 크기가 30개로 고정되어 있어 많은 종목 탐색 불편
- 배지 기능이 있지만 의미가 불명확
- 실시간가 업데이트 로직이 없음

---

### 3. 🤖 AI Reports (pages/2_🤖_AI_Reports.py)
**목적**: Google Gemini AI 기반 종목 분석 리포트 확인 및 승인
**주요 UI 요소**:

**상단 필터** (3 컬럼):
- 추천 등급: ALL / STRONG_APPROVE / WATCH_MORE / DO_NOT_APPROVE
- 리포트 상태: ALL / ACTIVE / TRADED / DROPPED
- (3번째 컬럼 비어있음)

**메인 영역**:
- 총 리포트 수 표시
- **리포트 카드** (Expander 방식):
  - 제목: 🟢/🟡/🔴 종목명 (코드) 🟢/💰/🔴 - 점수 - 추천등급 (신뢰도) - 날짜
  - 내용 (2 컬럼):
    - 왼쪽: 분석 요약
    - 오른쪽: 메트릭 (종합 점수, 추천, 신뢰도, 리포트 상태, 종목 상태, 탈락 사유)
  - 탭: 📈 모멘텀 / 💧 유동성 / ⚠️ 리스크
  - 액션 버튼 (3 컬럼):
    - ✅ Approve (monitoring → approved)
    - ❌ Reject (monitoring/approved → rejected)
    - 🔄 Monitoring 유지

**문제점**:
- Expander 방식이라 한 번에 여러 리포트 비교 어려움
- 리포트가 20개나 되면 스크롤이 너무 길어짐
- 종목 상세 정보 확인이 어려움 (차트 등)

---

### 4. ✅ Trading (pages/3_✅_Trading.py)
**목적**: 승인된 종목 모니터링 및 거래 관리

**탭 구조** (3개):

#### 📋 Approval Queue (Tab 1)
**대상**: status='approved' 종목

**상단 메트릭** (3 컬럼):
- Queue 종목 수
- 재평가 대상 (3일 이상 경과)
- 평균 점수

**종목 테이블** (클릭 선택):
- 종목코드 | 종목명 | 현재가 | 점수 | 거래대금(억) | 보유일

**선택된 종목 상세**:
- 메트릭 (4 컬럼): 종목명, 현재가, 종합 점수, 보유 일수
- 차트 탭 (3개):
  - 📈 가격 차트: 캔들스틱 + MA5 + MA20
  - 📊 거래량: 막대 차트
  - 📉 RSI 신호: RSI 차트 + 과매수/과매도 라인 + 탈락 위험 경고

**액션 버튼** (3 컬럼):
- 💰 매매 시작 (approved → trading)
- 🔄 재평가 실행
- ❌ Queue 제거 (approved → rejected)

#### 💰 Active Trades (Tab 2)
**대상**: status='trading' 종목

**상단 메트릭** (3 컬럼):
- 거래 중 종목 수
- 평균 수익률
- 승률

**거래 현황 테이블**:
- 종목코드 | 종목명 | 진입가 | 현재가 | 수익률(%)

#### 📊 Trade History (Tab 3)
**대상**: status='completed' 종목

**상단 메트릭** (4 컬럼):
- 총 거래 수
- 승률
- 평균 수익률
- 누적 수익률

**거래 이력 테이블**:
- 종목코드 | 종목명 | 진입가 | 청산가 | 수익률(%)

**문제점**:
- Kiwoom API 연동 전이라 실시간 데이터 없음
- Active Trades, Trade History는 현재 비어있음
- 재평가 실행 버튼이 구현 예정 상태

---

### 5. 📌 Stock Detail (pages/stock_detail.py)
**목적**: 개별 종목 상세 정보

**현재 상태**: 구조만 있고 구현 안 됨

---

## 사이드바 공통 요소

**상단**:
- 타이틀: 📊 StockGravity
- 캡션: Korean Stock Filtering & Monitoring System

**Quick Stats** (모든 페이지 공통):
```
📊 Quick Stats
--------------
AI 분석: 총 8개
🟢 8 | 🟡 0 | 🔴 0

거래 현황:
✅ Approved: 12
💰 Trading: 0
✔️ Completed: 0

후보 종목: 488개
--------------
⏰ Auto Update: Weekdays 15:20
🤖 AI Engine: Gemini 2.5 Flash
```

---

## 워크플로우

```
[매일 15:20 자동 실행]
         ↓
1. 필터링 (2,790개 → 500개)
         ↓
2. Stock Pool 저장 (status: monitoring)
         ↓
3. AI 분석 (Top 20)
         ↓
4. AI Reports 생성
         ↓
[사용자 검토]
         ↓
5. AI Reports에서 Approve 클릭
         ↓
6. Trading > Approval Queue로 이동 (status: approved)
         ↓
7. 3~7일간 모니터링 (재평가)
         ↓
8. 매매 시작 클릭
         ↓
9. Active Trades로 이동 (status: trading)
         ↓
10. 거래 완료 후 Trade History (status: completed)
```

---

## 개선이 필요한 부분

### 1. Dashboard 페이지
- **현재**: 거의 비어있음
- **필요**: 전체 시스템 상태를 한눈에 볼 수 있는 대시보드
  - 최근 AI 추천 종목 요약
  - 승인 대기 중인 종목 수
  - 거래 현황 요약
  - 최근 수익률 차트

### 2. AI Reports 페이지
- **문제**: Expander 방식이라 비교가 어려움
- **제안 필요**:
  - 테이블 + 상세보기 분리?
  - 카드 그리드 방식?
  - 탭으로 추천 등급 분리?

### 3. Stock Pool 페이지
- **문제**:
  - 배지 의미 불명확
  - 페이지네이션이 불편
  - 필터가 사이드바에 있어 좁음
- **제안 필요**: 레이아웃 개선

### 4. Trading 페이지
- **문제**:
  - Approval Queue가 너무 기능이 많음
  - 차트를 보려면 종목을 하나씩 선택해야 함
- **제안 필요**:
  - 멀티 차트 비교?
  - 간소화?

### 5. Stock Detail 페이지
- **현재**: 구현 안 됨
- **필요**:
  - 종합 차트 (가격, 거래량, RSI, MACD 등)
  - AI 리포트 히스토리
  - 메모 히스토리
  - 재평가 로그

---

## 질문

1. **Dashboard 페이지**: 어떤 정보를 중심으로 구성하는 게 좋을까요?
   - 옵션 A: 워크플로우 중심 (각 단계별 진행 상황)
   - 옵션 B: 메트릭 중심 (숫자 위주)
   - 옵션 C: 액션 중심 (해야 할 일 위주)

2. **AI Reports 페이지**: 20개 리포트를 어떻게 표시하는 게 좋을까요?
   - 현재: Expander 방식 (한 번에 1개씩 펼쳐서 상세 보기)
   - 대안 A: 테이블 + 우측 상세 패널
   - 대안 B: 그리드 카드 (6개씩 2행)
   - 대안 C: 탭으로 추천등급 분리 후 각각 테이블

3. **Stock Pool vs AI Reports**:
   - Stock Pool: 500개 전체 (필터링 결과)
   - AI Reports: Top 20개 (AI 분석 완료)
   - 이 둘의 역할 구분이 명확한가요? 통합 가능한가요?

4. **Trading > Approval Queue**:
   - 현재 너무 많은 기능 (테이블 + 차트 + 액션)
   - 간소화 필요한가요? 아니면 별도 페이지로 분리?

5. **전체 네비게이션 구조**:
   - 현재: Dashboard / Stock Pool / AI Reports / Trading / Stock Detail
   - 워크플로우 순서: AI Reports → (Approve) → Trading
   - 페이지 순서를 워크플로우에 맞춰 재정렬하는 게 좋을까요?

6. **색상 및 아이콘 시스템**:
   - 추천 등급: 🟢 STRONG_APPROVE / 🟡 WATCH_MORE / 🔴 DO_NOT_APPROVE
   - 리포트 상태: 🟢 ACTIVE / 💰 TRADED / 🔴 DROPPED
   - 종목 상태: 👀 monitoring / ✅ approved / ❌ rejected / 💰 trading / ✔️ completed
   - 일관성 있게 정리 필요한가요?

---

## 개선 제안을 부탁드립니다

위 내용을 바탕으로:
1. 각 페이지의 최적 레이아웃
2. 정보 계층 구조 (중요도에 따른 배치)
3. 사용자 플로우 개선안
4. 색상/아이콘 시스템 정리
5. 반응형 레이아웃 (컬럼 분할 등)

구체적인 개선안을 제시해주세요!
