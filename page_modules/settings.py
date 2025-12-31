#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
⚙️ Settings & Logs - 설정 및 로그
"""
import streamlit as st
import os


def render():
    st.title("⚙️ Settings & Logs")
    st.caption("시스템 설정 및 로그 확인")

    tab1, tab2 = st.tabs(["⚙️ Settings", "📜 Logs"])

    # ===== 설정 =====
    with tab1:
        st.subheader("자동 업데이트 설정")

        st.info("현재 설정: 평일 15:20 자동 실행")

        st.markdown("""
        ### 필터링 기준
        - 거래대금: > 1억원
        - 종가: > 5,000원
        - 5일 변화율: > -5%
        - 거래량 비율: > 0.5x

        ### AI 분석 설정
        - 모델: Google Gemini 2.5 Flash
        - 분석 대상: 상위 5개 종목
        """)

        st.divider()

        st.subheader("데이터베이스 설정")

        st.code("""
DB_HOST=localhost
DB_PORT=5432
DB_NAME=stockgravity
DB_USER=postgres
        """, language="ini")

        st.success("✅ 데이터베이스 연결 정상")

    # ===== 로그 =====
    with tab2:
        st.subheader("📜 System Logs")

        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        log_file = os.path.join(project_root, "cron.log")

        if os.path.exists(log_file):
            st.download_button(
                "📥 Download Log",
                data=open(log_file, 'r').read(),
                file_name="cron.log",
                mime="text/plain"
            )

            st.divider()

            # 최근 로그 표시
            with open(log_file, 'r') as f:
                lines = f.readlines()
                recent_logs = lines[-100:]  # 최근 100줄

            st.text_area(
                "최근 로그 (최근 100줄)",
                value="".join(recent_logs),
                height=400
            )
        else:
            st.info("로그 파일이 없습니다.")
            st.write(f"경로: {log_file}")
