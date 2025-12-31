import pandas as pd
import os
from dotenv import load_dotenv
import google.generativeai as genai
from duckduckgo_search import DDGS
from datetime import datetime
import argparse
from db_config import get_db_connection
import re

# 환경변수 로드
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    print("WARNING: GOOGLE_API_KEY not found in .env file.")

# Gemini 설정
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)

def search_news(keyword, num_results=5):
    """
    DuckDuckGo를 사용하여 뉴스 검색
    """
    try:
        ddgs = DDGS()
        results = list(ddgs.news(keywords=f"{keyword} 주가 전망", region="kr-kr", safesearch="off", max_results=num_results))
        news_summary = ""
        for i, res in enumerate(results):
            news_summary += f"{i+1}. Title: {res['title']}\n   Source: {res['source']}\n   Date: {res['date']}\n   Snippet: {res['body']}\n\n"
        return news_summary
    except Exception as e:
        print(f"Error searching news for {keyword}: {e}")
        return "No news found."

def analyze_stock_with_gemini(stock_info, news_text):
    """
    Gemini를 사용하여 종목 분석 리포트 생성 (필터링 데이터 기반)
    """
    if not GOOGLE_API_KEY:
        return "API Key missing. Cannot perform AI analysis."

    # gemini-2.5-flash 사용 (최신 안정 버전)
    model = genai.GenerativeModel('gemini-2.5-flash')

    prompt = f"""
    당신은 20년 경력의 베테랑 주식 애널리스트입니다. 아래 제공된 데이터와 뉴스를 바탕으로 해당 종목에 대한 투자 보고서를 작성해주세요.

    ## 분석 대상 종목
    - 종목명: {stock_info['name']} ({stock_info['ticker']})
    - 현재가: {stock_info['close']:,}원
    - 거래대금: {stock_info['trading_value']/100000000:.1f}억원
    - 5일 등락률: {stock_info['change_5d']:.2f}%
    - 거래량 증가율: {stock_info['vol_ratio']:.2f}배
    - 종합 점수: {stock_info['final_score']:.1f}점 (거래대금 40% + 모멘텀 30% + 거래량 30%)

    ## 최근 관련 뉴스
    {news_text}

    ## 작성 가이드
    1. **요약 의견**: 매수/관심종목/보류 중 하나의 의견을 제시하고 이유를 한 문장으로 요약하세요.
    2. **모멘텀 분석**: 5일 등락률과 거래량 증가율을 바탕으로 현재 모멘텀 상태를 분석하세요.
    3. **유동성 분석**: 거래대금을 바탕으로 종목의 유동성과 안정성을 평가하세요.
    4. **재료 분석**: 뉴스 내용을 바탕으로 호재/악재를 분석하세요.
    5. **리스크 요인**: 주의해야 할 점을 지적하세요.
    6. **투자 전략**: 진입 타이밍, 목표 수익률, 손절 기준을 제안하세요.

    보고서는 마크다운 형식으로 작성해주세요. 간결하고 실용적으로 작성하세요.
    """

    import time
    max_retries = 3
    retry_delay = 10  # 초

    for attempt in range(max_retries):
        try:
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg or "quota" in error_msg.lower():
                if attempt < max_retries - 1:
                    print(f"    ⚠️ API 할당량 초과. {retry_delay}초 후 재시도... ({attempt + 1}/{max_retries})")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # 지수 백오프
                    continue
                else:
                    return f"⚠️ API 할당량 초과로 분석 실패. 잠시 후 다시 시도해주세요.\n\n[상세 에러: {error_msg[:200]}]"
            else:
                return f"⚠️ 분석 중 오류 발생: {error_msg[:200]}"

    return "⚠️ 재시도 횟수 초과"

def parse_ai_response(analysis_text):
    """
    AI 분석 결과에서 구조화된 정보 추출
    """
    # 기본값
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
            # 불필요한 마크다운 제거
            content = re.sub(r'[*#]+', '', content).strip()
            result[field_name] = content[:500]  # 길이 제한

    # summary가 비어있으면 전체 텍스트의 첫 200자 사용
    if not result['summary']:
        result['summary'] = analysis_text[:200].strip()

    return result

def save_to_database(ticker, analysis_data):
    """
    AI 분석 결과를 데이터베이스에 저장
    """
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
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
        return True
    except Exception as e:
        print(f"    ⚠️ DB 저장 실패: {e}")
        return False

