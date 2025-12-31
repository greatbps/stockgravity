#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📊 Dashboard - v0 Design
KPI Cards + Workflow Progress + Action Items
"""
import streamlit as st
import pandas as pd
from db_config import get_db_connection
from datetime import datetime


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
                COUNT(*) FILTER (WHERE recommendation = 'STRONG_APPROVE') as strong_approve,
                COUNT(*) FILTER (WHERE recommendation = 'WATCH_MORE') as watch_more,
                COUNT(*) FILTER (WHERE recommendation = 'DO_NOT_APPROVE') as do_not_approve
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
        'ai_watch': ai_stats[2] if ai_stats else 0,
        'ai_reject': ai_stats[3] if ai_stats else 0,
        'last_update': last_update
    }


@st.cache_data(ttl=30)
def get_workflow_status():
    """워크플로우 상태 조회"""
    with get_db_connection() as conn:
        cur = conn.cursor()

        # 각 단계별 카운트
        cur.execute("SELECT COUNT(*) FROM stock_pool WHERE status = 'monitoring'")
        pool_count = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM ai_analysis_reports WHERE report_date >= CURRENT_DATE - INTERVAL '7 days'")
        ai_count = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM stock_pool WHERE status = 'approved'")
        approval_count = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM stock_pool WHERE status = 'trading'")
        trading_count = cur.fetchone()[0]

    return {
        'filter': 2790,  # 전체 종목 수 (고정값)
        'pool': pool_count,
        'ai_analysis': ai_count,
        'approval': approval_count,
        'trading': trading_count
    }


@st.cache_data(ttl=30)
def get_action_items():
    """액션 아이템 조회"""
    actions = []

    with get_db_connection() as conn:
        cur = conn.cursor()

        # 1. AI Reports 검토 필요
        cur.execute("""
            SELECT COUNT(*)
            FROM ai_analysis_reports a
            LEFT JOIN stock_pool s ON a.ticker = s.ticker
            WHERE a.recommendation = 'STRONG_APPROVE'
              AND COALESCE(s.status, 'monitoring') = 'monitoring'
              AND a.report_date >= CURRENT_DATE - INTERVAL '7 days'
        """)
        review_count = cur.fetchone()[0]

        if review_count > 0:
            actions.append({
                'type': 'review',
                'title': f'{review_count} AI Reports need review',
                'description': 'Top stocks analyzed, awaiting approval decision',
                'priority': 'high',
                'icon': '📄'
            })

        # 2. 재평가 필요 (3일 이상 경과)
        cur.execute("""
            SELECT COUNT(*)
            FROM stock_pool
            WHERE status = 'approved'
              AND approved_date < CURRENT_DATE - INTERVAL '3 days'
        """)
        reeval_count = cur.fetchone()[0]

        if reeval_count > 0:
            actions.append({
                'type': 'reevaluate',
                'title': f'{reeval_count} Stocks need re-evaluation',
                'description': 'Stocks held for 3+ days require review',
                'priority': 'medium',
                'icon': '🔄'
            })

        # 3. 활성 거래 모니터링
        cur.execute("""
            SELECT COUNT(*)
            FROM stock_pool
            WHERE status = 'trading'
        """)
        trading_count = cur.fetchone()[0]

        if trading_count > 0:
            actions.append({
                'type': 'monitor',
                'title': f'{trading_count} Active trades to monitor',
                'description': 'Review real-time positions and P/L',
                'priority': 'high',
                'icon': '💰'
            })

    return actions


@st.cache_data(ttl=60)
def get_recent_ai_reports(limit=5):
    """최근 AI 추천 종목"""
    query = """
        SELECT
            a.ticker,
            COALESCE(s.name, a.ticker) as name,
            COALESCE(s.final_score, 0) as final_score,
            COALESCE(s.status, 'unknown') as stock_status,
            a.recommendation,
            a.confidence_score,
            a.summary
        FROM ai_analysis_reports a
        LEFT JOIN (
            SELECT DISTINCT ON (ticker) ticker, name, final_score, status
            FROM stock_pool
            ORDER BY ticker, added_date DESC
        ) s ON a.ticker = s.ticker
        WHERE a.recommendation = 'STRONG_APPROVE'
          AND a.report_date >= CURRENT_DATE - INTERVAL '7 days'
        ORDER BY COALESCE(s.final_score, 0) DESC
        LIMIT %s
    """

    with get_db_connection() as conn:
        df = pd.read_sql(query, conn, params=(limit,))
    return df


def render_kpi_card(title, value, icon, trend=None, variant='default'):
    """KPI 카드 렌더링"""
    variant_styles = {
        'default': 'border: 2px solid #e5e5e5;',
        'success': 'border: 2px solid rgba(101, 161, 80, 0.3); background: rgba(101, 161, 80, 0.05);',
        'warning': 'border: 2px solid rgba(197, 169, 64, 0.3); background: rgba(197, 169, 64, 0.05);',
        'info': 'border: 2px solid rgba(77, 143, 199, 0.3); background: rgba(77, 143, 199, 0.05);',
    }

    icon_bg_colors = {
        'default': '#f5f5f5',
        'success': 'rgba(101, 161, 80, 0.2)',
        'warning': 'rgba(197, 169, 64, 0.2)',
        'info': 'rgba(77, 143, 199, 0.2)',
    }

    icon_colors = {
        'default': '#262626',
        'success': '#65A150',
        'warning': '#C5A940',
        'info': '#4D8FC7',
    }

    trend_html = ''
    if trend:
        trend_color = '#65A150' if trend['positive'] else '#C75545'
        trend_html = f'<p style="margin: 0.25rem 0 0 0; font-size: 0.75rem; color: {trend_color};">{trend["value"]}</p>'

    html = f"""
    <div style="{variant_styles[variant]} border-radius: 0.5rem; padding: 1.5rem; background: white;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <p style="margin: 0; font-size: 0.875rem; color: #737373; font-weight: 500;">{title}</p>
                <p style="margin: 0.5rem 0 0 0; font-size: 2rem; font-weight: bold; color: #262626;">{value}</p>
                {trend_html}
            </div>
            <div style="display: flex; align-items: center; justify-content: center;
                        width: 3rem; height: 3rem; border-radius: 0.5rem;
                        background: {icon_bg_colors[variant]}; font-size: 1.5rem;">
                {icon}
            </div>
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def render_workflow_progress(workflow_data):
    """워크플로우 진행 상황"""
    steps = [
        {'name': 'Filter', 'count': workflow_data['filter'], 'status': 'complete'},
        {'name': 'Pool', 'count': workflow_data['pool'], 'status': 'complete'},
        {'name': 'AI Analysis', 'count': workflow_data['ai_analysis'], 'status': 'active'},
        {'name': 'Approval', 'count': workflow_data['approval'], 'status': 'pending'},
        {'name': 'Trading', 'count': workflow_data['trading'], 'status': 'pending'},
    ]

    html = '<div style="padding: 1.5rem; background: white; border: 1px solid #e5e5e5; border-radius: 0.5rem;">'
    html += '<h3 style="margin: 0 0 1.5rem 0; font-size: 1rem; font-weight: 600;">Workflow Progress</h3>'
    html += '<div style="display: flex; justify-content: space-between; align-items: center;">'

    for i, step in enumerate(steps):
        # 상태별 색상
        if step['status'] == 'complete':
            circle_color = '#65A150'
            icon = '✓'
            line_color = '#65A150'
        elif step['status'] == 'active':
            circle_color = '#C5A940'
            icon = '●'
            line_color = '#e5e5e5'
        else:
            circle_color = '#e5e5e5'
            icon = '○'
            line_color = '#e5e5e5'

        html += '<div style="flex: 1; display: flex; align-items: center;">'
        html += '<div style="display: flex; flex-direction: column; align-items: center; flex: 1;">'

        # Circle
        html += f'<div style="width: 2.5rem; height: 2.5rem; border-radius: 50%; border: 2px solid {circle_color}; display: flex; align-items: center; justify-content: center; background: white; font-weight: bold; color: {circle_color};">{icon}</div>'

        # Label
        html += f'<p style="margin: 0.5rem 0 0 0; font-size: 0.75rem; font-weight: 600; text-align: center;">{step["name"]}</p>'
        html += f'<p style="margin: 0.25rem 0 0 0; font-size: 0.75rem; color: #737373; text-align: center;">{step["count"]}</p>'

        html += '</div>'

        # Connector line
        if i < len(steps) - 1:
            html += f'<div style="height: 2px; flex: 1; background: {line_color}; margin: 0 0.5rem 2rem 0.5rem;"></div>'

        html += '</div>'

    html += '</div></div>'

    st.markdown(html, unsafe_allow_html=True)


