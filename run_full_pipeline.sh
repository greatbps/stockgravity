#!/bin/bash
# 전체 파이프라인 실행 스크립트

echo "======================================"
echo "StockGravity 전체 파이프라인 실행"
echo "======================================"

# 가상환경 활성화
source venv/bin/activate

echo ""
echo "1️⃣ 종목 필터링 (2,790개 → 500개)"
echo "======================================"
python quick_filter.py --top 500

if [ $? -ne 0 ]; then
    echo "❌ 필터링 실패"
    exit 1
fi

echo ""
echo "2️⃣ 실시간 데이터 수집 (500개 종목)"
echo "======================================"
python collect_realtime_data.py --workers 10

if [ $? -ne 0 ]; then
    echo "⚠️ 실시간 수집 실패 (장 마감 시간일 수 있음)"
fi

echo ""
echo "3️⃣ AI 분석 (상위 5개 종목)"
echo "======================================"
python generate_ai_report.py --top 5

if [ $? -ne 0 ]; then
    echo "⚠️ AI 분석 실패 (API 할당량 확인)"
fi

echo ""
echo "======================================"
echo "✅ 파이프라인 완료!"
echo ""
echo "결과 확인:"
echo "  - 필터링: filtered_stocks.csv"
echo "  - 실시간: filtered_stocks_with_realtime.csv"
echo "  - AI: ai_analysis_report.txt"
echo "======================================"
