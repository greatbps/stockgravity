-- daily_prices 테이블 생성
CREATE TABLE IF NOT EXISTS daily_prices (
    id SERIAL PRIMARY KEY,
    ticker VARCHAR(6) NOT NULL,
    date DATE NOT NULL,
    open NUMERIC(12,2),
    high NUMERIC(12,2),
    low NUMERIC(12,2),
    close NUMERIC(12,2),
    volume BIGINT,
    diff VARCHAR(20),  -- 전일비 (원본 텍스트)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- 중복 방지
    CONSTRAINT unique_ticker_date UNIQUE (ticker, date)
);

-- 인덱스 생성 (조회 성능 향상)
CREATE INDEX IF NOT EXISTS idx_daily_prices_ticker ON daily_prices(ticker);
CREATE INDEX IF NOT EXISTS idx_daily_prices_date ON daily_prices(date);
CREATE INDEX IF NOT EXISTS idx_daily_prices_ticker_date ON daily_prices(ticker, date DESC);

-- 코멘트
COMMENT ON TABLE daily_prices IS '일별 주가 데이터 (2014~ 현재)';
COMMENT ON COLUMN daily_prices.ticker IS '종목코드 (6자리)';
COMMENT ON COLUMN daily_prices.date IS '거래일';
COMMENT ON COLUMN daily_prices.diff IS '전일비 (상승/하락 텍스트)';
