import subprocess
import os
import sys
from io import StringIO

def run_script(script_name, args=[]):
    print(f"\n[StockAI] Running {script_name} {' '.join(args)}...")
    try:
        cmd = [sys.executable, script_name] + args
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running {script_name}: {e}")
        return False
    return True

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", action="store_true", help="Run in test mode with limited data")
    args = parser.parse_args()
    
    print("Starting StockAI Analysis Pipeline...")
    
    limit_args = []
    if args.test:
        print("TEST MODE: Running with limit=10 stocks")
        limit_args = ["--limit", "10"]
    
    # 1. 데이터 수집 - 시세
    if not run_script("create_complete_daily_prices.py", limit_args): return
    
    # 2. 데이터 수집 - 수급
    if not run_script("all_institutional_trend_data.py", limit_args): return
    
    # 3. 파동 분석 (데이터가 적으므로 그대로 실행)
    if not run_script("analysis2.py"): return
    
    # 4. AI 심층 분석
    if not run_script("investigate_top_stocks.py"): return
    
    print("\nAll analysis completed successfully!")
    print("Run 'streamlit run dashboard/app.py' to view the results.")

if __name__ == "__main__":
    main()
