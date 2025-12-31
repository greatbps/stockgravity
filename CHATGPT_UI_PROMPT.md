# StockGravity UI 디자인 요청

## 프로젝트 개요

**StockGravity**는 한국 주식시장에서 유망 종목을 자동으로 필터링하고 모니터링하는 시스템입니다.

### 주요 기능
1. **자동 필터링**: 매일 15:20에 2,790개 종목 중 500개 선별
2. **실시간 데이터 수집**: 선별된 종목의 실시간 시세 수집
3. **AI 분석**: Google Gemini를 활용한 종목 분석
4. **DB 저장**: PostgreSQL에 데이터 저장 및 모니터링
5. **Kiwoom Trading 연동**: 승인된 종목을 실제 트레이딩 시스템에 연동

---

## 데이터베이스 구조

### 1. stock_pool (필터링된 종목 풀)
```sql
- ticker VARCHAR(6)           -- 종목코드
- name VARCHAR(100)            -- 종목명
- close NUMERIC(10,2)          -- 종가
- trading_value BIGINT         -- 거래대금
- change_5d NUMERIC(5,2)       -- 5일 변화율
- vol_ratio NUMERIC(5,2)       -- 거래량 비율
- final_score NUMERIC(5,2)     -- 최종 점수
- status VARCHAR(20)           -- 상태: monitoring/approved/rejected/trading/completed
- added_date TIMESTAMP         -- 추가일
- approved_date TIMESTAMP      -- 승인일
- monitored_days INTEGER       -- 모니터링 일수
- realtime_price NUMERIC(10,2) -- 실시간 가격
- realtime_volume BIGINT       -- 실시간 거래량
- realtime_updated_at TIMESTAMP -- 실시간 업데이트 시각
- entry_price NUMERIC(10,2)    -- 진입가
- exit_price NUMERIC(10,2)     -- 청산가
- profit_rate NUMERIC(5,2)     -- 수익률
- notes TEXT                   -- 메모
```

### 2. stock_monitoring_history (일별 모니터링 히스토리)
```sql
- ticker VARCHAR(6)
- date DATE
- open, high, low, close NUMERIC(10,2)
- volume BIGINT
- price_change NUMERIC(5,2)
- volume_change NUMERIC(5,2)
- ma5, ma20 NUMERIC(10,2)
- rsi NUMERIC(5,2)
```

### 3. ai_analysis_reports (AI 분석 리포트)
```sql
- ticker VARCHAR(6)
- report_date DATE
- summary TEXT                 -- 분석 요약
- recommendation VARCHAR(20)   -- BUY/HOLD/SELL
- confidence_score NUMERIC(3,2) -- 신뢰도 점수
- momentum_analysis TEXT       -- 모멘텀 분석
- liquidity_analysis TEXT      -- 유동성 분석
- risk_factors TEXT            -- 리스크 요인
```

### 뷰
- `v_monitoring_stocks`: 모니터링 중인 종목 (status='monitoring')
- `v_approved_stocks`: 승인된 종목 (status='approved')

---

## 현재 기술 스택

- **프론트엔드**: Streamlit (Python 웹 프레임워크)
- **백엔드**: Python 3.x
- **데이터베이스**: PostgreSQL 16
- **데이터 수집**: Kiwoom API
- **AI**: Google Gemini 2.5 Flash
- **스케줄링**: Cron (평일 15:20 자동 실행)

---

## UI 디자인 요구사항

### 필수 화면 구성

#### 1. 대시보드 (홈)
- **자동 업데이트 상태 표시**
  - 마지막 업데이트 시간
  - 다음 업데이트 예정 시간 (평일 15:20)
  - 현재 진행 중인 작업 (필터링/수집/분석)
  - 진행률 표시 (프로그레스 바)

- **주요 지표 카드**
  - 전체 모니터링 종목 수
  - 승인된 종목 수
  - 거래 중 종목 수
  - 오늘 완료된 종목 수

