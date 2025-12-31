#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PostgreSQL 데이터베이스 연결 설정
"""

import os
import psycopg2
from psycopg2 import pool
from dotenv import load_dotenv
from contextlib import contextmanager
import logging

load_dotenv()
logger = logging.getLogger(__name__)


class DatabaseConfig:
    """데이터베이스 연결 설정"""

    def __init__(self):
        """환경변수에서 DB 설정 로드"""
        self.host = os.getenv("DB_HOST", "localhost")
        self.port = os.getenv("DB_PORT", "5432")
        self.database = os.getenv("DB_NAME", "stockgravity")
        self.user = os.getenv("DB_USER", "postgres")
        self.password = os.getenv("DB_PASSWORD", "")

        # 연결 풀 생성
        self.connection_pool = None

    def get_connection_string(self):
        """PostgreSQL 연결 문자열 반환"""
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"

    def init_pool(self, minconn=1, maxconn=10):
        """연결 풀 초기화"""
        try:
            self.connection_pool = psycopg2.pool.SimpleConnectionPool(
                minconn,
                maxconn,
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password
            )
            logger.info(f"✅ DB 연결 풀 초기화 완료 (min={minconn}, max={maxconn})")
            return True
        except Exception as e:
            logger.error(f"❌ DB 연결 풀 초기화 실패: {e}")
            return False

    @contextmanager
    def get_connection(self):
        """연결 풀에서 연결 가져오기 (컨텍스트 매니저)"""
        if not self.connection_pool:
            self.init_pool()

        conn = self.connection_pool.getconn()
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"DB 작업 중 오류: {e}")
            raise
        finally:
            self.connection_pool.putconn(conn)

    def close_pool(self):
        """연결 풀 종료"""
        if self.connection_pool:
            self.connection_pool.closeall()
            logger.info("DB 연결 풀 종료")


# 전역 DB 설정 인스턴스
db_config = DatabaseConfig()


@contextmanager
def get_db_connection():
    """DB 연결 가져오기 (단순 사용)"""
    with db_config.get_connection() as conn:
        yield conn


def execute_query(query, params=None, fetch=False):
    """
    쿼리 실행 헬퍼 함수

    Args:
        query: SQL 쿼리
        params: 쿼리 파라미터
        fetch: True면 결과 반환, False면 실행만

    Returns:
        fetch=True면 결과 rows, False면 None
    """
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            if fetch:
                return cur.fetchall()
            return None


if __name__ == "__main__":
    """연결 테스트"""
    logging.basicConfig(level=logging.INFO)

    print("PostgreSQL 연결 테스트...")
    print(f"연결 문자열: {db_config.get_connection_string()}")

    try:
        if db_config.init_pool():
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT version();")
                    version = cur.fetchone()
                    print(f"✅ 연결 성공!")
                    print(f"PostgreSQL 버전: {version[0]}")

            db_config.close_pool()
        else:
            print("❌ 연결 실패")
    except Exception as e:
        print(f"❌ 오류: {e}")
