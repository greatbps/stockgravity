# StockGravity 데이터베이스 설정 완료

## ✅ 설정 완료 사항

### 1. PostgreSQL 데이터베이스
- **데이터베이스명**: stockgravity
- **버전**: PostgreSQL 16.11
- **상태**: 정상 작동

### 2. 생성된 테이블 (3개)

#### stock_pool
필터링된 종목 풀 - 모니터링 및 승인 관리
- 종목 기본 정보 (ticker, name)
- 필터링 메트릭 (close, trading_value, change_5d, vol_ratio, final_score)
- 상태 관리 (status, added_date, approved_date, monitored_days)
- 실시간 데이터 (realtime_price, realtime_volume, realtime_updated_at)
- 성과 추적 (entry_price, exit_price, profit_rate, trade_date)

#### stock_monitoring_history
일별 모니터링 데이터
- OHLCV 데이터 (open, high, low, close, volume)
- 변화 추적 (price_change, volume_change)
- 기술적 지표 (ma5, ma20, rsi)

#### ai_analysis_reports
AI 분석 리포트
- 분석 결과 (summary, recommendation, confidence_score)
- 상세 분석 (momentum_analysis, liquidity_analysis, risk_factors)

### 3. 뷰 (2개)

#### v_monitoring_stocks
모니터링 중인 종목 조회 (status='monitoring')

#### v_approved_stocks
승인된 종목 조회 (status='approved')

### 4. 인덱스
- `idx_stock_pool_status` - 상태별 조회 최적화
- `idx_stock_pool_ticker` - 종목코드 조회 최적화
- `idx_stock_pool_added_date` - 추가일자 조회 최적화
- `idx_stock_pool_score` - 점수 정렬 최적화
- `idx_monitoring_ticker_date` - 모니터링 히스토리 조회 최적화
- `idx_monitoring_date` - 날짜별 조회 최적화
- `idx_ai_reports_ticker_date` - AI 리포트 조회 최적화

### 5. 트리거
- `update_stock_pool_updated_at` - updated_at 자동 갱신

## 📝 연결 정보

환경변수 (.env):
```
DB_HOST=localhost
DB_PORT=5432
DB_NAME=stockgravity
DB_USER=postgres
DB_PASSWORD=killer99!!
```

## 🔧 사용 방법

### Python에서 연결
```python
from db_config import DatabaseConfig, get_db_connection

# 방법 1: 전역 인스턴스 사용
with get_db_connection() as conn:
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM stock_pool LIMIT 10")
    rows = cursor.fetchall()

# 방법 2: 개별 인스턴스 사용
db = DatabaseConfig()
db.init_pool(minconn=1, maxconn=10)
with db.get_connection() as conn:
    cursor = conn.cursor()
    # ... 쿼리 실행
```

### psql에서 연결
```bash
psql -U postgres -h localhost -d stockgravity
```

## ✅ 테스트 결과

모든 테스트 통과:
- ✓ 데이터베이스 연결
- ✓ 테이블 생성 (3개)
- ✓ 뷰 생성 (2개)
- ✓ 데이터 삽입/조회/삭제
- ✓ 인덱스 적용
- ✓ 트리거 작동

테스트 명령:
```bash
source venv/bin/activate
python test_db.py
```

## 📊 다음 단계

1. **데이터 수집 스크립트 DB 연동**
   - quick_filter.py → stock_pool 저장
   - collect_realtime_data.py → realtime 필드 업데이트
   - generate_ai_report.py → ai_analysis_reports 저장

2. **모니터링 히스토리 수집**
   - 일별 데이터를 stock_monitoring_history에 저장
   - monitored_days 자동 증가

3. **대시보드 DB 연동**
   - app.py에서 CSV 대신 DB에서 데이터 조회
   - 뷰(v_monitoring_stocks, v_approved_stocks) 활용

4. **Kiwoom Trading 연동**
   - 승인된 종목(status='approved')을 kiwoom_trading에서 조회
   - 거래 결과를 stock_pool에 업데이트