- **최근 필터링 결과 요약**
  - Top 10 종목 (점수순)
  - 종목명, 종가, 거래대금, 5일 변화율, 최종점수

#### 2. 종목 풀 관리 (stock_pool)
- **필터 옵션**
  - 상태별 (monitoring/approved/rejected/trading/completed)
  - 점수 범위 (슬라이더)
  - 거래대금 범위
  - 종가 범위
  - 추가일 기간 선택

- **테이블 표시**
  - 정렬 가능한 컬럼 (점수, 거래대금, 변화율 등)
  - 페이지네이션
  - 실시간 가격 업데이트 표시 (색상 변화)
  - 각 종목별 액션 버튼:
    * 상세보기
    * 승인/거부
    * 메모 추가

- **종목 상세 모달/페이지**
  - 기본 정보 (종목명, 코드, 현재가, 거래대금)
  - 필터링 메트릭 (점수, 변화율, 거래량 비율)
  - 모니터링 기간 및 일수
  - 차트 (가격 추이, 거래량 추이)
  - AI 분석 결과 (있는 경우)
  - 메모 입력/수정 기능
  - 상태 변경 버튼

#### 3. 모니터링 히스토리 (stock_monitoring_history)
- **종목 선택**
  - 드롭다운 또는 검색으로 종목 선택

- **차트 표시**
  - 캔들스틱 차트 (OHLC)
  - 거래량 차트
  - 이동평균선 (MA5, MA20)
  - RSI 지표

- **일별 데이터 테이블**
  - 날짜, OHLCV, 변화율
  - 기술적 지표 값

#### 4. AI 분석 리포트 (ai_analysis_reports)
- **리포트 목록**
  - 날짜별, 종목별 리포트
  - 추천 등급별 필터 (BUY/HOLD/SELL)
  - 신뢰도 점수 표시

- **리포트 상세**
  - 분석 요약 (카드 형태)
  - 추천 등급 (색상으로 구분: BUY=녹색, HOLD=노랑, SELL=빨강)
  - 신뢰도 점수 (프로그레스 바)
  - 모멘텀 분석
  - 유동성 분석
  - 리스크 요인
  - 분석 일시

#### 5. 승인/거래 관리
- **승인 대기 종목**
  - monitoring 상태인 종목 리스트
  - 모니터링 일수 표시
  - 일괄 승인/거부 기능

- **승인된 종목**
  - approved 상태 종목 리스트
  - Kiwoom Trading 연동 상태 표시
  - 진입가 설정

- **거래 중 종목**
  - trading 상태 종목
  - 진입가, 현재가, 수익률 실시간 표시
  - 수익률에 따른 색상 (양수=녹색, 음수=빨강)

- **완료된 거래**
  - completed 상태 종목
  - 진입가, 청산가, 수익률
  - 거래 통계 (승률, 평균 수익률, 총 수익)

#### 6. 설정 및 로그
- **자동 업데이트 설정**
  - 크론 스케줄 확인/수정
  - 필터링 조건 설정 (거래대금, 종가 임계값)
  - AI 분석 대상 종목 수

- **로그 뷰어**
  - 자동 업데이트 실행 로그
  - 에러 로그
  - 날짜별 필터링

---

## UI/UX 요구사항

### 디자인 스타일
- **모던하고 깔끔한 디자인**
- **다크모드 지원** (선택 사항)
- **반응형 레이아웃** (데스크톱 중심, 태블릿 호환)
- **직관적인 네비게이션**

### 색상 스킴 제안
- **Primary**: 파랑/남색 계열 (신뢰감, 전문성)
- **Success**: 녹색 (상승, 수익, 승인)
- **Danger**: 빨강 (하락, 손실, 거부)
- **Warning**: 노랑/주황 (대기, 주의)
- **Info**: 하늘색 (정보, 모니터링)

