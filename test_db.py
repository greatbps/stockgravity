#!/usr/bin/env python3
"""데이터베이스 기본 작동 테스트"""

import sys
from db_config import DatabaseConfig

def test_database():
    """데이터베이스 연결 및 기본 작동 테스트"""

    print("=" * 60)
    print("StockGravity 데이터베이스 테스트")
    print("=" * 60)

    # 1. 연결 테스트
    print("\n1. DB 연결 테스트...")
    db = DatabaseConfig()
    db.init_pool(minconn=1, maxconn=5)

    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()

            # 2. 테이블 확인
            print("\n2. 테이블 확인...")
            cursor.execute("""
                SELECT tablename FROM pg_tables
                WHERE schemaname = 'public'
                ORDER BY tablename
            """)
            tables = cursor.fetchall()
            for table in tables:
                print(f"   ✓ {table[0]}")

            # 3. 뷰 확인
            print("\n3. 뷰 확인...")
            cursor.execute("""
                SELECT viewname FROM pg_views
                WHERE schemaname = 'public'
                ORDER BY viewname
            """)
            views = cursor.fetchall()
            for view in views:
                print(f"   ✓ {view[0]}")

            # 4. 테스트 데이터 삽입
            print("\n4. 테스트 데이터 삽입...")
            cursor.execute("""
                INSERT INTO stock_pool (ticker, name, close, trading_value, change_5d, vol_ratio, final_score)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (ticker, added_date) DO NOTHING
                RETURNING id, ticker, name
            """, ('000000', 'TEST종목', 10000, 150000000, 5.5, 1.2, 85.5))

            result = cursor.fetchone()
            if result:
                print(f"   ✓ 삽입 성공: ID={result[0]}, Ticker={result[1]}, Name={result[2]}")
            else:
                print(f"   ⚠ 이미 존재하는 데이터 (충돌)")

            # 5. 데이터 조회
            print("\n5. 데이터 조회...")
            cursor.execute("""
                SELECT ticker, name, close, trading_value, status
                FROM stock_pool
                ORDER BY created_at DESC
                LIMIT 5
            """)
            rows = cursor.fetchall()
            if rows:
                for row in rows:
                    print(f"   - {row[0]} {row[1]}: ₩{row[2]:,.0f}, 거래대금 {row[3]:,}원, 상태={row[4]}")
            else:
                print("   (데이터 없음)")

            # 6. 테스트 데이터 삭제
            print("\n6. 테스트 데이터 정리...")
            cursor.execute("DELETE FROM stock_pool WHERE ticker = '000000'")
            deleted = cursor.rowcount
            print(f"   ✓ {deleted}개 행 삭제")

            # 7. 뷰 테스트
            print("\n7. 뷰 조회 테스트...")
            cursor.execute("SELECT COUNT(*) FROM v_monitoring_stocks")
            count = cursor.fetchone()[0]
            print(f"   ✓ v_monitoring_stocks: {count}개 종목")

            cursor.execute("SELECT COUNT(*) FROM v_approved_stocks")
            count = cursor.fetchone()[0]
            print(f"   ✓ v_approved_stocks: {count}개 종목")

            cursor.close()

        print("\n" + "=" * 60)
        print("✅ 모든 테스트 통과!")
        print("=" * 60)

        return True

    except Exception as e:
        print(f"\n❌ 에러 발생: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        db.close_pool()

if __name__ == "__main__":
    success = test_database()
    sys.exit(0 if success else 1)
