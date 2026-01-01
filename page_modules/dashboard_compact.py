#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📊 Dashboard - Compact Trading View
초고밀도 정보 표시 / 스크롤 없는 대시보드
"""
import streamlit as st
import pandas as pd
from db_config import get_db_connection
from datetime import datetime
from market_utils import is_trading_day, get_next_trading_day


# ============================================================================
# Data Functions
# ============================================================================

@st.cache_data(ttl=30)
def get_all_data():
    """모든 데이터를 한 번에 조회"""
    with get_db_connection() as conn:
        cur = conn.cursor()

        # Stock Pool 상태별
        cur.execute("""
            SELECT status, COUNT(*) as count
            FROM stock_pool
            GROUP BY status
        """)
        pool_stats = dict(cur.fetchall())

        # AI Reports
        cur.execute("""
            SELECT
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE recommendation = 'STRONG_APPROVE') as strong
            FROM ai_analysis_reports
            WHERE report_date >= CURRENT_DATE - INTERVAL '7 days'
        """)
        ai_stats = cur.fetchone()

        # 최근 업데이트
        cur.execute("""
            SELECT MAX(added_date)
            FROM stock_pool
            WHERE status = 'monitoring'
        """)
        last_update = cur.fetchone()[0]

        # AI Score 분포
        cur.execute("""
            SELECT
                CASE
                    WHEN final_score >= 80 THEN 'high'
                    WHEN final_score >= 60 THEN 'mid'
                    ELSE 'low'
                END as range,
                COUNT(*) as count
            FROM stock_pool
            WHERE status = 'monitoring'
            GROUP BY range
        """)
        score_dist = dict(cur.fetchall())

        # Top AI 추천 (간략)
        cur.execute("""
            SELECT
                a.ticker,
                COALESCE(s.final_score, 0) as score
            FROM ai_analysis_reports a
            LEFT JOIN (
                SELECT DISTINCT ON (ticker) ticker, final_score
                FROM stock_pool
                ORDER BY ticker, added_date DESC
            ) s ON a.ticker = s.ticker
            WHERE a.recommendation = 'STRONG_APPROVE'
              AND a.report_date >= CURRENT_DATE - INTERVAL '7 days'
            ORDER BY COALESCE(s.final_score, 0) DESC
            LIMIT 5
        """)
        top_stocks = cur.fetchall()

    return {
        'pool': pool_stats.get('monitoring', 0),
        'approved': pool_stats.get('approved', 0),
        'trading': pool_stats.get('trading', 0),
        'ai_total': ai_stats[0] if ai_stats else 0,
        'ai_strong': ai_stats[1] if ai_stats else 0,
        'last_update': last_update,
        'score_high': score_dist.get('high', 0),
        'score_mid': score_dist.get('mid', 0),
        'score_low': score_dist.get('low', 0),
        'top_stocks': top_stocks
    }


# ============================================================================
# Render
# ============================================================================

def render():
    """초고밀도 Dashboard"""

    # 데이터 로드
    data = get_all_data()

    # ========== 헤더 (한 줄) ==========
    last_update_str = data['last_update'].strftime('%H:%M') if data['last_update'] else 'N/A'

    # 거래일 체크
    is_trading, reason = is_trading_day()
    if is_trading:
        market_status = "🟢 거래일"
    else:
        next_trading = get_next_trading_day()
        next_str = next_trading.strftime('%m/%d') if next_trading else 'N/A'
        market_status = f"🔴 {reason} | 다음 거래일: {next_str}"

    st.markdown(f"""
    ### 🚀 StockGravity | AI: Gemini 2.5 | Updated: {last_update_str} | {market_status}
    """)

    st.divider()

    # ========== KPI (한 줄 텍스트 블록) ==========
    st.markdown(f"""
    **📦 Pool {data['pool']}** | **🤖 AI {data['ai_total']} (🟢{data['ai_strong']})** | **✅ Approval {data['approved']}** | **💼 Trading {data['trading']}**
    """)

    st.divider()

    # ========== Workflow (한 줄 체인) ==========
    # 동적 상태 결정
    pool_icon = '🟢' if data['pool'] > 0 else '⚪'
    ai_icon = '⏳' if data['ai_total'] > 0 else '⚪'
    approval_icon = '🟡' if data['approved'] > 0 else '⚪'
    trade_icon = '🟢' if data['trading'] > 0 else '⚪'

    st.markdown(f"""
    **Filter 🟢2790** → **Pool {pool_icon}{data['pool']}** → **AI {ai_icon}{data['ai_total']}** → **Approval {approval_icon}{data['approved']}** → **Trade {trade_icon}{data['trading']}**
    """)

    st.divider()

    # ========== 3-Column Compact Layout ==========
    col1, col2, col3 = st.columns(3)

    # --- Column 1: Action Needed ---
    with col1:
        st.markdown("### ⚡ Action")

        if data['ai_strong'] > 0:
            st.markdown(f"📄 **{data['ai_strong']} AI Reports** need review")

        if data['approved'] >= 3:
            st.markdown(f"🔄 **{data['approved']} Stocks** need re-eval")

        if data['trading'] > 0:
            st.markdown(f"💰 **{data['trading']} Trades** active")

        if data['ai_strong'] == 0 and data['approved'] < 3 and data['trading'] == 0:
            st.markdown("✅ All clear")

    # --- Column 2: Status Distribution ---
    with col2:
        st.markdown("### 📊 Status")

        total = data['pool'] + data['approved'] + data['trading']
        if total > 0:
            mon_pct = (data['pool'] / total * 100)
            app_pct = (data['approved'] / total * 100)
            trd_pct = (data['trading'] / total * 100)

            st.markdown(f"Monitoring: **{mon_pct:.0f}%** ({data['pool']})")
            st.markdown(f"Approved: **{app_pct:.0f}%** ({data['approved']})")
            st.markdown(f"Trading: **{trd_pct:.0f}%** ({data['trading']})")
        else:
            st.markdown("No data")

    # --- Column 3: AI Score Range ---
    with col3:
        st.markdown("### 🎯 AI Score")

        st.markdown(f"High (80+): **{data['score_high']}**")
        st.markdown(f"Mid (60-79): **{data['score_mid']}**")
        st.markdown(f"Low (40-59): **{data['score_low']}**")

    st.divider()

    # ========== Top AI Picks (한 줄 리스트) ==========
    st.markdown("### 🌟 Top AI Picks")

    if data['top_stocks']:
        top_list = " | ".join([f"**{ticker}** ({score:.0f})" for ticker, score in data['top_stocks']])
        st.markdown(top_list)
    else:
        st.markdown("No recommendations")

    st.divider()

    # ========== Quick Actions (한 줄) ==========
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("📦 Stock Pool", use_container_width=True):
            st.switch_page("pages/1_📦_Stock_Pool.py")

    with col2:
        if st.button("🤖 AI Reports", use_container_width=True, type="primary"):
            st.switch_page("pages/2_🤖_AI_Reports.py")

    with col3:
        if st.button("✅ Trading", use_container_width=True):
            st.switch_page("pages/3_✅_Trading.py")

    with col4:
        if st.button("🔄 Refresh", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
