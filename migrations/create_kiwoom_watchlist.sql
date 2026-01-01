-- 키움 워치리스트 테이블 생성
-- 이 테이블은 StockGravity에서 키움 트레이딩 시스템으로 전송된 종목을 추적합니다.

CREATE TABLE IF NOT EXISTS kiwoom_watchlist (
    id SERIAL PRIMARY KEY,

    -- 종목 정보
    ticker VARCHAR(10) NOT NULL,
    name VARCHAR(100),
    source VARCHAR(20) NOT NULL,  -- 'stock_pool' 또는 'ai_reports'

    -- 상태 관리
    status VARCHAR(20) DEFAULT 'monitoring',  -- 'monitoring', 'trading', 'completed', 'cancelled'

    -- 모니터링 조건
    added_to_kiwoom_at TIMESTAMP DEFAULT NOW(),
    entry_condition TEXT,           -- 진입 조건 설명
    target_price NUMERIC(10, 2),    -- 목표가
    stop_loss NUMERIC(10, 2),       -- 손절가
    position_size INT,              -- 포지션 크기 (주)

    -- 매매 정보
    order_date TIMESTAMP,           -- 주문 시각
    order_type VARCHAR(20),         -- 'buy', 'sell'
    order_price NUMERIC(10, 2),     -- 주문가
    order_quantity INT,             -- 주문수량

    -- 체결 정보
    executed_at TIMESTAMP,          -- 체결 시각
    executed_price NUMERIC(10, 2),  -- 체결가
    executed_quantity INT,          -- 체결수량

    -- 결과 (종료 시)
    exit_date TIMESTAMP,            -- 청산 시각
    exit_price NUMERIC(10, 2),      -- 청산가
    profit_loss NUMERIC(12, 2),     -- 손익 (금액)
    profit_rate NUMERIC(6, 2),      -- 수익률 (%)
    completed_at TIMESTAMP,         -- 완료 시각

    -- 추가 정보
    notes TEXT,                     -- 메모
    kiwoom_order_id VARCHAR(50),    -- 키움 주문번호

    -- 타임스탬프
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_kiwoom_watchlist_ticker ON kiwoom_watchlist(ticker);
CREATE INDEX IF NOT EXISTS idx_kiwoom_watchlist_status ON kiwoom_watchlist(status);
CREATE INDEX IF NOT EXISTS idx_kiwoom_watchlist_source ON kiwoom_watchlist(source);
CREATE INDEX IF NOT EXISTS idx_kiwoom_watchlist_created ON kiwoom_watchlist(created_at DESC);

-- stock_pool 테이블에 키움 관련 컬럼 추가
ALTER TABLE stock_pool
ADD COLUMN IF NOT EXISTS sent_to_kiwoom_at TIMESTAMP,
ADD COLUMN IF NOT EXISTS kiwoom_status VARCHAR(20);

-- 코멘트 추가
COMMENT ON TABLE kiwoom_watchlist IS '키움 트레이딩 시스템 워치리스트';
COMMENT ON COLUMN kiwoom_watchlist.source IS 'stock_pool 또는 ai_reports';
COMMENT ON COLUMN kiwoom_watchlist.status IS 'monitoring: 모니터링 중, trading: 매매 중, completed: 완료, cancelled: 취소';
COMMENT ON COLUMN kiwoom_watchlist.profit_rate IS '수익률 (%), (exit_price - executed_price) / executed_price * 100';
