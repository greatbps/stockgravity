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
from page_modules import dashboard_compact as dashboard
from sidebar_utils import render_sidebar_badges

# Streamlit 기본 네비게이션 숨기기
st.markdown("""
<style>
    [data-testid="stSidebarNav"] {display: none;}
</style>
""", unsafe_allow_html=True)

# 사이드바 커스텀 네비게이션
st.sidebar.title("📊 StockGravity")
st.sidebar.caption("Korean Stock Filtering & Monitoring System")

# 페이지 네비게이션
st.sidebar.markdown("---")
st.sidebar.markdown("### 📑 Navigation")

# 현재 페이지 표시
current_page = st.session_state.get('current_page', 'Dashboard')

if st.sidebar.button("📊 Dashboard", use_container_width=True, type="primary" if current_page == 'Dashboard' else "secondary"):
    st.session_state.current_page = 'Dashboard'

if st.sidebar.button("📦 Stock Pool", use_container_width=True, type="primary" if current_page == 'Stock Pool' else "secondary"):
    st.switch_page("pages/1_📦_Stock_Pool.py")

if st.sidebar.button("🤖 AI Reports", use_container_width=True, type="primary" if current_page == 'AI Reports' else "secondary"):
    st.switch_page("pages/2_🤖_AI_Reports.py")

if st.sidebar.button("✅ Trading", use_container_width=True, type="primary" if current_page == 'Trading' else "secondary"):
    st.switch_page("pages/3_✅_Trading.py")

st.sidebar.markdown("---")

# 사이드바 배지 렌더링
render_sidebar_badges()

# 메인 대시보드 렌더링
dashboard.render()
