import pandas as pd
import numpy as np
from tqdm import tqdm
import argparse
from db_config import get_db_connection

def calculate_stock_score(stock_df):
    """
    종목별 점수 계산 (거래대금 40%, 모멘텀 30%, 거래량증가율 30%)
    """
    if len(stock_df) < 20:
        return None

    stock_df = stock_df.sort_values('date')
    latest = stock_df.iloc[-1]
    recent_20 = stock_df.tail(20)
    recent_5 = stock_df.tail(5)

    # 1. 거래대금
    trading_value = latest['close'] * latest['volume']

    # 2. 5일 모멘텀
    if recent_5.iloc[0]['close'] > 0:
        change_5d = ((latest['close'] - recent_5.iloc[0]['close']) / recent_5.iloc[0]['close'] * 100)
    else:
        change_5d = 0

    # 3. 거래량 증가율
    vol_avg_20 = recent_20['volume'].mean()
    vol_ratio = latest['volume'] / vol_avg_20 if vol_avg_20 > 0 else 0

    return {
        'ticker': latest['ticker'],
        'close': latest['close'],
        'volume': latest['volume'],
        'trading_value': trading_value,
        'change_5d': change_5d,
        'vol_ratio': vol_ratio
    }

def filter_stocks(stock_list_path, output_path, top_n=500, days_back=60):
    """
    옵션 B: 균형적 필터링 (상위 500개) - DB 버전
    """
    print(f"Loading price data from DB (최근 {days_back}일)...")
    with get_db_connection() as conn:
        df = pd.read_sql(f"""
            SELECT ticker, date, open, high, low, close, volume
            FROM daily_prices
            WHERE date >= CURRENT_DATE - INTERVAL '{days_back} days'
            ORDER BY ticker, date
        """, conn)

    df['date'] = pd.to_datetime(df['date'])
    df['ticker'] = df['ticker'].astype(str).str.zfill(6)
    print(f"   ✅ {len(df):,}행 로드 (종목 {df['ticker'].nunique()}개)")

    print("Calculating scores for all stocks...")
    stock_scores = []

    for ticker in tqdm(df['ticker'].unique()):
        stock_df = df[df['ticker'] == ticker]
        score_data = calculate_stock_score(stock_df)

        if score_data:
            stock_scores.append(score_data)

    scores_df = pd.DataFrame(stock_scores)

    print(f"\nTotal stocks analyzed: {len(scores_df)}")

    # 필터링 기준 적용
    print("\nApplying filters...")
    filtered = scores_df[
        (scores_df['trading_value'] > 100_000_000) &  # 거래대금 > 1억원
        (scores_df['change_5d'] > -5) &               # 5일 등락률 > -5%
        (scores_df['vol_ratio'] > 0.5) &              # 거래량 증가율 > 0.5배
        (scores_df['close'] > 5000)                   # 종가 > 5,000원
    ].copy()

    print(f"After filtering: {len(filtered)} stocks")

    # 점수 계산 (정규화)
    # 거래대금, 모멘텀, 거래량 증가율을 0-100 범위로 정규화
    if len(filtered) > 0:
        # Min-Max 정규화
        filtered['trading_value_score'] = (
            (filtered['trading_value'] - filtered['trading_value'].min()) /
            (filtered['trading_value'].max() - filtered['trading_value'].min()) * 100
        )

        # 모멘텀은 -5 ~ max 범위를 0-100으로
        filtered['momentum_score'] = (
            (filtered['change_5d'] - filtered['change_5d'].min()) /
            (filtered['change_5d'].max() - filtered['change_5d'].min()) * 100
        )

        filtered['volume_score'] = (
            (filtered['vol_ratio'] - filtered['vol_ratio'].min()) /
            (filtered['vol_ratio'].max() - filtered['vol_ratio'].min()) * 100
        )

        # 가중 평균 점수
        filtered['final_score'] = (
            filtered['trading_value_score'] * 0.4 +
            filtered['momentum_score'] * 0.3 +
            filtered['volume_score'] * 0.3
        )

        # 점수 순으로 정렬
        filtered = filtered.sort_values('final_score', ascending=False)

        # 상위 N개 선정
        top_stocks = filtered.head(top_n)

        print(f"\nTop {top_n} stocks selected")
        print(f"\nScore statistics:")
        print(f"  Average trading value: {top_stocks['trading_value'].mean()/100000000:.1f}억원")
        print(f"  Average 5-day change: {top_stocks['change_5d'].mean():.2f}%")
        print(f"  Average volume ratio: {top_stocks['vol_ratio'].mean():.2f}x")

        # 종목 리스트 파일에서 종목명 가져오기
        stock_list = pd.read_csv(stock_list_path)
        stock_list['ticker'] = stock_list['ticker'].astype(str).str.zfill(6)

        top_stocks = top_stocks.merge(
            stock_list[['ticker', 'name']],
            on='ticker',
            how='left'
        )

        # 결과 저장
        top_stocks.to_csv(output_path, index=False)
        print(f"\nFiltered stock list saved to {output_path}")

        # Top 20 출력
        print("\n=== Top 20 Stocks ===")
        print(top_stocks[['ticker', 'name', 'close', 'trading_value', 'change_5d', 'final_score']].head(20).to_string(index=False))

        return top_stocks
    else:
        print("No stocks passed the filters!")
        return None

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Filter stocks based on trading metrics (DB version)')
    parser.add_argument('--top', type=int, default=500, help='Number of top stocks to select')
    parser.add_argument('--days', type=int, default=60, help='Number of days to look back')
    args = parser.parse_args()

    STOCK_LIST_FILE = "korean_stocks_list.csv"
    OUTPUT_FILE = "filtered_stocks.csv"

    filter_stocks(STOCK_LIST_FILE, OUTPUT_FILE, top_n=args.top, days_back=args.days)
