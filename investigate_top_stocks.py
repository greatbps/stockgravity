import pandas as pd
import os
from dotenv import load_dotenv
import google.generativeai as genai
from duckduckgo_search import DDGS
from datetime import datetime

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
    Gemini를 사용하여 종목 분석 리포트 생성
    """
    if not GOOGLE_API_KEY:
        return "API Key missing. Cannot perform AI analysis."

    model = genai.GenerativeModel('gemini-2.5-flash')
    
    prompt = f"""
    당신은 20년 경력의 베테랑 주식 애널리스트입니다. 아래 제공된 데이터와 뉴스를 바탕으로 해당 종목에 대한 투자 보고서를 작성해주세요.
    
    ## 분석 대상 종목
    - 종목명: {stock_info['name']} ({stock_info['ticker']})
    - 현재가: {stock_info['close']}원
    - 파동 단계: {stock_info['wave_stage']}
    - 기술적 점수: {stock_info['score']}점
    - RSI: {stock_info['RSI']:.2f}
    
    ## 최근 관련 뉴스
    {news_text}
    
    ## 작성 가이드
    1. **요약 의견**: 매수/매도/보류 중 하나의 의견을 제시하고 이유를 한 문장으로 요약하세요.
    2. **기술적 분석**: 현재 파동 단계와 지표들이 의미하는 바를 설명하세요.
    3. **재료 분석**: 뉴스 내용을 바탕으로 호재/악재를 분석하세요.
    4. **리스크 요인**: 주의해야 할 점을 지적하세요.
    5. **목표가/손절가 제안**: (가상의) 단기 목표가와 손절가를 제안하세요.
    
    보고서는 마크다운 형식으로 작성해주세요.
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error analyzing with Gemini: {e}"

def run_investigation(input_csv="wave_transition_analysis_results.csv", top_n=3):
    if not os.path.exists(input_csv):
        print(f"{input_csv} not found.")
        return

    df = pd.read_csv(input_csv)
    if df.empty:
        print("No analysis results found.")
        return
        
    # 상위 종목 선정
    top_stocks = df.head(top_n)
    
    report_filename = f"ai_analysis_report_{datetime.now().strftime('%Y%m%d')}.md"
    
    with open(report_filename, "w", encoding="utf-8") as f:
        f.write(f"# StockAI Daily Analysis Report ({datetime.now().strftime('%Y-%m-%d')})\n\n")
        
        for _, row in top_stocks.iterrows():
            print(f"Analyzing {row['name']}...")
            
            # 뉴스 검색
            news = search_news(row['name'])
            
            # AI 분석
            analysis = analyze_stock_with_gemini(row, news)
            
            # 리포트 작성
            f.write(f"---\n\n## {row['name']} ({row['ticker']})\n")
            f.write(f"- **Score**: {row['score']}\n")
            f.write(f"- **Wave Stage**: {row['wave_stage']}\n\n")
            f.write(analysis)
            f.write("\n\n")
            
    print(f"AI Analysis Report saved to {report_filename}")

if __name__ == "__main__":
    run_investigation()
