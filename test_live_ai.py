import os
os.add_dll_directory(r"C:\mingw64\bin") 

from stable_baselines3 import PPO
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockLatestQuoteRequest
import numpy as np

API_KEY = "PKU2E7QDWC6JGEJVIPMW3OITPH"
SECRET_KEY = "76VqRXpZUc1v5PAwuW84fJMf5UnkWRKKVoE3yCBbFkr9"
ticker = "AAPL"

# 1. Load your trained AI brain
print("Loading Nexus Quant Brain...")
try:
    model = PPO.load("nexus_quant_brain")
except Exception as e:
    print(f"Error loading model: {e}")
    exit()

# 2. Connect to Alpaca
print(f"Connecting to Alpaca for live pre-market data on {ticker}...")
client = StockHistoricalDataClient(API_KEY, SECRET_KEY)
request_params = StockLatestQuoteRequest(symbol_or_symbols=ticker)

try:
    # 3. Get the absolute latest quote
    quote = client.get_stock_latest_quote(request_params)
    
    if ticker in quote:
        live_ask = float(quote[ticker].ask_price)
        live_bid = float(quote[ticker].bid_price)
        print(f"Live Market Data -> Bid: ${live_bid:.2f} | Ask: ${live_ask:.2f}")
        
        # 4. Build the AI's observation matrix
        # (Bid, Ask, Balance, Position, SMA, RSI, MACD)
        # We will use dummy starting values for balance and indicators for this single test ping
        obs = np.array([live_bid, live_ask, 10000.0, 0, live_bid, 50.0, 0.0], dtype=np.float32)
        
        # 5. Ask the AI what to do
        print("Asking the AI for a decision...")
        action, _states = model.predict(obs)
        
        if action == 0:
            print("🤖 AI Decision: HOLD (Wait for a better setup)")
        elif action == 1:
            print(f"🤖 AI Decision: BUY 10 Shares at ${live_ask:.2f}")
        elif action == 2:
            print(f"🤖 AI Decision: SELL 10 Shares at ${live_bid:.2f}")
    else:
        print("No live quote data found.")
        
except Exception as e:
    print(f"An error occurred: {e}")