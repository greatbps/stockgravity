# 📊 Daily Prices DB 마이그레이션

**일시**: 2025-12-31

## 🎯 변경 이유

### ❌ 기존 방식 (CSV 기반)
```
daily_prices.csv (70MB, 109만 행)
  ├─ 전체 히스토리 재다운로드 (수십분 소요)
  ├─ 매일 실행하면 비효율적
  └─ 스크립트마다 CSV 파일 읽기 (느림)
```

### ✅ 새 방식 (DB 기반)
```
PostgreSQL daily_prices 테이블
  ├─ 최초 1회: CSV → DB 벌크 임포트
  ├─ 매일: 증분 업데이트 (최신 데이터만)
  └─ 빠른 조회 (인덱스 활용)
```

---

## 📋 테이블 구조

### daily_prices
```sql
CREATE TABLE daily_prices (
    id SERIAL PRIMARY KEY,
    ticker VARCHAR(6) NOT NULL,      -- 종목코드
    date DATE NOT NULL,               -- 거래일
    open NUMERIC(12,2),               -- 시가
    high NUMERIC(12,2),               -- 고가
    low NUMERIC(12,2),                -- 저가
    close NUMERIC(12,2),              -- 종가
    volume BIGINT,                    -- 거래량
    diff VARCHAR(20),                 -- 전일비
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE (ticker, date)             -- 중복 방지
);

-- 인덱스
CREATE INDEX idx_daily_prices_ticker ON daily_prices(ticker);
CREATE INDEX idx_daily_prices_date ON daily_prices(date);
CREATE INDEX idx_daily_prices_ticker_date ON daily_prices(ticker, date DESC);
```

**용량**:
- 행: 약 109만개
- 종목: 2,791개
- 기간: 2014-04-28 ~ 2025-12-30

---

## 🚀 사용 방법

### 1. 최초 설정 (1회만)

#### ① 테이블 생성
```bash
python3 -c "
from db_config import get_db_connection
with open('create_daily_prices_table.sql') as f:
    sql = f.read()
with get_db_connection() as conn:
    conn.cursor().execute(sql)
print('✅ 테이블 생성 완료')
"
```

#### ② CSV → DB 벌크 임포트
```bash
python3 import_daily_prices_to_db.py

# 또는 배치 크기 조정
python3 import_daily_prices_to_db.py --batch 50000
```

**예상 시간**: 5~10분 (109만 행)

---

### 2. 일일 운영

#### 매일 증분 업데이트
```bash
# 모든 종목의 최신 데이터 업데이트
python3 update_daily_prices.py

# 또는 일부 종목만 테스트
python3 update_daily_prices.py --limit 100
```

**동작**:
1. DB에서 최신 거래일 조회
2. 각 종목의 최신 1일 데이터만 크롤링
3. 신규 데이터면 INSERT, 기존이면 UPDATE

**소요 시간**:
- 2,791개 전체: 약 5~10분
- 100개: 약 1분

---

## 📝 스크립트 수정 가이드

### 기존 코드 (CSV 읽기)
```python
# ❌ 기존
prices_df = pd.read_csv('daily_prices.csv')
prices_df['ticker'] = prices_df['ticker'].astype(str).str.zfill(6)
```

### 새 코드 (DB 읽기)
```python
# ✅ 새로운 방식
from db_config import get_db_connection

with get_db_connection() as conn:
    prices_df = pd.read_sql("""
        SELECT ticker, date, open, high, low, close, volume
        FROM daily_prices
        WHERE date >= '2025-01-01'  -- 필요한 기간만
        ORDER BY ticker, date
    """, conn)
```

**장점**:
- 필요한 데이터만 조회 (WHERE 절)
- 메모리 효율적
- 빠른 속도 (인덱스 활용)

---

## 🔧 수정 필요한 파일

