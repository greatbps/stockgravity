#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🏅 Approval Badge Logic
승인 추천 배지 로직
"""
import pandas as pd


def get_approval_badge(stock, rsi=None, ai_report=None):
    """
    승인 추천 배지 계산

    Args:
        stock: 종목 정보 (dict or Series)
        rsi: 최근 RSI 값 (float or None)
        ai_report: AI 리포트 (dict/Series or None)

    Returns:
        tuple: (badge_name, icon, score)
    """
    score = 0

    # =============================
    # 1. Final Score (점수 기반)
    # =============================
    final_score = stock.get('final_score', 0)

    if final_score >= 85:
        score += 2
    elif final_score >= 75:
        score += 1

    # =============================
    # 2. Momentum (모멘텀)
    # =============================
    change_5d = stock.get('change_5d', 0)
    vol_ratio = stock.get('vol_ratio', 0)

    if change_5d > 3:
        score += 1

    if vol_ratio > 1.2:
        score += 1

    # =============================
    # 3. RSI (기술적 지표)
    # =============================
    if rsi is not None and pd.notna(rsi):
        if 45 <= rsi <= 65:
            score += 1  # 적정 범위
        elif rsi > 70:
            score -= 1  # 과열 구간

    # =============================
    # 4. AI Recommendation
    # =============================
    if ai_report is not None and not (isinstance(ai_report, pd.DataFrame) and ai_report.empty):
        if isinstance(ai_report, pd.DataFrame):
            ai_report = ai_report.iloc[0]

        rec = ai_report.get('recommendation', '')
        conf = ai_report.get('confidence_score', 0)

        if rec == 'BUY' and conf >= 0.75:
            score += 2
        elif rec == 'BUY':
            score += 1
        elif rec == 'SELL':
            score -= 2

    # =============================
    # Final Decision
    # =============================
    if score >= 5:
        return "STRONG_APPROVE", "🟢", score
    elif score >= 3:
        return "WATCH_MORE", "🟡", score
    else:
        return "DO_NOT_APPROVE", "🔴", score


def get_badge_style(badge_name):
    """배지 스타일 반환"""
    styles = {
        "STRONG_APPROVE": {
            "bg": "#10b981",  # green
            "text": "#ffffff"
        },
        "WATCH_MORE": {
            "bg": "#f59e0b",  # yellow/orange
            "text": "#000000"
        },
        "DO_NOT_APPROVE": {
            "bg": "#ef4444",  # red
            "text": "#ffffff"
        }
    }
    return styles.get(badge_name, {"bg": "#6b7280", "text": "#ffffff"})


def render_badge_html(badge_name, icon, score):
    """배지 HTML 렌더링"""
    style = get_badge_style(badge_name)

    return f"""
    <div style="
        padding: 12px 20px;
        border-radius: 8px;
        font-weight: 600;
        background-color: {style['bg']};
        color: {style['text']};
        display: inline-block;
        margin: 10px 0;
        font-size: 16px;
    ">
        {icon} Approval Recommendation: <b>{badge_name.replace('_', ' ')}</b>
        &nbsp;&nbsp;|&nbsp;&nbsp;Score: {score}
    </div>
    """


def should_enable_approval(badge_name):
    """승인 버튼 활성화 여부"""
    # DO_NOT_APPROVE는 승인 버튼 비활성화
    return badge_name != "DO_NOT_APPROVE"


def get_badge_explanation(badge_name, score):
    """배지 설명 반환"""
    explanations = {
        "STRONG_APPROVE": f"✅ 종합 점수 {score}점으로 승인 강력 추천합니다. 모든 지표가 긍정적입니다.",
        "WATCH_MORE": f"⏳ 종합 점수 {score}점으로 1~2일 더 관찰을 권장합니다. 지표가 엇갈립니다.",
        "DO_NOT_APPROVE": f"⛔ 종합 점수 {score}점으로 현재 승인을 권장하지 않습니다. 조건 미달입니다."
    }
    return explanations.get(badge_name, "")
