-- StockGravity PostgreSQL 스키마
-- 필터링된 종목 관리 및 모니터링

-- 데이터베이스 생성 (필요시)
-- CREATE DATABASE stockgravity;

-- 확장 기능
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. 필터링된 종목 풀 테이블
CREATE TABLE IF NOT EXISTS stock_pool (
    id SERIAL PRIMARY KEY,
    ticker VARCHAR(6) NOT NULL,
    name VARCHAR(100),

    -- 필터링 메트릭
    close NUMERIC(10,2),
    trading_value BIGINT,
    change_5d NUMERIC(5,2),
    vol_ratio NUMERIC(5,2),
    final_score NUMERIC(5,2),

    -- 상태 관리
    status VARCHAR(20) DEFAULT 'monitoring',
    -- 상태: 'monitoring', 'approved', 'rejected', 'trading', 'completed'
    added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    approved_date TIMESTAMP,
    rejected_date TIMESTAMP,
    monitored_days INTEGER DEFAULT 0,

    -- 실시간 데이터 (수집 시)
    realtime_price NUMERIC(10,2),
    realtime_volume BIGINT,
    realtime_updated_at TIMESTAMP,

    -- 성과 추적
    entry_price NUMERIC(10,2),
    exit_price NUMERIC(10,2),
    profit_rate NUMERIC(5,2),
    trade_date DATE,

    -- 메모
    notes TEXT,

    -- 타임스탬프
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- UNIQUE constraint will be added via index
    CONSTRAINT unique_ticker UNIQUE(ticker, added_date)
);

-- 2. 일별 모니터링 히스토리
CREATE TABLE IF NOT EXISTS stock_monitoring_history (
    id SERIAL PRIMARY KEY,
    ticker VARCHAR(6) NOT NULL,
    date DATE NOT NULL,

    -- OHLCV 데이터
    open NUMERIC(10,2),
    high NUMERIC(10,2),
    low NUMERIC(10,2),
    close NUMERIC(10,2),
    volume BIGINT,

    -- 변화 추적
    price_change NUMERIC(5,2),
    volume_change NUMERIC(5,2),

    -- 기술적 지표 (선택)
    ma5 NUMERIC(10,2),
    ma20 NUMERIC(10,2),
    rsi NUMERIC(5,2),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT unique_ticker_monitoring_date UNIQUE(ticker, date)
);

-- 3. AI 분석 리포트 (선택)
CREATE TABLE IF NOT EXISTS ai_analysis_reports (
    id SERIAL PRIMARY KEY,
    ticker VARCHAR(6) NOT NULL,
    report_date DATE NOT NULL,

    -- AI 분석 결과
    summary TEXT,
    recommendation VARCHAR(20), -- 'BUY', 'HOLD', 'SELL'
    confidence_score NUMERIC(3,2),

    -- 상세 분석
    momentum_analysis TEXT,
    liquidity_analysis TEXT,
    risk_factors TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT unique_ticker_report_date UNIQUE(ticker, report_date)
);

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_stock_pool_status ON stock_pool(status);
CREATE INDEX IF NOT EXISTS idx_stock_pool_ticker ON stock_pool(ticker);
CREATE INDEX IF NOT EXISTS idx_stock_pool_added_date ON stock_pool(added_date);
CREATE INDEX IF NOT EXISTS idx_stock_pool_score ON stock_pool(final_score DESC);

CREATE INDEX IF NOT EXISTS idx_monitoring_ticker_date ON stock_monitoring_history(ticker, date);
CREATE INDEX IF NOT EXISTS idx_monitoring_date ON stock_monitoring_history(date DESC);

CREATE INDEX IF NOT EXISTS idx_ai_reports_ticker_date ON ai_analysis_reports(ticker, report_date);

-- 업데이트 트리거 (updated_at 자동 갱신)
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_stock_pool_updated_at
    BEFORE UPDATE ON stock_pool
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- 초기 데이터 확인 뷰
CREATE OR REPLACE VIEW v_monitoring_stocks AS
SELECT
    sp.ticker,
    sp.name,
    sp.status,
    sp.final_score,
    sp.added_date,
    sp.monitored_days,
    sp.realtime_price,
    COUNT(smh.id) as history_count
FROM stock_pool sp
LEFT JOIN stock_monitoring_history smh ON sp.ticker = smh.ticker
WHERE sp.status = 'monitoring'
GROUP BY sp.id
ORDER BY sp.final_score DESC;

-- 승인된 종목 뷰
CREATE OR REPLACE VIEW v_approved_stocks AS
SELECT
    ticker,
    name,
    final_score,
    realtime_price as current_price,
    approved_date,
    notes
FROM stock_pool
WHERE status = 'approved'
ORDER BY final_score DESC;

COMMENT ON TABLE stock_pool IS '필터링된 종목 풀 - 모니터링 및 승인 관리';
COMMENT ON TABLE stock_monitoring_history IS '일별 모니터링 데이터';
COMMENT ON TABLE ai_analysis_reports IS 'AI 분석 리포트 저장';
