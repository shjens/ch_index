import yfinance as yf
import pandas as pd
import json
import os

# 1. Configuration
tickers = ['NOVN.SW', 'JFN.SW', 'RO.SW', 'CFR.SW']
weights_map = {
    'NOVN.SW': 0.30,
    'JFN.SW': 0.30,
    'RO.SW': 0.20,
    'CFR.SW': 0.20
}

# 2. Date Setup
start_date_str = '2020-11-01'
index_100_date = pd.to_datetime('2020-11-02')
base_value = 100

# 3. Fetch Data
print(f"Downloading data...")
data = yf.download(tickers, start=start_date_str, progress=False)['Close']

# 4. Locate Start Date
if start_date_str not in data.index:
    actual_start_date = data.index[data.index > start_date_str][0]
else:
    actual_start_date = pd.Timestamp(start_date_str)

data = data.loc[actual_start_date:].copy()

# 5. Calculate Fixed Shares
initial_prices = data.loc[index_100_date].copy()
fixed_shares = {}

for ticker in tickers:
    weight = weights_map[ticker]
    start_price = initial_prices[ticker]
    allocated_capital = base_value * weight
    fixed_shares[ticker] = allocated_capital / start_price

# 6. Build Index
data['Swiss_Custom_Index'] = 0.0
for ticker in tickers:
    data['Swiss_Custom_Index'] += data[ticker] * fixed_shares[ticker]

# 7. Prepare JSON Output
# We want the latest value, plus perhaps the last 30 days of history for charts
latest_date = data.index[-1]
latest_value = data['Swiss_Custom_Index'].iloc[-1]

# Create a clean dictionary structure
output_data = {
    "meta": {
        "name": "Swiss Custom Index",
        "last_updated": latest_date.strftime('%Y-%m-%d'),
        "base_value": base_value,
        "start_date": start_date_str
    },
    "latest": {
        "date": latest_date.strftime('%Y-%m-%d'),
        "value": round(latest_value, 2)
    },
    # Convert the whole index history to a dictionary {date: value}
    "history": data['Swiss_Custom_Index'].round(2).to_dict()
}

# Fix Timestamp keys in history to be strings
# Pandas to_dict() might leave keys as Timestamps, which JSON hates
output_data["history"] = {k.strftime('%Y-%m-%d'): v for k, v in output_data["history"].items()}

# 8. Save to file
with open('index_data.json', 'w') as f:
    json.dump(output_data, f, indent=4)

print("Successfully generated index_data.json")
