-- stock_pool_history 테이블 생성 (과거 기록 보관)
CREATE TABLE IF NOT EXISTS stock_pool_history (
    id SERIAL PRIMARY KEY,
    ticker VARCHAR(6) NOT NULL,
    name VARCHAR(100),
    close NUMERIC(12,2),
    trading_value BIGINT,
    change_5d NUMERIC(10,2),
    vol_ratio NUMERIC(10,2),
    final_score NUMERIC(10,2),
    status VARCHAR(20),
    realtime_price NUMERIC(12,2),
    realtime_volume BIGINT,
    realtime_updated_at TIMESTAMP,
    notes TEXT,
    added_date DATE NOT NULL,
    snapshot_date DATE NOT NULL,  -- 스냅샷 찍은 날짜
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT unique_history_ticker_snapshot UNIQUE (ticker, added_date, snapshot_date)
);

-- 인덱스
CREATE INDEX IF NOT EXISTS idx_pool_history_ticker ON stock_pool_history(ticker);
CREATE INDEX IF NOT EXISTS idx_pool_history_snapshot ON stock_pool_history(snapshot_date);
CREATE INDEX IF NOT EXISTS idx_pool_history_status ON stock_pool_history(status);

COMMENT ON TABLE stock_pool_history IS 'stock_pool 일별 스냅샷 히스토리';
COMMENT ON COLUMN stock_pool_history.snapshot_date IS '해당 데이터가 유효했던 날짜';
