#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🤖 AI Reports - AI 분석 리포트
"""
import streamlit as st
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

st.set_page_config(
    page_title="AI Reports - StockGravity",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

from page_modules import ai_reports
from sidebar_utils import render_sidebar_badges

st.sidebar.title("📊 StockGravity")
st.sidebar.caption("Korean Stock Filtering & Monitoring System")

# 사이드바 배지 렌더링
render_sidebar_badges()

ai_reports.render()
