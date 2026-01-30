
import yfinance as yf
import pandas as pd

def research_yfinance():
    symbol = "AAPL"
    print(f"--- Researching Data for {symbol} ---")
    ticker = yf.Ticker(symbol)
    
    print("\n1. Financials (Income Statement):")
    try:
        fin = ticker.financials
        if not fin.empty:
            print(fin.head())
            print("Columns:", fin.columns)
            print("Index:", fin.index)
    except Exception as e:
        print(f"Error: {e}")

    print("\n2. Major Holders:")
    try:
        holders = ticker.major_holders
        if holders is not None:
             print(holders)
    except Exception as e:
        print(f"Error: {e}")

    print("\n3. Sustainability (ESG):")
    try:
        esg = ticker.sustainability
        if esg is not None:
            print(esg.head())
    except Exception as e:
        print(f"Error: {e}")
        
    print("\n4. Recommendations Summary:")
    try:
        recs = ticker.recommendations_summary
        if recs is not None:
            print(recs.head())
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    research_yfinance()
