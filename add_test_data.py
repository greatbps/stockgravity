#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""테스트 데이터 추가"""

from db_config import get_db_connection
from datetime import datetime, timedelta
import random

def add_test_stocks():
    """테스트 종목 데이터 추가"""

    test_stocks = [
        ('005930', '삼성전자', 72000, 850000000000, 3.5, 1.2, 88.5),
        ('000660', 'SK하이닉스', 135000, 450000000000, 5.2, 1.5, 92.3),
        ('035420', 'NAVER', 220000, 280000000000, -2.1, 0.8, 75.2),
        ('005380', '현대차', 195000, 320000000000, 4.8, 1.3, 85.7),
        ('051910', 'LG화학', 425000, 210000000000, 2.3, 1.1, 81.4),
        ('035720', '카카오', 48500, 180000000000, -1.5, 0.9, 72.8),
        ('006400', '삼성SDI', 385000, 190000000000, 6.2, 1.6, 90.1),
        ('028260', '삼성물산', 115000, 150000000000, 1.8, 1.0, 78.6),
        ('105560', 'KB금융', 58000, 140000000000, 3.2, 1.2, 82.3),
        ('055550', '신한지주', 39500, 130000000000, 2.7, 1.1, 79.5),
    ]

    with get_db_connection() as conn:
        cur = conn.cursor()

        for ticker, name, close, trading_value, change_5d, vol_ratio, final_score in test_stocks:
            # 실시간 가격 (종가 기준 ±2% 랜덤)
            realtime_price = close * (1 + random.uniform(-0.02, 0.02))
            realtime_volume = trading_value // close * random.randint(80, 120) // 100

            cur.execute("""
                INSERT INTO stock_pool
                (ticker, name, close, trading_value, change_5d, vol_ratio, final_score,
                 status, realtime_price, realtime_volume, realtime_updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                ON CONFLICT (ticker, added_date) DO UPDATE SET
                    close = EXCLUDED.close,
                    trading_value = EXCLUDED.trading_value,
                    change_5d = EXCLUDED.change_5d,
                    vol_ratio = EXCLUDED.vol_ratio,
                    final_score = EXCLUDED.final_score,
                    realtime_price = EXCLUDED.realtime_price,
                    realtime_volume = EXCLUDED.realtime_volume,
                    realtime_updated_at = NOW()
            """, (ticker, name, close, trading_value, change_5d, vol_ratio, final_score,
                  'monitoring', realtime_price, realtime_volume))

        print(f"✅ {len(test_stocks)}개 테스트 종목 추가 완료")

if __name__ == "__main__":
    add_test_stocks()
