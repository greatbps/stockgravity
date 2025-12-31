#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
사이드바 배지용 유틸리티
"""
import streamlit as st
from db_config import get_db_connection


@st.cache_data(ttl=30)
def get_stock_pool_counts():
    """Stock Pool 상태별 개수"""
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT status, COUNT(*) as count
            FROM stock_pool
            GROUP BY status
        """)
        results = cur.fetchall()

    counts = {status: count for status, count in results}
    return {
        'monitoring': counts.get('monitoring', 0),
        'approved': counts.get('approved', 0),
        'rejected': counts.get('rejected', 0),
        'trading': counts.get('trading', 0),
        'completed': counts.get('completed', 0)
    }


@st.cache_data(ttl=30)
def get_ai_reports_counts():
    """AI Reports 추천별 개수"""
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT recommendation, COUNT(*) as count
            FROM ai_analysis_reports
            WHERE report_date >= CURRENT_DATE - INTERVAL '7 days'
            GROUP BY recommendation
        """)
        results = cur.fetchall()

    counts = {rec: count for rec, count in results}
    return {
        'STRONG_APPROVE': counts.get('STRONG_APPROVE', 0),
        'WATCH_MORE': counts.get('WATCH_MORE', 0),
        'DO_NOT_APPROVE': counts.get('DO_NOT_APPROVE', 0),
        'total': sum(counts.values())
    }


def render_sidebar_badges():
    """사이드바 배지 렌더링 (간소화)"""
    pool_counts = get_stock_pool_counts()
    ai_counts = get_ai_reports_counts()

    st.sidebar.divider()
    st.sidebar.caption("📊 **Quick Stats**")

    # AI 분석 현황
    if ai_counts['total'] > 0:
        st.sidebar.markdown(
            f"**AI 분석:** 총 {ai_counts['total']}개  \n"
            f"🟢 {ai_counts['STRONG_APPROVE']} | "
            f"🟡 {ai_counts['WATCH_MORE']} | "
            f"🔴 {ai_counts['DO_NOT_APPROVE']}"
        )
    else:
        st.sidebar.markdown("**AI 분석:** 없음")

    # 거래 현황
    st.sidebar.markdown(
        f"**거래 현황:**  \n"
        f"✅ Approved: {pool_counts['approved']}  \n"
        f"💰 Trading: {pool_counts['trading']}  \n"
        f"✔️ Completed: {pool_counts['completed']}"
    )

    # 후보 종목
    st.sidebar.markdown(f"**후보 종목:** {pool_counts['monitoring']}개")

    st.sidebar.divider()
    st.sidebar.caption("⏰ **Auto Update:** Weekdays 15:20")
    st.sidebar.caption("🤖 **AI Engine:** Gemini 2.5 Flash")


def get_page_badge(page_name):
    """특정 페이지의 배지 텍스트 반환"""
    pool_counts = get_stock_pool_counts()
    ai_counts = get_ai_reports_counts()

    badges = {
        'stock_pool': f"👀 {pool_counts['monitoring']}",
        'monitoring': f"✅ {pool_counts['approved']}",
        'ai_reports': f"🟢 {ai_counts['STRONG_APPROVE']} 🟡 {ai_counts['WATCH_MORE']}",
        'trading': f"💰 {pool_counts['trading']} ⚠️ {pool_counts['approved']}"
    }

    return badges.get(page_name, "")