def render_action_items(actions):
    """액션 아이템 렌더링"""
    if not actions:
        st.info("✅ No pending actions - all caught up!")
        return

    st.markdown('<div style="background: white; border: 1px solid #e5e5e5; border-radius: 0.5rem; padding: 1.5rem;">', unsafe_allow_html=True)
    st.markdown('<h3 style="margin: 0 0 1rem 0; font-size: 1.125rem; font-weight: 600;">Action Needed</h3>', unsafe_allow_html=True)

    for action in actions:
        priority_color = '#C5A940' if action['priority'] == 'high' else '#4D8FC7'
        priority_bg = 'rgba(197, 169, 64, 0.1)' if action['priority'] == 'high' else 'rgba(77, 143, 199, 0.1)'

        html = f"""
        <div style="display: flex; justify-content: space-between; align-items: start; gap: 1rem;
                    padding: 1rem; border: 1px solid #e5e5e5; border-radius: 0.5rem; margin-bottom: 0.75rem;">
            <div style="display: flex; gap: 0.75rem; flex: 1;">
                <div style="width: 2.5rem; height: 2.5rem; border-radius: 0.5rem; background: {priority_bg};
                            display: flex; align-items: center; justify-content: center; font-size: 1.25rem;">
                    {action['icon']}
                </div>
                <div style="flex: 1;">
                    <div style="display: flex; gap: 0.5rem; align-items: center; margin-bottom: 0.25rem;">
                        <h4 style="margin: 0; font-size: 0.875rem; font-weight: 600;">{action['title']}</h4>
                        {f'<span style="padding: 0.125rem 0.5rem; background: #C75545; color: white; border-radius: 0.25rem; font-size: 0.625rem; font-weight: 600;">HIGH PRIORITY</span>' if action['priority'] == 'high' else ''}
                    </div>
                    <p style="margin: 0; font-size: 0.75rem; color: #737373;">{action['description']}</p>
                </div>
            </div>
        </div>
        """
        st.markdown(html, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)


