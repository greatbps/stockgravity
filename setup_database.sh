#!/bin/bash
# PostgreSQL 데이터베이스 초기 설정

echo "======================================"
echo "StockGravity PostgreSQL 설정"
echo "======================================"

# 기본 설정
DB_NAME="stockgravity"
DB_USER="postgres"

echo ""
echo "1. 데이터베이스 생성 확인..."

# 데이터베이스 존재 확인
if sudo -u postgres psql -lqt | cut -d \| -f 1 | grep -qw $DB_NAME; then
    echo "✓ 데이터베이스 '$DB_NAME'가 이미 존재합니다."
else
    echo "데이터베이스 '$DB_NAME' 생성 중..."
    sudo -u postgres createdb $DB_NAME
    if [ $? -eq 0 ]; then
        echo "✓ 데이터베이스 생성 완료"
    else
        echo "❌ 데이터베이스 생성 실패"
        exit 1
    fi
fi

echo ""
echo "2. 스키마 적용 중..."
sudo -u postgres psql -d $DB_NAME -f db_schema.sql

if [ $? -eq 0 ]; then
    echo "✓ 스키마 적용 완료"
else
    echo "❌ 스키마 적용 실패"
    exit 1
fi

echo ""
echo "3. .env 파일 설정..."

# .env 파일이 없으면 생성
if [ ! -f ".env" ]; then
    echo "DB_HOST=localhost" >> .env
    echo "DB_PORT=5432" >> .env
    echo "DB_NAME=$DB_NAME" >> .env
    echo "DB_USER=$DB_USER" >> .env
    echo "DB_PASSWORD=" >> .env
    echo ""
    echo "⚠️  .env 파일을 생성했습니다."
    echo "   DB_PASSWORD를 설정해주세요!"
else
    echo "✓ .env 파일이 이미 존재합니다."
fi

echo ""
echo "4. 연결 테스트..."
source venv/bin/activate
python db_config.py

echo ""
echo "======================================"
echo "✅ 데이터베이스 설정 완료!"
echo ""
echo "생성된 테이블:"
echo "  - stock_pool (필터링된 종목)"
echo "  - stock_monitoring_history (모니터링 데이터)"
echo "  - ai_analysis_reports (AI 분석 리포트)"
echo ""
echo "뷰:"
echo "  - v_monitoring_stocks (모니터링 중인 종목)"
echo "  - v_approved_stocks (승인된 종목)"
echo "======================================"
