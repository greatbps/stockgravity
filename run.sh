#!/bin/bash

echo "======================================"
echo "StockGravity Dashboard 시작"
echo "======================================"

# 가상환경 활성화
if [ -d "venv" ]; then
    echo "✓ 가상환경 활성화 중..."
    source venv/bin/activate
else
    echo "⚠️  가상환경이 없습니다. venv를 먼저 생성해주세요."
    exit 1
fi

echo ""
echo "======================================"
echo "🚀 대시보드 시작 (포트 8000)..."
echo "로컬 접속: http://localhost:8000"
echo "외부 접속: http://$(hostname -I | awk '{print $1}'):8000"
echo ""
echo "종료하려면 Ctrl+C를 누르세요."
echo "======================================"

streamlit run app.py --server.port 8000 --server.address 0.0.0.0
