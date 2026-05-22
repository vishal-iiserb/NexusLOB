import csv
from datetime import datetime, timedelta, timezone
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame

API_KEY = "PKU2E7QDWC6JGEJVIPMW3OITPH"
SECRET_KEY = "76VqRXpZUc1v5PAwuW84fJMf5UnkWRKKVoE3yCBbFkr9"
ticker = "AAPL"

print(f"Connecting to Alpaca to fetch intraday (1-min) data for {ticker}...")
client = StockHistoricalDataClient(API_KEY, SECRET_KEY)

# Fetching the last 30 days of minute data
end_date = datetime.now(timezone.utc) - timedelta(minutes=20)
start_date = end_date - timedelta(days=30)

request_params = StockBarsRequest(
    symbol_or_symbols=ticker,
    timeframe=TimeFrame.Minute, # Intraday speed!
    start=start_date,
    end=end_date
)

print("Downloading 1-minute candles... This might take 5-10 seconds.")
try:
    bars = client.get_stock_bars(request_params)
    filename = "real_market_data.csv"
    
    with open(filename, mode='w', newline='') as file:
        writer = csv.writer(file)
        # We add 'Timestamp' so our environment can track the exact date and time
        writer.writerow(["Timestamp", "Open", "High", "Low", "Close", "Volume"])
        
        if ticker in bars.data:
            total_rows = 0
            for bar in bars.data[ticker]:
                writer.writerow([bar.timestamp, bar.open, bar.high, bar.low, bar.close, bar.volume])
                total_rows += 1
                
            print(f"💥 Success! Loaded {total_rows} intraday minutes into {filename}.")
        else:
            print("No data found.")
            
except Exception as e:
    print(f"An error occurred: {e}")