### 컴포넌트 우선순위
1. **실시간 데이터 표시**: 가격/거래량 업데이트 시 애니메이션
2. **차트**: 인터랙티브한 차트 (확대/축소, 툴팁)
3. **테이블**: 정렬, 필터, 페이지네이션
4. **상태 표시**: 배지, 프로그레스 바, 아이콘
5. **액션 버튼**: 명확한 CTA (Call To Action)

### Streamlit 고려사항
- `st.tabs()`, `st.columns()`, `st.expander()` 활용
- `st.dataframe()` vs `st.data_editor()` 선택
- `st.plotly_chart()` 또는 `st.line_chart()` 사용
- `st.metric()` 카드로 주요 지표 표시
- `st.sidebar` 네비게이션 및 필터
- `st.progress()`, `st.status()` 진행 상태 표시

---

## 워크플로우

### 일반 사용자 시나리오

1. **매일 15:20 자동 실행**
   - 2,790개 종목 필터링 → 500개 선별
   - 실시간 데이터 수집
   - 상위 5개 종목 AI 분석
   - 결과를 DB에 저장

2. **사용자 확인 (15:30~16:00)**
   - 대시보드에서 오늘 필터링 결과 확인
   - Top 종목들의 실시간 가격 모니터링
   - AI 분석 리포트 검토

3. **종목 승인 (16:00~17:00)**
   - monitoring 상태 종목 검토
   - 며칠 지켜본 종목 중 유망한 종목 승인
   - 메모 작성 (승인 이유, 주의사항)

4. **거래 실행 (다음날~)**
   - 승인된 종목이 Kiwoom Trading 시스템에 자동 전달
   - 거래 시작 시 status → 'trading' 변경
   - 실시간 수익률 모니터링

5. **거래 완료**
   - 청산 시 status → 'completed' 변경
   - 수익률 기록
   - 거래 통계 업데이트

---

## 출력 형식 요청

다음 형식으로 UI 디자인을 제공해주세요:

1. **와이어프레임/목업**
   - 각 화면의 레이아웃 스케치
   - 주요 컴포넌트 배치

2. **Streamlit 코드 구조**
   - 각 화면/탭에 대한 코드 스켈레톤
   - 주요 함수 및 컴포넌트 사용법
   - DB 쿼리 예제

3. **디자인 설명**
   - 색상 스킴
   - 폰트 추천
   - 아이콘 사용 가이드

4. **구현 우선순위**
   - Phase 1: 필수 화면 (대시보드, 종목 풀)
   - Phase 2: 고급 기능 (차트, AI 리포트)
   - Phase 3: 부가 기능 (설정, 로그)

---

## 추가 요청사항

- **실용성 중심**: 화려함보다는 정보 전달과 효율성 우선
- **데이터 시각화**: 숫자보다는 차트/그래프로 직관적 표현
- **빠른 액세스**: 자주 쓰는 기능은 2클릭 이내 접근
- **에러 처리**: DB 연결 실패, 데이터 없음 등 예외 상황 UI
- **로딩 상태**: 데이터 로딩 중 스켈레톤/스피너 표시

---

## 참고 정보

### 현재 .env 설정
```ini
GOOGLE_API_KEY=AIzaSyDdNHaQYD_X3vPmi4zafMxySyGClmQqhqk
DB_HOST=localhost
DB_PORT=5432
DB_NAME=stockgravity
DB_USER=postgres
DB_PASSWORD=killer99!!
```

### DB 연결 코드 예시
```python
from db_config import get_db_connection

with get_db_connection() as conn:
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM v_monitoring_stocks")
    stocks = cursor.fetchall()
```

### 현재 필터링 기준
- 거래대금 > 1억원
- 종가 > 5,000원
- 5일 변화율 > -5%
- 거래량 비율 > 0.5

---

이 프롬프트를 바탕으로 StockGravity 프로젝트의 Streamlit 대시보드 UI를 디자인해주세요.
특히 **DB 조회 화면**(종목 풀, 모니터링 히스토리, AI 리포트)에 중점을 두어주시고,
실제 구현 가능한 Streamlit 코드와 함께 제공해주시면 감사하겠습니다.
