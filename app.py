#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
StockGravity - Main Dashboard (Home)
"""
import streamlit as st
import sys
import os

# 경로 설정
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

st.set_page_config(
    page_title="StockGravity",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Dashboard (Home) 페이지
from page_modules import dashboard
from sidebar_utils import render_sidebar_badges

st.sidebar.title("📊 StockGravity")
st.sidebar.caption("Korean Stock Filtering & Monitoring System")

# 사이드바 배지 렌더링
render_sidebar_badges()

# 메인 대시보드 렌더링
dashboard.render()
