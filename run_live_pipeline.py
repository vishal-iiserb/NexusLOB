import time
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockLatestQuoteRequest

API_KEY = "PKU2E7QDWC6JGEJVIPMW3OITPH"
SECRET_KEY = "76VqRXpZUc1v5PAwuW84fJMf5UnkWRKKVoE3yCBbFkr9"
ticker = "AAPL" 

client = StockHistoricalDataClient(API_KEY, SECRET_KEY)

print("Starting data collector for:", ticker)
print("Time      | Price   | SMA     | Status")
print("-" * 50)

prices = []

try:
    while True:
        try:
            req = StockLatestQuoteRequest(symbol_or_symbols=ticker)
            data = client.get_stock_latest_quote(req)
            
            bid = float(data[ticker].bid_price)
            ask = float(data[ticker].ask_price)
            
            if ask == 0:
                current_p = bid
            else:
                current_p = (bid + ask) / 2.0
            
            prices.append(current_p)
            if len(prices) > 10:
                prices.pop(0)
                
            sma = sum(prices) / len(prices)
            
            signal = "Scanning..."
            if len(prices) >= 3:
                if current_p > prices[-2] * 1.0005: 
                    signal = "HAMMER DETECTED!"

            t = time.strftime("%H:%M:%S", time.localtime())
            print(f"{t} | ${current_p:.2f} | ${sma:.2f} | {signal}")
            
        except Exception as err:
            print("Error occurred but skipping:", err)
            
        time.sleep(3)

except KeyboardInterrupt:
    print("\nStopping the script...")