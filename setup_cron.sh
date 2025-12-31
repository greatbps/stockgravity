#!/bin/bash
# StockGravity 자동 업데이트 크론 설정

echo "======================================"
echo "StockGravity 크론 작업 설정"
echo "======================================"

# 프로젝트 경로
PROJECT_DIR="/home/greatbps/projects/stockgravity"
PYTHON_BIN="$PROJECT_DIR/venv/bin/python"
SCRIPT="$PROJECT_DIR/daily_auto_update.py"

# 크론 작업 내용
# 평일 15:20에 실행 (장 마감 10분 전 - 실시간 데이터 수집)
CRON_JOB="20 15 * * 1-5 $PYTHON_BIN $SCRIPT >> $PROJECT_DIR/cron.log 2>&1"

echo ""
echo "설정할 크론 작업:"
echo "$CRON_JOB"
echo ""
echo "스케줄: 평일(월~금) 15:20 (장 마감 10분 전)"
echo "작업: 필터링 → 실시간 수집 → AI 분석"
echo "목적: 실시간 데이터 수집 (장 운영 중)"
echo ""

# 기존 크론 작업 확인
if crontab -l 2>/dev/null | grep -q "daily_auto_update.py"; then
    echo "⚠️  기존 크론 작업이 이미 존재합니다."
    echo ""
    crontab -l | grep "daily_auto_update.py"
    echo ""
    read -p "기존 작업을 삭제하고 새로 등록하시겠습니까? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "취소되었습니다."
        exit 0
    fi

    # 기존 작업 제거
    crontab -l | grep -v "daily_auto_update.py" | crontab -
fi

# 새 크론 작업 추가
(crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -

echo ""
echo "✅ 크론 작업이 등록되었습니다!"
echo ""
echo "현재 등록된 크론 작업:"
crontab -l | grep "daily_auto_update.py"
echo ""
echo "======================================"
echo "수동 실행 테스트:"
echo "  $PYTHON_BIN $SCRIPT"
echo ""
echo "로그 확인:"
echo "  tail -f $PROJECT_DIR/daily_update.log"
echo "  tail -f $PROJECT_DIR/cron.log"
echo "======================================"
