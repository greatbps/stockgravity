# ✅ 실제 데이터 파이프라인 완료 (RSI + AI)

**완료 시각**: 2025-12-31 17:30

---

## 📊 데이터 현황

### 1. Stock Pool (필터링 완료)
- **총 종목**: 500개
- **상태**: 모두 'monitoring'
- **점수 범위**: 1.2 ~ 46.3점
- **데이터 소스**: daily_prices.csv (실제 가격 데이터)

### 2. RSI 데이터 (모니터링 히스토리)
- **종목 수**: 100개 (상위 점수순)
- **총 데이터**: 4,041개 데이터 포인트
- **기간**: 2025-11-03 ~ 2025-12-30 (최근 60일)
- **포함 지표**:
  - RSI (14-period)
  - MA5, MA20
  - price_change, volume_change
  - OHLCV

### 3. AI 분석 리포트
- **분석 종목**: 5개 (최상위)
- **AI 모델**: Google Gemini 2.5 Flash
- **분석 내용**:
  - 요약 의견 (summary)
  - 추천 등급 (STRONG_APPROVE/WATCH_MORE/DO_NOT_APPROVE)
  - 신뢰도 점수 (confidence_score)
  - 모멘텀/유동성/리스크 분석

---

## 🏆 AI 분석 완료 종목 (Top 5)

| 종목코드 | 종목명 | Final Score | AI 추천 | 배지 총점 | 배지 |
|---------|--------|-------------|---------|-----------|------|
| 053700 | 삼보모터스 | 46.3 | WATCH_MORE | 48.3 | 🟢 STRONG_APPROVE |
| 080220 | 제주반도체 | 46.2 | STRONG_APPROVE | 49.2 | 🟢 STRONG_APPROVE |
| 000660 | SK하이닉스 | 46.1 | STRONG_APPROVE | 49.1 | 🟢 STRONG_APPROVE |
| 005930 | 삼성전자 | 41.5 | STRONG_APPROVE | 44.5 | 🟢 STRONG_APPROVE |
| 489500 | 엘케이켐 | 37.9 | WATCH_MORE | 39.9 | 🟡 WATCH_MORE |

### 배지 점수 구성
- **Final Score**: 필터링 점수 (거래대금 40% + 모멘텀 30% + 거래량 30%)
- **Momentum**: +1 (5일 등락률 > 5%)
- **RSI**: +1 (RSI 40~60 적정 범위)
- **AI**: +2 (STRONG_APPROVE) / +1 (WATCH_MORE) / +0 (DO_NOT_APPROVE)

### 배지 판정 기준
- **🟢 STRONG_APPROVE**: 총점 >= 40
- **🟡 WATCH_MORE**: 총점 >= 10
- **🔴 DO_NOT_APPROVE**: 총점 < 10

---

## 🔧 수정된 파일

### 1. `generate_ai_report.py` (수정)
**변경 내용**:
- AI 분석 결과를 DB에 자동 저장 추가
- `parse_ai_response()`: AI 응답 파싱
- `save_to_database()`: DB 저장 함수

**사용법**:
```bash
python3 generate_ai_report.py --top 5
```

### 2. `populate_monitoring_history.py` (신규)
**기능**:
- daily_prices.csv에서 실제 가격 데이터 로드
- RSI, MA5, MA20 계산
- stock_monitoring_history 테이블에 저장

**사용법**:
```bash
python3 populate_monitoring_history.py
```

### 3. `import_ai_report.py` (신규)
**기능**:
- 기존 markdown AI 리포트를 DB로 임포트
- 구조화된 데이터 추출 및 저장

**사용법**:
```bash
python3 import_ai_report.py
```

### 4. 데이터베이스 스키마 수정
```sql
-- stock_monitoring_history 테이블
ALTER TABLE stock_monitoring_history
ALTER COLUMN price_change TYPE NUMERIC(10,2),
ALTER COLUMN volume_change TYPE NUMERIC(10,2);

-- ai_analysis_reports 테이블
ALTER TABLE ai_analysis_reports
ALTER COLUMN confidence_score TYPE NUMERIC(5,2);
```

**이유**:
- price_change: 대형주 일일 변동률이 66% 등 큰 값 저장 필요
- confidence_score: 0~100 범위 지원 필요

---

## 📍 대시보드 확인

### 접속 URL
- **로컬**: http://localhost:8000
- **외부**: http://192.168.123.100:8000

### 확인 사항

1. **Stock Pool 페이지** (📦 stock_pool)
   - 500개 종목 리스트
   - 상위 5개 종목에 배지 표시
   - 🟢 (4개), 🟡 (1개) 확인