def render():
    """메인 렌더 함수"""
    # CSS 로드
    try:
        with open('/home/greatbps/projects/stockgravity/styles/v0_theme.css', 'r') as f:
            css = f.read()
        st.markdown(f'<style>{css}</style>', unsafe_allow_html=True)
    except:
        pass

    st.title("📊 StockGravity Dashboard")
    st.caption("Korean Stock Filtering & AI Trading System")

    # 데이터 로드
    kpi_data = get_kpi_data()
    workflow_data = get_workflow_status()
    actions = get_action_items()
    recent_reports = get_recent_ai_reports(5)

    # AI Engine 상태
    st.markdown("""
    <div style="padding: 0.75rem 1rem; background: rgba(101, 161, 80, 0.1); border: 1px solid rgba(101, 161, 80, 0.3);
                border-radius: 0.5rem; margin-bottom: 1.5rem; display: flex; align-items: center; gap: 0.5rem;">
        <div style="width: 0.5rem; height: 0.5rem; border-radius: 50%; background: #65A150; animation: pulse 2s infinite;"></div>
        <span style="font-weight: 600; font-size: 0.875rem;">AI Engine Active</span>
        <span style="color: #737373; font-size: 0.875rem; margin-left: auto;">Gemini 2.5 Flash • Last update: {}</span>
    </div>
    """.format(kpi_data['last_update'].strftime('%Y-%m-%d %H:%M') if kpi_data['last_update'] else 'N/A'), unsafe_allow_html=True)

    # KPI Cards
    st.markdown("### 📈 Key Metrics")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        render_kpi_card(
            "Pool Size",
            kpi_data['pool_size'],
            "📦",
            variant='default'
        )

    with col2:
        render_kpi_card(
            "AI Reports",
            kpi_data['ai_total'],
            "🤖",
            trend={'value': f"{kpi_data['ai_strong']} Strong Approve", 'positive': True},
            variant='info'
        )

    with col3:
        render_kpi_card(
            "Approved",
            kpi_data['approved'],
            "✅",
            variant='success'
        )

    with col4:
        render_kpi_card(
            "Active Trades",
            kpi_data['trading'],
            "💰",
            variant='warning'
        )

    st.markdown("<div style='margin: 2rem 0;'></div>", unsafe_allow_html=True)

    # Workflow Progress
    st.markdown("### 🔄 Pipeline Status")
    render_workflow_progress(workflow_data)

    st.markdown("<div style='margin: 2rem 0;'></div>", unsafe_allow_html=True)

    # 2 Columns: Action Items + Recent Reports
    col_left, col_right = st.columns([1, 1])

    with col_left:
        st.markdown("### ⚡ Action Items")
        render_action_items(actions)

    with col_right:
        st.markdown("### 🌟 Top AI Recommendations")

        if len(recent_reports) > 0:
            st.markdown('<div style="background: white; border: 1px solid #e5e5e5; border-radius: 0.5rem; padding: 1.5rem;">', unsafe_allow_html=True)

            for _, report in recent_reports.iterrows():
                status_color = {
                    'monitoring': '#737373',
                    'approved': '#65A150',
                    'trading': '#C5A940'
                }.get(report['stock_status'], '#737373')

                html = f"""
                <div style="padding: 0.75rem; border: 1px solid #e5e5e5; border-radius: 0.5rem; margin-bottom: 0.75rem;">
                    <div style="display: flex; justify-content: space-between; align-items: start;">
                        <div>
                            <div style="display: flex; gap: 0.5rem; align-items: center;">
                                <span style="font-family: monospace; font-weight: 600; font-size: 0.875rem;">{report['ticker']}</span>
                                <span style="background: #65A150; color: white; padding: 0.125rem 0.5rem; border-radius: 0.25rem; font-size: 0.625rem; font-weight: 600;">STRONG APPROVE</span>
                            </div>
                            <p style="margin: 0.25rem 0 0 0; font-size: 0.875rem; color: #737373;">{report['name']}</p>
                        </div>
                        <div style="text-align: right;">
                            <div style="font-family: monospace; font-weight: 700; font-size: 1.25rem;">{report['final_score']:.0f}</div>
                            <div style="font-size: 0.625rem; color: #737373;">{report['confidence_score']:.0f}% conf</div>
                        </div>
                    </div>
                    <p style="margin: 0.5rem 0 0 0; font-size: 0.75rem; color: #737373;
                              overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                        {report['summary'][:80] if pd.notna(report['summary']) else 'No summary'}...
                    </p>
                    <div style="margin-top: 0.5rem; font-size: 0.75rem;">
                        <span style="color: {status_color}; font-weight: 600;">● {report['stock_status'].upper()}</span>
                    </div>
                </div>
                """
                st.markdown(html, unsafe_allow_html=True)

            st.markdown('</div>', unsafe_allow_html=True)

            if st.button("→ View All AI Reports", use_container_width=True):
                st.switch_page("pages/2_🤖_AI_Reports.py")
        else:
            st.info("No AI reports available. Run analysis to generate reports.")

    st.markdown("<div style='margin: 2rem 0;'></div>", unsafe_allow_html=True)

    # Quick Links
    st.markdown("### 🚀 Quick Actions")
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("📦 View Stock Pool", use_container_width=True, type="secondary"):
            st.switch_page("pages/1_📦_Stock_Pool.py")

    with col2:
        if st.button("🤖 Review AI Reports", use_container_width=True, type="primary"):
            st.switch_page("pages/2_🤖_AI_Reports.py")

    with col3:
        if st.button("✅ Manage Trading", use_container_width=True, type="secondary"):
            st.switch_page("pages/3_✅_Trading.py")
