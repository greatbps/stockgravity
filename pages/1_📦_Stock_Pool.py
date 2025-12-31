#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📦 Stock Pool
"""
import streamlit as st
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

st.set_page_config(
    page_title="Stock Pool",
    page_icon="📦",
    layout="wide"
)

# 기본 네비게이션 숨기기
st.markdown("""
<style>
    [data-testid="stSidebarNav"] {display: none;}
</style>
""", unsafe_allow_html=True)

from page_modules import stock_pool_compact as stock_pool
from sidebar_utils import render_sidebar_badges

st.sidebar.title("📊 StockGravity")
st.sidebar.caption("Korean Stock Filtering & Monitoring System")

st.sidebar.markdown("---")
st.sidebar.markdown("### 📑 Navigation")

if st.sidebar.button("📊 Dashboard", use_container_width=True):
    st.switch_page("app.py")

if st.sidebar.button("📦 Stock Pool", use_container_width=True, type="primary"):
    pass

if st.sidebar.button("🤖 AI Reports", use_container_width=True):
    st.switch_page("pages/2_🤖_AI_Reports.py")

if st.sidebar.button("✅ Trading", use_container_width=True):
    st.switch_page("pages/3_✅_Trading.py")

st.sidebar.markdown("---")
render_sidebar_badges()

stock_pool.render()
