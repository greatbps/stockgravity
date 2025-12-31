import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime, timedelta
import os
from tqdm import tqdm
import multiprocessing
from io import StringIO

def get_daily_price(ticker_pages):
    ticker, pages = ticker_pages

    url = f"https://finance.naver.com/item/sise_day.nhn?code={ticker}"
    headers = {'User-Agent': 'Mozilla/5.0'}
    session = requests.Session()
    session.headers.update(headers)

    df_list = []

    for page in range(1, pages + 1):
        response = session.get(f"{url}&page={page}")
        tables = pd.read_html(StringIO(response.text))

        if not tables:
            break

        df = tables[0].dropna()
        df_list.append(df)

    if not df_list:
        return None

    df = pd.concat(df_list, ignore_index=True)
    df['ticker'] = ticker
    df = df.rename(columns={
        '날짜': 'date', '종가': 'close', '전일비': 'diff',
        '시가': 'open', '고가': 'high', '저가': 'low', '거래량': 'volume'
    })
    df['date'] = pd.to_datetime(df['date'])
    return df.sort_values('date')


def fetch_and_save_data(stock_list_path, output_path, pages_to_fetch=20, limit=None):
    stocks = pd.read_csv(stock_list_path)
    stocks['ticker'] = stocks['ticker'].astype(str).str.zfill(6)
    tickers = stocks['ticker'].tolist()

    if limit:
        tickers = tickers[:limit]

    print(f"Processing {len(tickers)} stocks with multiprocessing...")

    workers = max(1, multiprocessing.cpu_count() - 1)
    pool = multiprocessing.Pool(workers)

    tasks = [(ticker, pages_to_fetch) for ticker in tickers]

    results = list(tqdm(
        pool.imap_unordered(get_daily_price, tasks),
        total=len(tasks)
    ))

    pool.close()
    pool.join()

    final_data = [df for df in results if df is not None]

    if final_data:
        final_df = pd.concat(final_data, ignore_index=True)
        final_df.to_csv(output_path, index=False)
        print(f"Saved {len(final_df)} rows")


if __name__ == "__main__":
    # 설정
    STOCK_LIST_FILE = "korean_stocks_list.csv"
    OUTPUT_FILE = "daily_prices.csv"
    PAGES = 40 
    
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, help="Limit number of stocks to process")
    args = parser.parse_args()

    if os.path.exists(STOCK_LIST_FILE):
        if args.limit:
            print(f"Running in limited mode: {args.limit} stocks")
            # fetch_and_save_data 함수 내부를 수정하거나, 여기서 ticker 리스트를 잘라서 전달해야 함.
            # 하지만 fetch_and_save_data는 파일 경로를 받음.
            # 함수를 수정하는 것이 좋겠음.
            # 아래와 같이 함수를 호출하기 전에 내부적으로 처리하도록 수정.
            pass
        
        # 함수 재정의 대신, 함수 인자로 limit을 전달하도록 수정 필요.
        # 따라서 fetch_and_save_data 시그니처 변경
        fetch_and_save_data(STOCK_LIST_FILE, OUTPUT_FILE, PAGES, limit=args.limit)
    else:
        print(f"File not found: {STOCK_LIST_FILE}")
