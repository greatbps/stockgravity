#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
StockGravity 일일 자동 업데이트
장 종료 후 자동 실행: 필터링 → 실시간 수집 → AI 분석
"""

import subprocess
import sys
import os
from datetime import datetime
import logging

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('daily_update.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


class DailyUpdater:
    """일일 자동 업데이트 실행기"""

    def __init__(self):
        self.project_root = os.path.dirname(os.path.abspath(__file__))
        self.python_exec = sys.executable
        self.success_count = 0
        self.failed_count = 0

    def run_script(self, script_name: str, args: list = None, description: str = "") -> bool:
        """
        스크립트 실행

        Args:
            script_name: 실행할 스크립트 파일명
            args: 추가 인자
            description: 작업 설명

        Returns:
            성공 여부
        """
        script_path = os.path.join(self.project_root, script_name)
        cmd = [self.python_exec, script_path]

        if args:
            cmd.extend(args)

        logger.info(f"{'='*60}")
        logger.info(f"시작: {description}")
        logger.info(f"명령: {' '.join(cmd)}")
        logger.info(f"{'='*60}")

        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=600  # 10분 타임아웃
            )

            if result.returncode == 0:
                logger.info(f"✅ 완료: {description}")
                logger.info(f"출력:\n{result.stdout}")
                self.success_count += 1
                return True
            else:
                logger.error(f"❌ 실패: {description}")
                logger.error(f"에러:\n{result.stderr}")
                self.failed_count += 1
                return False

        except subprocess.TimeoutExpired:
            logger.error(f"⏰ 타임아웃: {description} (10분 초과)")
            self.failed_count += 1
            return False
        except Exception as e:
            logger.error(f"❌ 예외 발생: {description}")
            logger.error(f"상세: {str(e)}")
            self.failed_count += 1
            return False

    def run_daily_update(self):
        """일일 업데이트 전체 실행"""
        start_time = datetime.now()
        logger.info(f"\n{'#'*60}")
        logger.info(f"StockGravity 일일 자동 업데이트 시작")
        logger.info(f"시작 시간: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"{'#'*60}\n")

        # 1단계: 필터링 (3분)
        if not self.run_script(
            "quick_filter.py",
            ["--top", "500"],
            "종목 필터링 (2,790개 → 500개)"
        ):
            logger.error("필터링 실패로 중단합니다.")
            return False

        # 2단계: 실시간 데이터 수집 (1분)
        if not self.run_script(
            "collect_realtime_data.py",
            ["--workers", "10"],
            "실시간 데이터 수집 (500개 종목)"
        ):
            logger.warning("실시간 데이터 수집 실패 (계속 진행)")
            # 실시간 수집 실패해도 계속 진행 (장 마감 시간이면 정상)

        # 3단계: AI 분석 (2분)
        if not self.run_script(
            "generate_ai_report.py",
            ["--top", "5"],
            "AI 분석 리포트 생성 (상위 5개)"
        ):
            logger.warning("AI 분석 실패 (계속 진행)")
            # AI 분석 실패해도 계속 진행

        # 완료
        end_time = datetime.now()
        elapsed = (end_time - start_time).total_seconds()

        logger.info(f"\n{'#'*60}")
        logger.info(f"일일 업데이트 완료")
        logger.info(f"종료 시간: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"소요 시간: {elapsed/60:.1f}분")
        logger.info(f"성공: {self.success_count}개 | 실패: {self.failed_count}개")
        logger.info(f"{'#'*60}\n")

        return True


def main():
    """메인 실행"""
    updater = DailyUpdater()

    try:
        success = updater.run_daily_update()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.warning("\n사용자에 의해 중단되었습니다.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n예상치 못한 오류: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
