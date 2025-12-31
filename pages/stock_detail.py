#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📌 Stock Detail - 종목 상세 페이지
"""
import streamlit as st
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

st.set_page_config(
    page_title="Stock Detail - StockGravity",
    page_icon="📌",
    layout="wide",
    initial_sidebar_state="expanded"
)

from page_modules import stock_detail
from sidebar_utils import render_sidebar_badges

st.sidebar.title("📊 StockGravity")
st.sidebar.caption("Korean Stock Filtering & Monitoring System")

# 사이드바 배지 렌더링
render_sidebar_badges()

stock_detail.render()
