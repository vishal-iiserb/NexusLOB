import time
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockLatestQuoteRequest


API_KEY = "PKU2E7QDWC6JGEJVIPMW3OITPH"
SECRET_KEY = "76VqRXpZUc1v5PAwuW84fJMf5UnkWRKKVoE3yCBbFkr9"
ticker = "AAPL" 

client = StockHistoricalDataClient(API_KEY, SECRET_KEY)

print("Starting independent mega scanner for:", ticker)
print("-" * 80)

closes = []

try:
    while True:
        try:
            req = StockLatestQuoteRequest(symbol_or_symbols=ticker)
            data = client.get_stock_latest_quote(req)
            
            bid = float(data[ticker].bid_price)
            ask = float(data[ticker].ask_price)
            current_p = bid if ask == 0 else (bid + ask) / 2.0
            
            closes.append(current_p)
            if len(closes) > 35:
                closes.pop(0)
            
            # 1. SIMPLE MOVING AVERAGE (SMA)
            sma = sum(closes[-10:]) / len(closes[-10:]) if len(closes) >= 10 else sum(closes) / len(closes)
            
            # 2. RELATIVE STRENGTH INDEX (RSI)
            rsi = 50.0
            if len(closes) >= 14:
                gains, losses = 0, 0
                for i in range(len(closes) - 13, len(closes)):
                    change = closes[i] - closes[i-1]
                    if change > 0:
                        gains += change
                    else:
                        losses += abs(change)
                if losses == 0:
                    rsi = 100.0
                else:
                    rsi = 100.0 - (100.0 / (1.0 + (gains / losses)))
            
            # 3. MOVING AVERAGE CONVERGENCE DIVERGENCE (MACD)
            macd = 0.0
            if len(closes) >= 26:
                ema12 = sum(closes[-12:]) / 12
                ema26 = sum(closes[-26:]) / 26
                macd = ema12 - ema26

            # 4. CANDLESTICK / STRATEGY SCANNER
            signal = "Scanning..."
            if rsi > 70:
                signal = "OVERBOUGHT! (SELL)"
            elif rsi < 30:
                signal = "OVERSOLD! (BUY)"
            elif len(closes) >= 3 and current_p > closes[-2] * 1.0005: 
                signal = "HAMMER PATTERN!"

            t = time.strftime("%H:%M:%S", time.localtime())
            print(f"{t} | Price: ${current_p:.2f} | SMA: ${sma:.2f} | RSI: {rsi:.1f} | MACD: {macd:.4f} | Status: {signal}")
            
        except Exception as err:
            print("Skipping error:", err)
            
        time.sleep(3)

except KeyboardInterrupt:
    print("\nStopping data tracking...")