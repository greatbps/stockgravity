#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dashboard Skeleton - V0 Design
레이아웃 구조와 정보 계층에 집중
"""
import streamlit as st
import pandas as pd

# ============================================================================
# Data Functions (Mock - 실제 DB 연결로 교체 필요)
# ============================================================================

def get_kpi_data():
    """KPI 메트릭 데이터 조회"""
    return {
        'pool_size': 500,
        'ai_reports': 20,
        'approval_queue': 5,
        'active_trades': 8,
        'active_trades_pnl': '+16.5%'
    }

def get_workflow_status():
    """5단계 워크플로우 상태"""
    return [
        {'step': 'Filter', 'count': '2,790', 'status': 'complete'},
        {'step': 'Pool', 'count': '500', 'status': 'complete'},
        {'step': 'AI Analysis', 'count': '20', 'status': 'active'},
        {'step': 'Approval', 'count': '5', 'status': 'pending'},
        {'step': 'Trading', 'count': '8', 'status': 'pending'},
    ]

def get_action_items():
    """액션 필요 항목 리스트"""
    return [
        {
            'icon': '📄',
            'title': '5 AI Reports need review',
            'description': 'Top 20 stocks analyzed, awaiting approval decision',
            'priority': 'High Priority',
            'page': 'ai-reports'
        },
        {
            'icon': '🔄',
            'title': '3 Stocks need re-evaluation',
            'description': 'Price movement triggers requiring attention',
            'priority': None,
            'page': 'approval-queue'
        },
        {
            'icon': '⚠️',
            'title': '2 Active trades approaching stop-loss',
            'description': 'Monitor positions: Samsung Electronics, NAVER',
            'priority': 'High Priority',
            'page': 'active-trades'
        },
    ]

def get_status_distribution():
    """상태별 분포"""
    return {
        'Approved': 40,
        'Monitoring': 35,
        'Pending': 25
    }

def get_ai_score_range():
    """AI 점수 범위별 분포"""
    return {
        'High (80-100)': 8,
        'Medium (60-79)': 7,
        'Low (40-59)': 5
    }


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
            value=f"{kpi_data['ai_reports']}",
            help="AI analysis reports generated today"
        )

    with col3:
        st.metric(
            label="✅ Approval Queue",
            value=f"{kpi_data['approval_queue']}",
            delta="from yesterday",
            help="Stocks awaiting approval for trading"
        )

    with col4:
        st.metric(
            label="💰 Active Trades",
            value=f"{kpi_data['active_trades']}",
            delta=kpi_data['active_trades_pnl'],
            delta_color="normal",
            help="Currently open positions"
        )


def render_workflow_progress(workflow_status):
    """5단계 워크플로우 진행 상태"""
    st.subheader("🔄 Workflow Progress")

    # 5개 컬럼으로 단계 표시
    cols = st.columns(5)

    for idx, step_data in enumerate(workflow_status):
        with cols[idx]:
            # 상태에 따른 아이콘
            if step_data['status'] == 'complete':
                icon = '✅'
            elif step_data['status'] == 'active':
                icon = '⏳'
            else:
                icon = '○'

            st.markdown(f"### {icon}")
            st.markdown(f"**{step_data['step']}**")
            st.caption(f"{step_data['count']}")


def render_action_items(action_items):
    """액션 필요 항목 리스트"""
    st.subheader("⚡ Action Needed")

    for item in action_items:
        # 우선순위 배지가 있으면 warning, 없으면 info
        if item['priority']:
            with st.container():
                col1, col2 = st.columns([5, 1])
                with col1:
                    st.warning(
                        f"{item['icon']} **{item['title']}** `{item['priority']}`\n\n"
                        f"{item['description']}",
                        icon=item['icon']
                    )
                with col2:
                    st.button("View", key=f"action_{item['page']}", use_container_width=True)
        else:
            with st.container():
                col1, col2 = st.columns([5, 1])
                with col1:
                    st.info(
                        f"{item['icon']} **{item['title']}**\n\n"
                        f"{item['description']}",
                        icon=item['icon']
                    )
                with col2:
                    st.button("View", key=f"action_{item['page']}", use_container_width=True)


def render_status_distribution(status_dist, score_range):
    """상태 분포 및 AI 점수 범위"""
    st.subheader("📊 Status Distribution")

    # 상태별 분포 (Progress bars로 시각화)
    st.markdown("**Stock Status**")
    for status, percentage in status_dist.items():
        st.markdown(f"{status}")
        st.progress(percentage / 100)
        st.caption(f"{percentage}%")

    st.divider()

    # AI 점수 범위
    st.markdown("**AI Score Range**")
    for score_range_label, count in score_range.items():
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"{score_range_label}")
        with col2:
            st.markdown(f"**{count}** stocks")


# ============================================================================
# Main Render
# ============================================================================

def render():
    """메인 Dashboard 렌더링"""

    # Page Header
    st.title("📊 Dashboard")
    st.caption("System overview and next actions")

    st.divider()

    # 1. KPI Cards (4-column)
    kpi_data = get_kpi_data()
    render_kpi_cards(kpi_data)

    st.divider()

    # 2. Workflow Progress (5-step pipeline)
    workflow_status = get_workflow_status()
    render_workflow_progress(workflow_status)

    st.divider()

    # 3. Two-column layout: Action Needed + Status Distribution
    col_left, col_right = st.columns([2, 1])

    with col_left:
        action_items = get_action_items()
        render_action_items(action_items)

    with col_right:
        status_dist = get_status_distribution()
        score_range = get_ai_score_range()
        render_status_distribution(status_dist, score_range)


# ============================================================================
# 테스트 실행
# ============================================================================

if __name__ == "__main__":
    st.set_page_config(
        page_title="Dashboard - StockGravity",
        page_icon="📊",
        layout="wide"
    )
    render()
