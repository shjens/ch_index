import yfinance as yf
import pandas as pd
import json
import sys

# 1. Configuration
portfolio = {
    'CFR.SW':  {'qty': 15, 'trade_price': 172.35},
    'JFN.SW':  {'qty': 15, 'trade_price': 259.00},
    'NOVN.SW': {'qty': 36, 'trade_price': 104.38},
    'ABBN.SW': {'qty': 45, 'trade_price': 57.58}
}

tickers = list(portfolio.keys())

# 2. Calculate Base Divisor
base_portfolio_value = sum(item['qty'] * item['trade_price'] for item in portfolio.values())
print(f"Base Portfolio Value (Index 100): {base_portfolio_value:.2f} CHF")

# 3. Date Setup
start_date_str = '2020-11-01'

# 4. Fetch Data
print(f"Downloading data for: {tickers}...")

# Added 'auto_adjust=False' to ensure consistent column behavior across versions
# Added 'threads=False' which sometimes helps avoid rate limits in CI environments
raw_data = yf.download(tickers, start=start_date_str, progress=False, auto_adjust=False, threads=False)

# --- DEBUGGING BLOCK ---
if raw_data.empty:
    print("!!! ERROR: Yahoo Finance returned no data. The IP might be blocked or tickers are wrong.")
    sys.exit(1)

print("Data downloaded successfully. Checking structure...")

# Handle yfinance structure variations (MultiIndex vs Single Index)
try:
    # If we have a MultiIndex (Price, Ticker), extract 'Close'
    if isinstance(raw_data.columns, pd.MultiIndex):
        data = raw_data['Close']
    else:
        # Sometimes yfinance returns a flat DF if only 1 ticker or specific settings
        # We assume 'Close' is not available in the top level if it's flat, 
        # but usually with multiple tickers, it IS a MultiIndex.
        # If it's not MultiIndex, it might be malformed for our needs.
        print(f"Columns found: {raw_data.columns}")
        # Fallback: try to just use raw_data if it looks like it has ticker columns
        data = raw_data
except KeyError as e:
    print(f"!!! ERROR: Could not find 'Close' price in data. Columns are: {raw_data.columns}")
    sys.exit(1)

# Check if all tickers are present
missing_tickers = [t for t in tickers if t not in data.columns]
if missing_tickers:
    print(f"!!! ERROR: The following tickers failed to download: {missing_tickers}")
    # We can either exit or continue. Exiting is safer to prevent bad index calculation.
    sys.exit(1)
# -----------------------

# Handle NaNs
data = data.ffill().dropna()

if data.empty:
    print("!!! ERROR: Data is empty after dropping NaNs. Check start dates or ticker validity.")
    sys.exit(1)

# 5. Build Index
data = data.copy() # Prevent SettingWithCopy warnings
data['Portfolio_Value'] = 0.0

for ticker in tickers:
    qty = portfolio[ticker]['qty']
    data['Portfolio_Value'] += data[ticker] * qty

data['Swiss_Custom_Index'] = (data['Portfolio_Value'] / base_portfolio_value) * 100

# 6. Prepare JSON Output
latest_date = data.index[-1]
latest_value = data['Swiss_Custom_Index'].iloc[-1]

output_data = {
    "meta": {
        "name": "Swiss Custom Index",
        "last_updated": latest_date.strftime('%Y-%m-%d'),
        "base_value": 100,
        "base_calculation_value": round(base_portfolio_value, 2),
        "start_date": start_date_str
    },
    "latest": {
        "date": latest_date.strftime('%Y-%m-%d'),
        "value": round(latest_value, 2)
    },
    "history": {
        date.strftime('%Y-%m-%d'): round(val, 2)
        for date, val in data['Swiss_Custom_Index'].items()
    }
}

# 7. Save to file
with open('index_data.json', 'w') as f:
    #json.dump(output_data, f, indent=4)
    f.write(output_data) # or json.dump(data, f)


print(f"Successfully generated index_data.json. Latest Value: {latest_value:.2f}")
