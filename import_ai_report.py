#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
기존 AI 리포트를 DB로 임포트
"""
import re
from datetime import datetime
from db_config import get_db_connection

def parse_ai_response(analysis_text):
    """AI 분석 결과에서 구조화된 정보 추출"""
    result = {
        'summary': '',
        'recommendation': 'WATCH_MORE',
        'confidence_score': 50.0,
        'momentum_analysis': '',
        'liquidity_analysis': '',
        'risk_factors': ''
    }

    # 요약 의견에서 recommendation 추출
    if '매수' in analysis_text or 'BUY' in analysis_text.upper():
        result['recommendation'] = 'STRONG_APPROVE'
        result['confidence_score'] = 70.0
    elif '관심종목' in analysis_text or 'WATCH' in analysis_text.upper():
        result['recommendation'] = 'WATCH_MORE'
        result['confidence_score'] = 50.0
    elif '보류' in analysis_text or 'HOLD' in analysis_text.upper() or '매도' in analysis_text:
        result['recommendation'] = 'DO_NOT_APPROVE'
        result['confidence_score'] = 30.0

    # 섹션별 내용 추출
    sections = {
        '요약 의견': 'summary',
        '모멘텀 분석': 'momentum_analysis',
        '유동성 분석': 'liquidity_analysis',
        '리스크 요인': 'risk_factors'
    }

    for section_name, field_name in sections.items():
        pattern = f'[*#]*{section_name}[*#]*[:\\s]*(.*?)(?=[*#]*(?:모멘텀 분석|유동성 분석|재료 분석|리스크 요인|투자 전략)|$)'
        match = re.search(pattern, analysis_text, re.DOTALL | re.IGNORECASE)
        if match:
            content = match.group(1).strip()
            content = re.sub(r'[*#]+', '', content).strip()
            result[field_name] = content[:500]

    if not result['summary']:
        result['summary'] = analysis_text[:200].strip()

    return result

def import_report(filename='ai_analysis_report_20251231.md'):
    """마크다운 리포트 파싱 및 DB 저장"""
    print(f"\n📥 {filename} 임포트 중...\n")

    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()

    # 종목별 섹션 분리
    sections = re.split(r'\n## ', content)

    saved_count = 0
    with get_db_connection() as conn:
        cur = conn.cursor()

        for section in sections[1:]:  # 첫 번째는 헤더이므로 스킵
            # 종목명과 티커 추출
            match = re.match(r'(.*?)\s*\((\d{6})\)', section)
            if not match:
                continue

            name = match.group(1).strip()
            ticker = match.group(2)

            # 분석 내용 추출 (종합 점수 다음부터)
            analysis_start = section.find('\n\n')
            if analysis_start == -1:
                continue

            analysis_text = section[analysis_start:].strip()

            # 구조화된 데이터 추출
            analysis_data = parse_ai_response(analysis_text)

            # DB 저장
            try:
                cur.execute("""
                    INSERT INTO ai_analysis_reports
                    (ticker, report_date, summary, recommendation, confidence_score,
                     momentum_analysis, liquidity_analysis, risk_factors)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (ticker, report_date) DO UPDATE SET
                        summary = EXCLUDED.summary,
                        recommendation = EXCLUDED.recommendation,
                        confidence_score = EXCLUDED.confidence_score,
                        momentum_analysis = EXCLUDED.momentum_analysis,
                        liquidity_analysis = EXCLUDED.liquidity_analysis,
                        risk_factors = EXCLUDED.risk_factors,
                        created_at = CURRENT_TIMESTAMP
                """, (
                    ticker,
                    datetime.now().date(),
                    analysis_data['summary'],
                    analysis_data['recommendation'],
                    analysis_data['confidence_score'],
                    analysis_data['momentum_analysis'],
                    analysis_data['liquidity_analysis'],
                    analysis_data['risk_factors']
                ))
                saved_count += 1
                print(f"✅ {ticker} {name}: {analysis_data['recommendation']}")
            except Exception as e:
                print(f"❌ {ticker} {name} 저장 실패: {e}")

    print(f"\n✅ 총 {saved_count}개 종목 DB 저장 완료")
    return saved_count

if __name__ == '__main__':
    import_report()
