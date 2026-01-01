-- 한국 증시 휴장일 테이블 생성
CREATE TABLE IF NOT EXISTS market_holidays (
    id SERIAL PRIMARY KEY,
    holiday_date DATE NOT NULL UNIQUE,
    holiday_name VARCHAR(100) NOT NULL,
    holiday_type VARCHAR(20) DEFAULT 'regular',  -- 'regular', 'temporary', 'weekend'
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_market_holidays_date ON market_holidays(holiday_date);

-- 2026년 한국 증시 휴장일 데이터 삽입
INSERT INTO market_holidays (holiday_date, holiday_name, holiday_type, description) VALUES
-- 1월
('2026-01-01', '신정', 'regular', '새해 첫날'),

-- 2월 (설날)
('2026-02-16', '설날 연휴', 'regular', '설날 전날'),
('2026-02-17', '설날', 'regular', '설날 당일'),
('2026-02-18', '설날 연휴', 'regular', '설날 다음날'),

-- 3월
('2026-03-01', '삼일절', 'regular', '3·1 독립운동 기념일'),

-- 4월
('2026-04-05', '식목일', 'regular', '식목일 (2026년부터 공휴일)'),

-- 5월
('2026-05-05', '어린이날', 'regular', '어린이날'),
('2026-05-19', '석가탄신일', 'regular', '부처님 오신 날'),

-- 6월
('2026-06-06', '현충일', 'regular', '현충일'),

-- 8월
('2026-08-15', '광복절', 'regular', '광복절'),

-- 9월 (추석)
('2026-09-24', '추석 연휴', 'regular', '추석 전날'),
('2026-09-25', '추석', 'regular', '추석 당일'),
('2026-09-26', '추석 연휴', 'regular', '추석 다음날'),

-- 10월
('2026-10-03', '개천절', 'regular', '개천절'),
('2026-10-09', '한글날', 'regular', '한글날'),

-- 12월
('2026-12-25', '성탄절', 'regular', '크리스마스')

ON CONFLICT (holiday_date) DO NOTHING;

-- 코멘트 추가
COMMENT ON TABLE market_holidays IS '한국 증시 휴장일 (주말 제외)';
COMMENT ON COLUMN market_holidays.holiday_type IS 'regular: 정기 공휴일, temporary: 임시 공휴일, weekend: 주말';
