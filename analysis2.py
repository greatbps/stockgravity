import pandas as pd
import numpy as np
import os
from tqdm import tqdm
from db_config import get_db_connection

class EnhancedWaveTransitionAnalyzerV3:
    def __init__(self, investor_data_path, stock_list_path, days_back=180):
        # Load price data from DB
        print(f"Loading price data from DB (최근 {days_back}일)...")
        with get_db_connection() as conn:
            self.price_data = pd.read_sql(f"""
                SELECT ticker, date, open, high, low, close, volume
                FROM daily_prices
                WHERE date >= CURRENT_DATE - INTERVAL '{days_back} days'
                ORDER BY ticker, date
            """, conn)
        print(f"   ✅ {len(self.price_data):,}행 로드")

        self.stock_list = pd.read_csv(stock_list_path)

        # Ticker format check
        self.price_data['ticker'] = self.price_data['ticker'].astype(str).str.zfill(6)
        self.stock_list['ticker'] = self.stock_list['ticker'].astype(str).str.zfill(6)

        # 날짜 포맷 통일
        self.price_data['date'] = pd.to_datetime(self.price_data['date'])

        # 수급 데이터는 선택적으로 로드
        self.investor_data = None
        try:
            if investor_data_path and os.path.exists(investor_data_path):
                self.investor_data = pd.read_csv(investor_data_path)
                if 'ticker' in self.investor_data.columns:
                    self.investor_data['ticker'] = self.investor_data['ticker'].astype(str).str.zfill(6)
                    self.investor_data['date'] = pd.to_datetime(self.investor_data['date'])
                else:
                    print("Warning: investor data missing 'ticker' column. Proceeding without investor data.")
                    self.investor_data = None
        except Exception as e:
            print(f"Warning: Could not load investor data: {e}. Proceeding without investor data.")
            self.investor_data = None
        
    def _calculate_rsi(self, series, period=14):
        delta = series.diff(1)
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        return 100 - (100 / (1 + rs))

    def _calculate_technical_indicators(self, df):
        # 이동평균선
        df['MA20'] = df['close'].rolling(window=20).mean()
        df['MA50'] = df['close'].rolling(window=50).mean()
        df['MA200'] = df['close'].rolling(window=200).mean()
        
        # 거래량 평균
        df['VolMA20'] = df['volume'].rolling(window=20).mean()
        
        # 52주 신고가/신저가
        # 최근 250일(약 1년) 데이터가 충분하지 않을 수 있으므로 가능한 만큼 계산
        df['High52'] = df['high'].rolling(window=252, min_periods=50).max()
        df['Low52'] = df['low'].rolling(window=252, min_periods=50).min()
        
        # 52주 위치 (0~1)
        df['Position52'] = (df['close'] - df['Low52']) / (df['High52'] - df['Low52'])
        
        # RSI
        df['RSI'] = self._calculate_rsi(df['close'])
        
        return df

    def analyze_stock(self, ticker):
        df_price = self.price_data[self.price_data['ticker'] == ticker].copy()
        if df_price.empty or len(df_price) < 60: # 최소 데이터 요구량
            return None
            
        df_price = df_price.sort_values(by='date')
        df_price = self._calculate_technical_indicators(df_price)
        
        # 최신 데이터만 분석 (오늘 기준)
        latest = df_price.iloc[-1]
        
        # 지표가 NaN이면 분석 불가
        if pd.isna(latest['MA20']) or pd.isna(latest['MA50']):
            return None
            
        score = 0
        wave_stage = "Unknown"
        
        # 조건 변수
        ma_aligned = (latest['MA20'] > latest['MA50']) and (latest['MA50'] > latest['MA200'] if not pd.isna(latest['MA200']) else True)
        ma_golden = latest['MA20'] > latest['MA50']
        
        pos52 = latest['Position52'] if not pd.isna(latest['Position52']) else 0.5
        vol_ratio = latest['volume'] / latest['VolMA20'] if latest['VolMA20'] > 0 else 1.0
        rsi = latest['RSI'] if not pd.isna(latest['RSI']) else 50
        
        # 1. 2단계 중기 (Strong Uptrend) - 90점
        if ma_aligned and (0.6 <= pos52 <= 0.95) and (vol_ratio >= 1.3) and (55 <= rsi <= 85):
            score = 90
            wave_stage = "Strong Uptrend"
            
        # 2. 2단계 초기 (Early Uptrend) - 80점
        elif ma_golden and (0.4 <= pos52 <= 0.75) and (latest['close'] > latest['MA20']) and (vol_ratio >= 1.1):
            score = 80
            wave_stage = "Early Uptrend"
            
        # 3. 1단계 -> 2단계 전환 (Transition) - 70점
        # 20일과 50일 이격도(Diff)가 작을 때 (수렴)
        elif abs(latest['MA20'] - latest['MA50']) / latest['MA50'] < 0.05 and (0.25 <= pos52 <= 0.6) and (45 <= rsi <= 65):
            score = 70
            wave_stage = "Transition"
            
        # 4. 일반 상승 추세 (General Uptrend) - 60점
        elif ma_golden and (0.3 <= pos52 <= 0.8):
            score = 60
            wave_stage = "General Uptrend"
            
        # 수급 점수 가산 (Investor Trends) - 선택적
        investor_score = 0
        if self.investor_data is not None:
            df_invest = self.investor_data[self.investor_data['ticker'] == ticker]
            if not df_invest.empty:
                # 최근 5일 기관/외국인 순매수 합계가 양수면 가산점
                recent_invest = df_invest[df_invest['date'] >= (latest['date'] - pd.Timedelta(days=7))]
                if not recent_invest.empty:
                    inst_sum = recent_invest['institutional_net_buy'].sum()
                    frgn_sum = recent_invest['foreigner_net_buy'].sum()

                    if inst_sum > 0: investor_score += 5
                    if frgn_sum > 0: investor_score += 5

        final_score = score + investor_score
        
        # 종목명 가져오기
        stock_name = self.stock_list[self.stock_list['ticker'] == ticker]['name'].values[0]
        
        return {
            'date': latest['date'],
            'ticker': ticker,
            'name': stock_name,
            'wave_stage': wave_stage,
            'score': final_score,
            'close': latest['close'],
            'volume': latest['volume'],
            'MA20': latest['MA20'],
            'MA50': latest['MA50'],
            'RSI': rsi,
            'Position52': pos52
        }

    def run_analysis(self):
        print("Starting Wave Analysis...")
        unique_tickers = self.price_data['ticker'].unique()
        results = []
        
        for ticker in tqdm(unique_tickers):
            try:
                res = self.analyze_stock(ticker)
                if res:
                    results.append(res)
            except Exception as e:
                # print(f"Error analyzing {ticker}: {e}")
                continue
                
        results_df = pd.DataFrame(results)
        if not results_df.empty:
            results_df = results_df.sort_values(by='score', ascending=False)
            
        return results_df

if __name__ == "__main__":
    INVESTOR_FILE = "all_institutional_trend_data.csv"
    STOCK_LIST_FILE = "korean_stocks_list.csv"
    OUTPUT_FILE = "wave_transition_analysis_results.csv"

    # DB 버전: PRICE_FILE 불필요
    print("Running analysis with DB-based price data...")
    analyzer = EnhancedWaveTransitionAnalyzerV3(INVESTOR_FILE, STOCK_LIST_FILE, days_back=180)
    results = analyzer.run_analysis()
    if not results.empty:
        results.to_csv(OUTPUT_FILE, index=False)
        print(f"Analysis saved to {OUTPUT_FILE}. Top 5 stocks:")
        print(results.head())
    else:
        print("No results generated.")
