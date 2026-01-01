#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📊 Dashboard - V0 Design (Final)
실제 DB 데이터 + V0 레이아웃 구조
"""
import streamlit as st
import pandas as pd
from db_config import get_db_connection
from datetime import datetime


# ============================================================================
# Data Functions (Real DB)
# ============================================================================

@st.cache_data(ttl=30)
def get_kpi_data():
    """KPI 데이터 조회"""
    with get_db_connection() as conn:
        cur = conn.cursor()

        # Stock Pool 상태별 카운트
        cur.execute("""
            SELECT status, COUNT(*) as count
            FROM stock_pool
            GROUP BY status
        """)
        pool_stats = dict(cur.fetchall())

        # AI Reports 카운트
        cur.execute("""
            SELECT
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE recommendation = 'STRONG_APPROVE') as strong_approve
            FROM ai_analysis_reports
            WHERE report_date >= CURRENT_DATE - INTERVAL '7 days'
        """)
        ai_stats = cur.fetchone()

        # 최근 업데이트 시간
        cur.execute("""
            SELECT MAX(added_date)
            FROM stock_pool
            WHERE status = 'monitoring'
        """)
        last_update = cur.fetchone()[0]

    return {
        'pool_size': pool_stats.get('monitoring', 0),
        'approved': pool_stats.get('approved', 0),
        'trading': pool_stats.get('trading', 0),
        'completed': pool_stats.get('completed', 0),
        'ai_total': ai_stats[0] if ai_stats else 0,
        'ai_strong': ai_stats[1] if ai_stats else 0,
        'last_update': last_update,
        'pool_stats': pool_stats  # 전체 통계
    }


@st.cache_data(ttl=60)
def get_status_distribution():
    """상태별 분포 (백분율)"""
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT status, COUNT(*) as count
            FROM stock_pool
            GROUP BY status
        """)
        results = cur.fetchall()

    total = sum([count for _, count in results])
    if total == 0:
        return {}

    distribution = {}
    for status, count in results:
        percentage = (count / total) * 100
        distribution[status] = {
            'count': count,
            'percentage': percentage
        }

    return distribution