def run_investigation(input_csv="filtered_stocks.csv", top_n=5, use_db_priority=True):
    """
    AI 분석 실행

    Args:
        input_csv: CSV 파일 경로 (DB 우선순위 사용 시 무시됨)
        top_n: 분석할 종목 수
        use_db_priority: True면 DB에서 우선순위 기반 선정
    """

    if use_db_priority:
        # DB 기반 우선순위 선정 (추천 방식)
        print("📊 DB 기반 우선순위 선정 중...")
        print("   - status='monitoring' 종목 중")
        print("   - 오늘 AI 분석 안 된 종목")
        print("   - final_score 순으로 선정\n")

        from db_config import get_db_connection
        import pandas as pd

        with get_db_connection() as conn:
            df = pd.read_sql(f"""
                SELECT ticker, name, close, trading_value, change_5d, vol_ratio, final_score
                FROM stock_pool
                WHERE status = 'monitoring'
                  AND ticker NOT IN (
                    SELECT DISTINCT ticker
                    FROM ai_analysis_reports
                    WHERE report_date = CURRENT_DATE
                  )
                ORDER BY final_score DESC
                LIMIT {top_n}
            """, conn)

        if df.empty:
            print("⚠️  모든 monitoring 종목이 이미 분석되었습니다.")
            print("    또는 stock_pool에 monitoring 종목이 없습니다.")
            return False

        print(f"✅ {len(df)}개 종목 선정 완료\n")
        top_stocks = df

    else:
        # 기존 CSV 기반 방식
        if not os.path.exists(input_csv):
            print(f"{input_csv} not found.")
            return False

        df = pd.read_csv(input_csv)
        if df.empty:
            print("No filtered stocks found.")
            return False

        # 상위 종목 선정 (final_score 기준)
        df = df.sort_values('final_score', ascending=False)
        top_stocks = df.head(top_n)

    report_filename = f"ai_analysis_report_{datetime.now().strftime('%Y%m%d')}.md"

    print(f"Generating AI analysis report for top {top_n} stocks...")

    import time
    successful_count = 0
    failed_count = 0

    with open(report_filename, "w", encoding="utf-8") as f:
        f.write(f"# StockGravity AI Analysis Report\n")
        f.write(f"**생성일**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"**분석 대상**: 필터링된 상위 {top_n}개 종목\n\n")
        f.write("---\n\n")

        for idx, (_, row) in enumerate(top_stocks.iterrows(), 1):
            print(f"  [{idx}/{len(top_stocks)}] {row['name']} ({row['ticker']}) 분석 중...")

            # 뉴스 검색
            news = search_news(row['name'])

            # AI 분석
            analysis = analyze_stock_with_gemini(row, news)

            # 리포트 작성
            f.write(f"## {row['name']} ({row['ticker']})\n\n")
            f.write(f"**종합 점수**: {row['final_score']:.1f}점 | ")
            f.write(f"**현재가**: {row['close']:,}원 | ")
            f.write(f"**거래대금**: {row['trading_value']/100000000:.1f}억원\n\n")
            f.write(analysis)
            f.write("\n\n---\n\n")

            # 성공/실패 카운트
            if "⚠️" in analysis or "Error" in analysis:
                failed_count += 1
            else:
                successful_count += 1
                # DB에 저장 (성공한 경우에만)
                ticker = str(row['ticker']).zfill(6)
                analysis_data = parse_ai_response(analysis)
                if save_to_database(ticker, analysis_data):
                    print(f"    ✅ DB 저장 완료")
                else:
                    print(f"    ⚠️ DB 저장 실패 (파일은 저장됨)")

            # Rate limit 방지: 종목 간 대기 (마지막 종목은 제외)
            if idx < len(top_stocks):
                print(f"    다음 종목 분석 대기 중 (3초)...")
                time.sleep(3)

    print(f"\n✅ AI Analysis Report saved to {report_filename}")
    print(f"   성공: {successful_count}개 | 실패: {failed_count}개")

    if failed_count > 0:
        print(f"\n⚠️  일부 종목 분석 실패. API 할당량을 확인하거나 잠시 후 다시 시도하세요.")

    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate AI analysis report for filtered stocks')
    parser.add_argument('--top', type=int, default=20, help='Number of top stocks to analyze (default: 20)')
    parser.add_argument('--use-csv', action='store_true', help='Use CSV instead of DB priority (legacy mode)')
    args = parser.parse_args()

    # 기본은 DB 우선순위 모드
    use_db = not args.use_csv

    success = run_investigation(top_n=args.top, use_db_priority=use_db)
    if not success:
        exit(1)
