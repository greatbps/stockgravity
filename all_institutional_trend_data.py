import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime
import os
from tqdm import tqdm
from io import StringIO 

def get_investor_trend(ticker, pages=10):
    """
    Naver Finance에서 투자자별 매매동향(외국인/기관)을 가져옵니다.
    """
    url = f"https://finance.naver.com/item/frgn.naver?code={ticker}"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    
    df_list = []
    
    try:
        for page in range(1, pages + 1):
            pg_url = f'{url}&page={page}'
            response = requests.get(pg_url, headers=headers)
            html = BeautifulSoup(response.text, "lxml")
            
            # 투자자별 매매동향 테이블 찾기 (보통 두 번째 테이블이지만 구조에 따라 다를 수 있음)
            tables = html.select("table")
            
            target_table = None
            for tbl in tables:
                if "기관" in str(tbl) and "외국인" in str(tbl):
                    target_table = tbl
                    break
            
            if target_table:
                df = pd.read_html(StringIO(str(target_table)))[0]
                df = df.dropna()
                # 컬럼 정리 (멀티 인덱스 등 처리)
                # 네이버 금융 구조: 날짜, 종가, 전일비, 등락률, 거래량, 기관(순매매량), 외국인(순매매량), 보유주수, 보유율
                # 컬럼명이 복잡할 수 있으므로 위치 기반으로 선택하거나 정리 필요
                
                # 보통 level 0: 날짜, 종가, 전일비, 등락률, 거래량, 기관, 외국인, 외국인...
                # level 1: 날짜, 종가, 전일비, 등락률, 거래량, 순매매량, 순매매량, 보유주수, 보유율
                
                if isinstance(df.columns, pd.MultiIndex):
                     df.columns = [c[1] if c[1] else c[0] for c in df.columns]
                
                df_list.append(df)
            else:
                break
                
            time.sleep(0.05)
            
        if not df_list:
            return None
            
        df = pd.concat(df_list, ignore_index=True)
        df['ticker'] = ticker
        
        # 컬럼 이름 매핑 (필요한 것만)
        # 실제 데이터프레임 컬럼 확인 필요. 일반적으로: ['날짜', '종가', '전일비', '등락률', '거래량', '순매매량', '순매매량', '보유주수', '보유율']
        # 5번째가 기관 순매매량, 6번째가 외국인 순매매량인 경우가 많음 (0-indexed)
        # 하지만 명시적으로 찾는 게 안전함.
        
        # '기관' 포함된 컬럼과 '외국인' 포함된 컬럼 찾기 (위치로 가정)
        # 네이버 페이지 구조상:
        # 날짜 | 종가 | 전일비 | 등락률 | 거래량 | 기관(순매매량) | 외국인(순매매량) | ...
        
        df = df.iloc[:, [0, 5, 6]] # 날짜, 기관, 외국인
        df.columns = ['date', 'institutional_net_buy', 'foreigner_net_buy']
        df['ticker'] = ticker  # ticker 컬럼 추가

        # 전처리
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values(by='date')
        
        return df

    except Exception as e:
        print(f"Error fetching investor data for {ticker}: {e}")
        return None

def fetch_and_save_investor_data(stock_list_path, output_path, pages_to_fetch=20, limit=None):
    print(f"Loading stock list from {stock_list_path}...")
    try:
        stocks = pd.read_csv(stock_list_path)
        if 'ticker' in stocks.columns:
            stocks['ticker'] = stocks['ticker'].astype(str).str.zfill(6)
        else:
            print("Error: 'ticker' column not found in csv")
            return
            
        tickers = stocks['ticker'].tolist()
        if limit:
            tickers = tickers[:limit]
        
    except Exception as e:
        print(f"Failed to read stock list: {e}")
        return

    all_data = []
    
    print("Starting investor trend data collection...")
    for ticker in tqdm(tickers):
        df = get_investor_trend(ticker, pages=pages_to_fetch)
        if df is not None:
            all_data.append(df)
            
    if all_data:
        final_df = pd.concat(all_data, ignore_index=True)
        final_df.to_csv(output_path, index=False)
        print(f"Data saved to {output_path}. Total rows: {len(final_df)}")
    else:
        print("No data collected.")

if __name__ == "__main__":
    STOCK_LIST_FILE = "korean_stocks_list.csv"
    OUTPUT_FILE = "all_institutional_trend_data.csv"
    PAGES = 20 # 최근 20페이지 (약 1달 반 - 2달)
    
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, help="Limit number of stocks to process")
    args = parser.parse_args()
    
    if os.path.exists(STOCK_LIST_FILE):
        fetch_and_save_investor_data(STOCK_LIST_FILE, OUTPUT_FILE, PAGES, limit=args.limit)
    else:
        print(f"File not found: {STOCK_LIST_FILE}")
