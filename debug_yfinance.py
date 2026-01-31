import yfinance as yf
import pandas as pd

def check_yfinance_features(symbol):
    print(f"--- Checking yfinance for {symbol} ---")
    ticker = yf.Ticker(symbol)
    
    # 1. Dividends
    print("\n[Dividends]")
    try:
        divs = ticker.dividends
        if not divs.empty:
            print(f"Available. Last 5:\n{divs.tail(5)}")
        else:
            print("Empty.")
    except Exception as e:
        print(f"Error: {e}")

    # 2. Holders
    print("\n[Holders]")
    try:
        major = ticker.major_holders
        inst = ticker.institutional_holders
        print(f"Major Holders:\n{major}")
        print(f"Institutional Holders:\n{inst.head() if inst is not None else 'None'}")
    except Exception as e:
        print(f"Error: {e}")

    # 3. Calendar
    print("\n[Calendar]")
    try:
        cal = ticker.calendar
        print(f"Calendar available: {cal}")
    except Exception as e:
        print(f"Error: {e}")

    # 4. Peer Comparison (Sector/Industry)
    print("\n[Peer Info]")
    try:
        info = ticker.info
        print(f"Sector: {info.get('sector')}")
        print(f"Industry: {info.get('industry')}")
        print(f"Full Info Keys (Sample): {list(info.keys())[:20]}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_yfinance_features("AAPL")
