# 시장 휴장일 정보

## 📅 휴장일 데이터 출처

### 한국거래소 (KRX) 공식 휴장일

휴장일 정보는 **한국거래소(KRX) 공식 웹사이트**에서 제공하는 공휴일 및 증시 휴장일을 기준으로 합니다.

- 공식 사이트: https://www.krx.co.kr
- 영업일정 페이지: https://www.krx.co.kr/contents/OPN/01/01010101/OPN01010101.jsp

### 2026년 한국 증시 휴장일 (16일)

| 날짜 | 휴장일 명칭 | 유형 |
|------|------------|------|
| 2026-01-01 | 신정 | 법정공휴일 |
| 2026-02-16 | 설날 연휴 (전날) | 법정공휴일 |
| 2026-02-17 | 설날 | 법정공휴일 |
| 2026-02-18 | 설날 연휴 (다음날) | 법정공휴일 |
| 2026-03-01 | 삼일절 | 법정공휴일 |
| 2026-04-05 | 식목일 | 법정공휴일 |
| 2026-05-05 | 어린이날 | 법정공휴일 |
| 2026-05-19 | 석가탄신일 | 법정공휴일 |
| 2026-06-06 | 현충일 | 법정공휴일 |
| 2026-08-15 | 광복절 | 법정공휴일 |
| 2026-09-24 | 추석 연휴 (전날) | 법정공휴일 |
| 2026-09-25 | 추석 | 법정공휴일 |
| 2026-09-26 | 추석 연휴 (다음날) | 법정공휴일 |
| 2026-10-03 | 개천절 | 법정공휴일 |
| 2026-10-09 | 한글날 | 법정공휴일 |
| 2026-12-25 | 성탄절 | 법정공휴일 |

**주말(토요일, 일요일)은 별도로 저장하지 않고 코드에서 자동 체크합니다.**

---

## 🗄️ 데이터베이스 구조

### market_holidays 테이블

```sql
CREATE TABLE market_holidays (
    id SERIAL PRIMARY KEY,
    holiday_date DATE NOT NULL UNIQUE,      -- 휴장일
    holiday_name VARCHAR(100) NOT NULL,     -- 휴장일 명칭
    holiday_type VARCHAR(20) DEFAULT 'regular',  -- regular/temporary/weekend
    description TEXT,                        -- 상세 설명
    created_at TIMESTAMP DEFAULT NOW()
);
```

### 데이터 삽입 위치

- **StockGravity DB:** `stockgravity` 데이터베이스
- **Kiwoom Trading DB:** `trading_system` 데이터베이스

두 프로젝트가 서로 다른 데이터베이스를 사용하므로 각각 테이블을 생성해야 합니다.

---

## 🔄 휴장일 업데이트 방법

### 1. 연도별 휴장일 추가

매년 말 KRX에서 다음 연도 영업일정을 발표하면 SQL 파일을 업데이트합니다.

```sql
-- 2027년 휴장일 추가 예시
INSERT INTO market_holidays (holiday_date, holiday_name, holiday_type, description) VALUES
('2027-01-01', '신정', 'regular', '새해 첫날'),
('2027-02-06', '설날 연휴', 'regular', '설날 전날'),
('2027-02-07', '설날', 'regular', '설날 당일'),
('2027-02-08', '설날 연휴', 'regular', '설날 다음날'),
-- ... 계속
ON CONFLICT (holiday_date) DO NOTHING;
```

### 2. 임시 휴장일 추가

국가 애도일, 특별 휴장일 등이 있을 경우:

```sql
INSERT INTO market_holidays (holiday_date, holiday_name, holiday_type, description) VALUES
('2026-03-15', '임시 공휴일', 'temporary', '특별 지정 공휴일')
ON CONFLICT (holiday_date) DO NOTHING;
```

### 3. 스크립트로 추가

```python
from market_utils import get_db_connection

conn = get_db_connection()
try:
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO market_holidays (holiday_date, holiday_name, holiday_type)
        VALUES (%s, %s, %s)
        ON CONFLICT (holiday_date) DO NOTHING
    """, ('2026-03-15', '임시 공휴일', 'temporary'))
    conn.commit()
    print("휴장일 추가 완료")
finally:
    conn.close()
```

---

## ⚙️ 자동화 방안

### KRX API 활용 (향후 계획)

한국거래소에서 API를 제공한다면 자동으로 휴장일을 가져올 수 있습니다.

```python
# 예시 코드 (KRX API 가상)
import requests

def update_holidays_from_krx(year):
    """KRX API에서 휴장일 정보 가져와서 DB 업데이트"""
    url = f"https://api.krx.co.kr/holidays/{year}"
    response = requests.get(url)
    holidays = response.json()

    conn = get_db_connection()
    try:
        cur = conn.cursor()
        for holiday in holidays:
            cur.execute("""
                INSERT INTO market_holidays (holiday_date, holiday_name, holiday_type)
                VALUES (%s, %s, %s)
                ON CONFLICT (holiday_date) DO NOTHING
            """, (holiday['date'], holiday['name'], 'regular'))
        conn.commit()
    finally:
        conn.close()
```

---

## 📋 주의사항

### 1. 대체공휴일

한국 증시는 **대체공휴일 제도**를 적용합니다.
- 공휴일이 토요일/일요일과 겹치면 다음 평일이 대체 휴무

**예시:**
- 2026년 어린이날(5/5)이 화요일이면 그대로 휴장
- 만약 토요일이면 다음 월요일이 대체휴무

### 2. 임시 공휴일

정부가 특별히 지정하는 임시 공휴일이 있을 수 있습니다.
- 선거일
- 국가 애도기간
- 기타 특별 지정일

### 3. 글로벌 시장 연동

한국 증시만 휴장이고 미국/중국 시장은 거래하는 경우가 있으므로 주의하세요.

---

## 🔍 휴장일 확인 방법

### 커맨드라인에서 확인

```bash
# 오늘 거래일 확인
python3 market_utils.py

# 특정 날짜 확인
python3 -c "
from market_utils import is_trading_day
from datetime import date

is_trading, reason = is_trading_day(date(2026, 1, 1))
print(f'2026-01-01: {\"거래일\" if is_trading else reason}')
"
```

### Python 코드에서 확인

```python
from market_utils import is_trading_day, get_next_trading_day

# 오늘 확인
is_trading, reason = is_trading_day()
if not is_trading:
    print(f"오늘은 {reason}입니다")
    next_day = get_next_trading_day()
    print(f"다음 거래일: {next_day}")
```

---

## 📚 참고 자료

- 한국거래소(KRX): https://www.krx.co.kr
- 대한민국 법정공휴일: https://www.law.go.kr
- 관공서의 공휴일에 관한 규정: 대통령령