### 1. `quick_filter.py`
```python
# 현재
PRICE_FILE = "daily_prices.csv"
df = pd.read_csv(PRICE_FILE)

# 변경 →
from db_config import get_db_connection
with get_db_connection() as conn:
    df = pd.read_sql("""
        SELECT * FROM daily_prices
        WHERE date >= CURRENT_DATE - INTERVAL '60 days'
    """, conn)
```

### 2. `populate_monitoring_history.py`
```python
# 현재
prices_df = pd.read_csv('daily_prices.csv')

# 변경 →
with get_db_connection() as conn:
    prices_df = pd.read_sql("""
        SELECT * FROM daily_prices
        WHERE ticker IN (SELECT ticker FROM stock_pool WHERE status='monitoring')
    """, conn)
```

### 3. `analysis2.py`
```python
# 동일하게 변경
```

---

## ⏰ Cron 자동화 예시

```bash
# crontab -e

# 매일 평일 15:30 - 증분 업데이트 (장 마감 후)
30 15 * * 1-5 cd /home/greatbps/projects/stockgravity && source venv/bin/activate && python3 update_daily_prices.py

# 매일 평일 15:40 - 종목 필터링
40 15 * * 1-5 cd /home/greatbps/projects/stockgravity && source venv/bin/activate && python3 run_pipeline_to_db.py

# 매일 평일 15:50 - RSI 계산
50 15 * * 1-5 cd /home/greatbps/projects/stockgravity && source venv/bin/activate && python3 populate_monitoring_history.py

# 매일 평일 16:00 - AI 분석 (상위 10개)
0 16 * * 1-5 cd /home/greatbps/projects/stockgravity && source venv/bin/activate && python3 generate_ai_report.py --top 10
```

---

## 📊 성능 비교

| 작업 | CSV 방식 | DB 방식 |
|------|---------|---------|
| 전체 데이터 로드 | ~5초 (70MB) | ~2초 (인덱스) |
| 최근 60일만 | ~5초 (전체 읽고 필터) | ~0.5초 (WHERE) |
| 특정 종목 조회 | ~5초 | ~0.1초 |
| 일일 업데이트 | 전체 재다운 (30분+) | 증분만 (5분) |
| 메모리 사용량 | 200MB+ | 10MB~ |

---

## ✅ 장점

1. **빠른 조회**: 인덱스 활용, 필요한 데이터만
2. **효율적 업데이트**: 증분 업데이트 (최신 데이터만)
3. **메모리 절약**: 전체 CSV 로드 불필요
4. **확장성**: 다른 테이블과 JOIN 가능
5. **안정성**: 트랜잭션, 중복 방지

---

## 📌 마이그레이션 체크리스트

- [x] daily_prices 테이블 생성
- [x] CSV → DB 벌크 임포트 스크립트 작성
- [x] 증분 업데이트 스크립트 작성
- [ ] quick_filter.py DB 읽기로 수정
- [ ] populate_monitoring_history.py DB 읽기로 수정
- [ ] analysis2.py DB 읽기로 수정
- [ ] cron 스케줄 설정
- [ ] 기존 CSV 파일 백업 후 제거

---

## 🔄 롤백 방법

문제 발생 시 기존 CSV 방식으로 복귀:

```bash
# daily_prices 테이블 삭제
python3 -c "
from db_config import get_db_connection
with get_db_connection() as conn:
    conn.cursor().execute('DROP TABLE IF EXISTS daily_prices')
print('✅ 테이블 삭제 완료')
"

# 기존 CSV 파일 복원
# (백업해둔 파일 사용)
```

---

**완료 후 확인**:
```bash
python3 -c "
from db_config import get_db_connection
with get_db_connection() as conn:
    cur = conn.cursor()
    cur.execute('SELECT COUNT(*), MIN(date), MAX(date) FROM daily_prices')
    row = cur.fetchone()
    print(f'총 {row[0]:,}행, {row[1]} ~ {row[2]}')
"
```