2. **종목 상세 페이지**
   - 053700, 080220, 000660, 005930, 489500 선택
   - RSI 차트 (60일 데이터)
   - AI 분석 리포트
   - 배지 점수 상세 내역

3. **모니터링 페이지** (📈 monitoring)
   - 100개 종목의 RSI 트렌드
   - MA5/MA20 크로스오버
   - 거래량 변화

---

## 🎯 배지 점수 예시

### 삼보모터스 (053700)
```
배지 총점: 48.3점
├─ Final Score: 46.3
├─ Momentum: +1 (5일 등락률 > 5%)
├─ RSI: +0 (현재 RSI 93.9, 과열 구간)
└─ AI: +1 (WATCH_MORE)
→ 🟢 STRONG_APPROVE
```

### SK하이닉스 (000660)
```
배지 총점: 49.1점
├─ Final Score: 46.1
├─ Momentum: +1
├─ RSI: +0 (현재 RSI 69.4, 약간 과열)
└─ AI: +2 (STRONG_APPROVE)
→ 🟢 STRONG_APPROVE
```

### 엘케이켐 (489500)
```
배지 총점: 39.9점
├─ Final Score: 37.9
├─ Momentum: +1
├─ RSI: +0 (현재 RSI 79.8, 과열)
└─ AI: +1 (WATCH_MORE)
→ 🟡 WATCH_MORE
```

---

## 📈 RSI 분석

### 현재 RSI 상태 (Top 5)
| 종목 | RSI | 상태 |
|------|-----|------|
| 삼보모터스 | 93.9 | 극심한 과열 |
| 제주반도체 | 82.7 | 과열 |
| 엘케이켐 | 79.8 | 과열 |
| 삼성전자 | 71.4 | 약간 과열 |
| SK하이닉스 | 69.4 | 약간 과열 |

**해석**:
- 모든 종목이 RSI 60 이상 (과열)
- 강한 상승 모멘텀이 반영된 상태
- RSI 보너스 점수는 40~60 범위에서만 부여
- 과열 구간 종목은 단기 조정 가능성 주의

---

## 🚀 다음 단계

### 1. 배지 점수 기준 조정 (선택)
현재 RSI가 모두 과열 구간이라 RSI 보너스 +1을 받는 종목이 없음.

**옵션**:
- RSI 범위 조정 (예: 50~70)
- RSI 가중치 변경
- 또는 현재 상태 유지 (과열 종목 필터링 역할)

### 2. 나머지 종목 AI 분석
```bash
# 6~20위 종목 추가 분석
python3 generate_ai_report.py --top 20
```

**주의**: API 할당량 고려 (하루 50회 제한 확인)

### 3. 정기 업데이트 스케줄링
```bash
# crontab 예시 (평일 15:30)
30 15 * * 1-5 cd /home/greatbps/projects/stockgravity && source venv/bin/activate && python run_pipeline_to_db.py
35 15 * * 1-5 cd /home/greatbps/projects/stockgravity && source venv/bin/activate && python populate_monitoring_history.py
40 15 * * 1-5 cd /home/greatbps/projects/stockgravity && source venv/bin/activate && python generate_ai_report.py --top 10
```

---

## ✅ 완료된 작업

1. ✅ 필터링 파이프라인 (2,790 → 500개)
2. ✅ RSI 데이터 생성 (100개 종목 × 60일)
3. ✅ AI 분석 리포트 (Top 5)
4. ✅ DB 스키마 수정 (precision 문제 해결)
5. ✅ 배지 점수 계산 검증
6. ✅ 대시보드 정상 작동 확인

---

## 📊 데이터베이스 통계

### stock_pool
```sql
SELECT COUNT(*), MIN(final_score), AVG(final_score), MAX(final_score)
FROM stock_pool WHERE status='monitoring';
-- 500개 | 1.2 | 5.0 | 46.3
```

### stock_monitoring_history
```sql
SELECT COUNT(DISTINCT ticker), COUNT(*), MIN(date), MAX(date)
FROM stock_monitoring_history;
-- 100개 | 4,041 | 2025-11-03 | 2025-12-30
```

### ai_analysis_reports
```sql
SELECT COUNT(DISTINCT ticker),
       COUNT(*) FILTER (WHERE recommendation='STRONG_APPROVE') as strong,
       COUNT(*) FILTER (WHERE recommendation='WATCH_MORE') as watch
FROM ai_analysis_reports;
-- 5개 | 3 STRONG | 2 WATCH
```

---

**완료**: 실제 데이터로 전체 파이프라인 구축 완료
**상태**: ✅ 정상 작동
**대시보드**: http://localhost:8000
