import pandas as pd
import os
import glob

def load_filtered_stocks(file_path):
    """필터링된 종목 데이터 로드"""
    if not os.path.exists(file_path):
        return pd.DataFrame()
    try:
        df = pd.read_csv(file_path)
        # ticker를 6자리로 패딩
        if 'ticker' in df.columns:
            df['ticker'] = df['ticker'].astype(str).str.zfill(6)
        return df
    except Exception as e:
        print(f"Error loading filtered stocks: {e}")
        return pd.DataFrame()

def load_analysis_results(file_path="wave_transition_analysis_results.csv"):
    if not os.path.exists(file_path):
        return pd.DataFrame()
    return pd.read_csv(file_path)

def load_price_data(file_path, ticker=None):
    """가격 데이터 로드"""
    if not os.path.exists(file_path):
        return pd.DataFrame()

    try:
        # 전체 데이터를 매번 로드하면 느릴 수 있으므로 최적화 필요하지만
        # 일단 기능 구현 우선. (실제 서비스시에는 DB 등 사용 권장)
        df = pd.read_csv(file_path)
        df['date'] = pd.to_datetime(df['date'])

        if ticker:
            df = df[df['ticker'].astype(str).str.zfill(6) == str(ticker).zfill(6)]

        return df
    except Exception as e:
        print(f"Error loading price data: {e}")
        return pd.DataFrame()

def get_latest_report():
    # 프로젝트 루트 디렉토리에서 리포트 파일 찾기
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.join(current_dir, "..")
    pattern = os.path.join(project_root, "ai_analysis_report_*.md")

    files = glob.glob(pattern)
    if not files:
        return None
    latest_file = max(files, key=os.path.getctime)
    try:
        with open(latest_file, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        print(f"Error reading report: {e}")
        return None