@st.cache_data(ttl=60)
def get_ai_score_range():
    """AI 점수 범위별 분포"""
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT
                CASE
                    WHEN final_score >= 80 THEN 'High (80-100)'
                    WHEN final_score >= 60 THEN 'Medium (60-79)'
                    ELSE 'Low (40-59)'
                END as score_range,
                COUNT(*) as count
            FROM stock_pool
            WHERE status = 'monitoring'
            GROUP BY score_range
            ORDER BY score_range DESC
        """)
        results = cur.fetchall()

    return {score_range: count for score_range, count in results}


def get_workflow_status(kpi_data):
    """워크플로우 각 단계의 상태 동적 판단"""
    steps = []

    # 1. Filter (항상 완료)
    steps.append({
        'name': 'Filter',
        'icon': '✅',
        'status': 'Complete',
        'count': '2,790'
    })

    # 2. Pool (monitoring이 있으면 완료)
    if kpi_data['pool_size'] > 0:
        icon = '✅'
        status = 'Complete'
    else:
        icon = '○'
        status = 'Pending'

    steps.append({
        'name': 'Pool',
        'icon': icon,
        'status': status,
        'count': f"{kpi_data['pool_size']}"
    })

    # 3. AI Analysis (AI 리포트가 있으면 활성)
    if kpi_data['ai_total'] > 0:
        icon = '⏳'
        status = 'Active'
    else:
        icon = '○'
        status = 'Pending'

    steps.append({
        'name': 'AI Analysis',
        'icon': icon,
        'status': status,
        'count': f"{kpi_data['ai_total']}"
    })

    # 4. Approval (승인 대기가 있으면 대기)
    if kpi_data['approved'] > 0:
        icon = '⏳'
        status = 'Pending'
    else:
        icon = '○'
        status = 'Idle'

    steps.append({
        'name': 'Approval',
        'icon': icon,
        'status': status,
        'count': f"{kpi_data['approved']}"
    })

    # 5. Trading (활성 거래가 있으면 활성)
    if kpi_data['trading'] > 0:
        icon = '⏳'
        status = 'Active'
    else:
        icon = '○'
        status = 'Idle'

    steps.append({
        'name': 'Trading',
        'icon': icon,
        'status': status,
        'count': f"{kpi_data['trading']}"
    })

    return steps


def get_action_items(kpi_data):
    """액션 필요 항목 동적 생성"""
    actions = []

    # AI Reports 검토 필요
    if kpi_data['ai_strong'] > 0:
        actions.append({
            'icon': '📄',
            'title': f"{kpi_data['ai_strong']} AI Reports need review",
            'description': 'Top stocks analyzed, awaiting approval decision',
            'priority': 'High Priority' if kpi_data['ai_strong'] >= 5 else None,
            'page': 'pages/2_🤖_AI_Reports.py'
        })

    # 승인된 종목 재평가
    if kpi_data['approved'] >= 3:
        actions.append({
            'icon': '🔄',
            'title': f"{kpi_data['approved']} Stocks need re-evaluation",
            'description': 'Stocks held for 3+ days require review',
            'priority': None,
            'page': 'pages/2_🤖_AI_Reports.py'
        })

    # 활성 거래 모니터링
    if kpi_data['trading'] > 0:
        actions.append({
            'icon': '💰',
            'title': f"{kpi_data['trading']} Active trades to monitor",
            'description': 'Review real-time positions and P/L',
            'priority': 'High Priority' if kpi_data['trading'] >= 5 else None,
            'page': 'pages/3_✅_Trading.py'
        })

    return actions


# ============================================================================
# Render Functions
# ============================================================================

def render_kpi_cards(kpi_data):
    """KPI 카드 4개 렌더링"""
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="📦 Stock Pool",
            value=f"{kpi_data['pool_size']:,}",
            help="Total stocks in monitoring pool"
        )

    with col2:
        st.metric(
            label="📄 AI Reports Today",
            value=f"{kpi_data['ai_total']}",
            delta=f"{kpi_data['ai_strong']} Strong Approve" if kpi_data['ai_strong'] > 0 else None,
            help="AI analysis reports generated in last 7 days"
        )

    with col3:
        st.metric(
            label="✅ Approval Queue",
            value=f"{kpi_data['approved']:,}",
            help="Stocks awaiting approval for trading"
        )

    with col4:
        st.metric(
            label="💰 Active Trades",
            value=f"{kpi_data['trading']:,}",
            help="Currently open positions"
        )


def render_workflow_progress(workflow_steps):
    """5단계 워크플로우 진행 상태"""
    st.subheader("🔄 Workflow Progress")

    cols = st.columns(5)

    for idx, step in enumerate(workflow_steps):
        with cols[idx]:
            st.markdown(f"### {step['icon']}")
            st.markdown(f"**{step['name']}**")
            st.caption(f"{step['count']}")


def render_action_items(actions):
    """액션 필요 항목 리스트"""
    st.subheader("⚡ Action Needed")

    if len(actions) == 0:
        st.success("✅ No pending actions - all caught up!")
        return

    for idx, action in enumerate(actions):
        with st.container():
            col1, col2 = st.columns([5, 1])

            with col1:
                if action['priority']:
                    st.warning(
                        f"{action['icon']} **{action['title']}** `{action['priority']}`\n\n"
                        f"{action['description']}",
                        icon=action['icon']
                    )
                else:
                    st.info(
                        f"{action['icon']} **{action['title']}**\n\n"
                        f"{action['description']}",
                        icon=action['icon']
                    )

            with col2:
                if st.button("View", key=f"action_{idx}", use_container_width=True):
                    st.switch_page(action['page'])


def render_status_distribution(status_dist, score_range):
    """상태 분포 및 AI 점수 범위"""
    st.subheader("📊 Status Distribution")

    # 상태별 분포
    st.markdown("**Stock Status**")

    # 주요 상태만 표시
    display_statuses = ['monitoring', 'approved', 'trading']

    for status in display_statuses:
        if status in status_dist:
            data = status_dist[status]
            st.markdown(f"{status.title()}")
            st.progress(data['percentage'] / 100)
            st.caption(f"{data['percentage']:.0f}% ({data['count']} stocks)")
        else:
            st.markdown(f"{status.title()}")
            st.progress(0)
            st.caption("0% (0 stocks)")

    st.divider()

    # AI 점수 범위
    st.markdown("**AI Score Range**")

    if score_range:
        for score_label, count in score_range.items():
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"{score_label}")
            with col2:
                st.markdown(f"**{count}** stocks")
    else:
        st.caption("No score data available")


# ============================================================================
# Main Render
# ============================================================================

def render():
    """메인 Dashboard 렌더링"""

    # Page Header
    st.title("🚀 Dashboard V0 (New Design)")
    st.caption("System overview and next actions • V0 Design with Real Data")

    # 데이터 로드
    kpi_data = get_kpi_data()

    # AI Engine Status
    if kpi_data['last_update']:
        last_update_str = kpi_data['last_update'].strftime('%Y-%m-%d %H:%M')
    else:
        last_update_str = 'N/A'

    st.success(
        f"🤖 **AI Engine Active** • Gemini 2.5 Flash • Last update: {last_update_str}",
        icon="✅"
    )

    st.divider()

    # 1. KPI Cards (4-column)
    render_kpi_cards(kpi_data)

    st.divider()

    # 2. Workflow Progress (5-step pipeline)
    workflow_steps = get_workflow_status(kpi_data)
    render_workflow_progress(workflow_steps)

    st.divider()

    # 3. Two-column layout: Action Needed + Status Distribution
    col_left, col_right = st.columns([2, 1])

    with col_left:
        actions = get_action_items(kpi_data)
        render_action_items(actions)

    with col_right:
        status_dist = get_status_distribution()
        score_range = get_ai_score_range()
        render_status_distribution(status_dist, score_range)

    st.divider()

    # 4. Quick Actions
    st.subheader("🚀 Quick Actions")
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("📦 View Stock Pool", use_container_width=True):
            st.switch_page("pages/1_📦_Stock_Pool.py")

    with col2:
        if st.button("🤖 Review AI Reports", use_container_width=True, type="primary"):
            st.switch_page("pages/2_🤖_AI_Reports.py")

    with col3:
        if st.button("✅ Manage Trading", use_container_width=True):
            st.switch_page("pages/3_✅_Trading.py")
