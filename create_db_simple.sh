#!/bin/bash
# Simple database creation script
# Run this manually: ./create_db_simple.sh

echo "StockGravity 데이터베이스 생성"
echo "================================"
echo ""
echo "PostgreSQL postgres 사용자 암호를 입력하세요:"
echo ""

# Create database
psql -U postgres -d postgres << EOF
CREATE DATABASE stockgravity;
\q
EOF

if [ $? -eq 0 ]; then
    echo ""
    echo "✓ 데이터베이스 생성 완료"
    echo ""
    echo "이제 스키마를 적용합니다..."
    echo ""

    # Apply schema
    psql -U postgres -d stockgravity -f /home/greatbps/projects/stockgravity/db_schema.sql

    if [ $? -eq 0 ]; then
        echo ""
        echo "✓ 스키마 적용 완료"
        echo ""
        echo "================================"
        echo "데이터베이스 설정 완료!"
        echo "================================"
    else
        echo ""
        echo "❌ 스키마 적용 실패"
    fi
else
    echo ""
    echo "❌ 데이터베이스 생성 실패"
    echo "   이미 존재하는 경우 스키마 적용만 진행합니다..."
    echo ""

    psql -U postgres -d stockgravity -f /home/greatbps/projects/stockgravity/db_schema.sql
fi
