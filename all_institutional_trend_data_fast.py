import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime
import os
from tqdm import tqdm
from io import StringIO
import multiprocessing

def get_investor_trend(ticker_pages):
    """
    Naver Finance에서 투자자별 매매동향(외국인/기관)을 가져옵니다.
    """
    ticker, pages = ticker_pages

    url = f"https://finance.naver.com/item/frgn.naver?code={ticker}"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

    df_list = []

    try:
        for page in range(1, pages + 1):
            pg_url = f'{url}&page={page}'
            response = requests.get(pg_url, headers=headers)
            html = BeautifulSoup(response.text, "lxml")

            # 투자자별 매매동향 테이블 찾기
            tables = html.select("table")

            target_table = None
            for tbl in tables:
                if "기관" in str(tbl) and "외국인" in str(tbl):
                    target_table = tbl
                    break

            if target_table:
                df = pd.read_html(StringIO(str(target_table)))[0]
                df = df.dropna()

                if isinstance(df.columns, pd.MultiIndex):
                     df.columns = [c[1] if c[1] else c[0] for c in df.columns]

                df_list.append(df)
            else:
                break

            time.sleep(0.05)

        if not df_list:
            return None

        df = pd.concat(df_list, ignore_index=True)

        df = df.iloc[:, [0, 5, 6]] # 날짜, 기관, 외국인
        df.columns = ['date', 'institutional_net_buy', 'foreigner_net_buy']
        df['ticker'] = ticker  # ticker 컬럼 추가

        # 전처리
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values(by='date')

        return df

    except Exception as e:
        # print(f"Error fetching investor data for {ticker}: {e}")
        return None

def fetch_and_save_investor_data(stock_list_path, output_path, pages_to_fetch=20, filtered_only=False):
    print(f"Loading stock list from {stock_list_path}...")

    if filtered_only and os.path.exists('filtered_stocks.csv'):
        print("Using filtered stock list (top 500)...")
        stocks = pd.read_csv('filtered_stocks.csv')
        stocks['ticker'] = stocks['ticker'].astype(str).str.zfill(6)
    else:
        stocks = pd.read_csv(stock_list_path)
        if 'ticker' in stocks.columns:
            stocks['ticker'] = stocks['ticker'].astype(str).str.zfill(6)
        else:
            print("Error: 'ticker' column not found in csv")
            return

    tickers = stocks['ticker'].tolist()

    print(f"Processing {len(tickers)} stocks with multiprocessing...")

    # 멀티프로세싱 설정
    workers = max(1, multiprocessing.cpu_count() - 1)
    print(f"Using {workers} worker processes")

    pool = multiprocessing.Pool(workers)

    tasks = [(ticker, pages_to_fetch) for ticker in tickers]

    results = list(tqdm(
        pool.imap_unordered(get_investor_trend, tasks),
        total=len(tasks)
    ))

    pool.close()
    pool.join()

    # None이 아닌 결과만 필터링
    all_data = [df for df in results if df is not None]

    if all_data:
        final_df = pd.concat(all_data, ignore_index=True)
        final_df.to_csv(output_path, index=False)
        print(f"\nData saved to {output_path}. Total rows: {len(final_df)}")
    else:
        print("No data collected.")

if __name__ == "__main__":
    STOCK_LIST_FILE = "korean_stocks_list.csv"
    OUTPUT_FILE = "all_institutional_trend_data.csv"
    PAGES = 20 # 최근 20페이지

    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--filtered-only", action="store_true",
                       help="Use filtered stock list (top 500) instead of all stocks")
    parser.add_argument("--pages", type=int, default=20,
                       help="Number of pages to fetch per stock")
    args = parser.parse_args()

    if os.path.exists(STOCK_LIST_FILE):
        fetch_and_save_investor_data(
            STOCK_LIST_FILE,
            OUTPUT_FILE,
            pages_to_fetch=args.pages,
            filtered_only=args.filtered_only
        )
    else:
        print(f"File not found: {STOCK_LIST_FILE}")
