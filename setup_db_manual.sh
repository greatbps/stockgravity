#!/bin/bash
# 수동 실행용 DB 설정 스크립트

echo "======================================"
echo "StockGravity DB 설정"
echo "======================================"

# 1. 데이터베이스 생성
echo "1. 데이터베이스 생성..."
sudo -u postgres psql -c "CREATE DATABASE stockgravity;" 2>&1 | grep -v "already exists" || echo "  (이미 존재하거나 생성 완료)"

# 2. 스키마 적용
echo "2. 스키마 적용..."
sudo -u postgres psql -d stockgravity -f /home/greatbps/projects/stockgravity/db_schema.sql

# 3. .env 설정
echo "3. .env 파일 업데이트..."
cd /home/greatbps/projects/stockgravity

# DB 설정 추가 (중복 체크)
if ! grep -q "DB_HOST" .env 2>/dev/null; then
    echo "DB_HOST=localhost" >> .env
    echo "DB_PORT=5432" >> .env
    echo "DB_NAME=stockgravity" >> .env
    echo "DB_USER=postgres" >> .env
    echo "DB_PASSWORD=" >> .env
fi

echo ""
echo "======================================"
echo "완료! 이제 .env 파일에서 DB_PASSWORD를 설정하세요."
echo "======================================"
