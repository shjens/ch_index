import yfinance as yf
import pandas as pd
import json

# 1. Configuration: Define the specific portfolio
# We use the specific quantities and trade prices provided to establish the base.
portfolio = {
    'CFR.SW':  {'qty': 15, 'trade_price': 172.35},
    'JFN.SW':  {'qty': 15, 'trade_price': 259.00},
    'NOVN.SW': {'qty': 36, 'trade_price': 104.38},
    'ABBN.SW': {'qty': 45, 'trade_price': 57.58}  # Replaced RO with ABBN
}

tickers = list(portfolio.keys())

# 2. Calculate the "Base Divisor"
# This calculates the total value of the portfolio at the moment the trade prices were set.
# This total value represents Index 100.
base_portfolio_value = sum(item['qty'] * item['trade_price'] for item in portfolio.values())
print(f"Base Portfolio Value (Index 100): {base_portfolio_value:.2f} CHF")

# 3. Date Setup
# We download data starting from 2020 to ensure we have history,
# but the math is now anchored to the trade prices provided above.
start_date_str = '2020-11-01'

# 4. Fetch Data
print(f"Downloading data for: {tickers}...")
data = yf.download(tickers, start=start_date_str, progress=False)['Close']

# Handle cases where data might have NaNs (fill forward or drop)
data = data.ffill().dropna()

# 5. Build Index
# Calculate the daily value of the portfolio using the fixed quantities
data['Portfolio_Value'] = 0.0

for ticker in tickers:
    qty = portfolio[ticker]['qty']
    data['Portfolio_Value'] += data[ticker] * qty

# Normalize to Index 100 based on the calculated base value
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
    # Convert history to dictionary {date_string: value}
    "history": {
        date.strftime('%Y-%m-%d'): round(val, 2)
        for date, val in data['Swiss_Custom_Index'].items()
    }
}

# 7. Save to file
with open('index_data.json', 'w') as f:
    json.dump(output_data, f, indent=4)

print(f"Successfully generated index_data.json. Latest Value: {latest_value:.2f}")
