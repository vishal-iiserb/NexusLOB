import os
import sys
import ctypes
import logging
from datetime import datetime
import pytz

from alpaca.data.live import StockDataStream
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import LimitOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce

# Set up clean logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger("NexusEngine")

print("\n" + "="*70)
print("🚀 NEXUS HYBRID ENGINE: INSTITUTIONAL VWAP & TRAILING LOCK")
print("="*70)

# --- 1. CONFIGURATION & KEYS ---
API_KEY = "PKU2E7QDWC6JGEJVIPMW3OITPH"
SECRET_KEY = "76VqRXpZUc1v5PAwuW84fJMf5UnkWRKKVoE3yCBbFkr9"
SYMBOL = "SPY"

# --- 2. LOAD HIGH-SPEED C++ LIBRARY ---
try:
    if sys.platform.startswith("win"):
        cpp_lib = ctypes.CDLL("./nexus_math.dll")
    else:
        cpp_lib = ctypes.CDLL("./nexus_math.so")
        
    cpp_lib.calculate_std.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.c_int]
    cpp_lib.calculate_std.restype = ctypes.c_double

    cpp_lib.calculate_vwap.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double), ctypes.c_int]
    cpp_lib.calculate_vwap.restype = ctypes.c_double

    cpp_lib.check_volume_spike.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.c_int, ctypes.c_double]
    cpp_lib.check_volume_spike.restype = ctypes.c_int
    logger.info("⚡ C++ Core loaded successfully.")
except Exception as e:
    logger.error(f"Failed to load C++ shared library: {e}")
    sys.exit(1)

# --- 3. INITIALIZE BROKER CONNECTIONS ---
trading_client = TradingClient(API_KEY, SECRET_KEY, paper=True)
wss_client = StockDataStream(API_KEY, SECRET_KEY)
historical_client = StockHistoricalDataClient(API_KEY, SECRET_KEY)

# --- 4. ENGINE STATE & ARRAYS ---
LOOKBACK_PERIOD = 30
VWAP_PERIOD = 15

price_history = []
volume_history = []

try:
    account = trading_client.get_account()
    logger.info(f"Connected to Alpaca. Current Liquidity: ${float(account.cash):,.2f}")
except Exception as e:
    logger.error(f"Broker connection failed: {e}")
    sys.exit(1)

# --- 5. INSTANT WARMUP ALGORITHM (FROM 9:30 AM EST) ---
logger.info("🔥 Initiating Instant Cache Warmup from Market Open...")
try:
    eastern = pytz.timezone('US/Eastern')
    now_est = datetime.now(eastern)
    market_open = now_est.replace(hour=9, minute=30, second=0, microsecond=0)
    
    if now_est > market_open:
        request_params = StockBarsRequest(
            symbol_or_symbols=SYMBOL,
            timeframe=TimeFrame.Minute,
            start=market_open,
            end=now_est
        )
        
        historical_bars = historical_client.get_stock_bars(request_params)
        
        if SYMBOL in historical_bars.data:
            bars_today = historical_bars.data[SYMBOL]
            for bar in bars_today:
                price_history.append(float(bar.close))
                volume_history.append(float(bar.volume))
                
        logger.info(f"✅ Cache Warmed: Pre-loaded {len(price_history)} bars since morning bell.")
    else:
        logger.info("Market has not opened yet today. Waiting for live data.")
except Exception as e:
    logger.error(f"Warmup failed, building cache live. Error: {e}")

# --- 6. ULTRA-LOW OVERHEAD EVENT LISTENER ---
async def on_minute_candle(bar):
    global price_history, volume_history
    
    current_price = float(bar.close)
    current_vol = float(bar.volume)
    
    price_history.append(current_price)
    volume_history.append(current_vol)
    
    if len(price_history) > 500:
        price_history.pop(0)
        volume_history.pop(0)
        
    logger.info(f"📊 Market Update | {SYMBOL} Price: ${current_price:.2f} | Volume: {int(current_vol)}")

    if len(price_history) < LOOKBACK_PERIOD:
        return

    c_prices = (ctypes.c_double * LOOKBACK_PERIOD)(*price_history[-LOOKBACK_PERIOD:])
    c_volumes = (ctypes.c_double * LOOKBACK_PERIOD)(*volume_history[-LOOKBACK_PERIOD:])
    
    std_dev = cpp_lib.calculate_std(c_prices, LOOKBACK_PERIOD)
    vwap = cpp_lib.calculate_vwap(c_prices, c_volumes, VWAP_PERIOD)
    is_vol_spike = cpp_lib.check_volume_spike(c_volumes, LOOKBACK_PERIOD, current_vol)

    positions = trading_client.get_all_positions()
    portfolio = {p.symbol: p for p in positions}
    is_holding = SYMBOL in portfolio

    # --- 7. AGGRESSIVE EXECUTION & TRAILING LOCK LOGIC ---
    if not is_holding:
        buy_threshold = vwap - (std_dev * 1.0)
        
        if current_price < buy_threshold and is_vol_spike == 1:
            account_data = trading_client.get_account()
            buying_power = float(account_data.buying_power)
            
            target_allocation = buying_power * 0.90 
            shares_to_buy = int(target_allocation / current_price)
            
            if shares_to_buy > 0:
                limit_price = round(current_price * 1.0001, 2) 
                try:
                    buy_order = LimitOrderRequest(
                        symbol=SYMBOL,
                        qty=shares_to_buy,
                        side=OrderSide.BUY,
                        time_in_force=TimeInForce.DAY,
                        limit_price=limit_price
                    )
                    trading_client.submit_order(order_data=buy_order)
                    logger.info(f"🔥 [ENTRY TRIGGERED] Entering long: {shares_to_buy} shares at LIMIT ${limit_price}")
                except Exception as e:
                    logger.error(f"Order routing failed: {e}")
                    
    else:
        current_position = portfolio[SYMBOL]
        qty_held = int(current_position.qty)
        entry_cost = float(current_position.avg_entry_price)
        
        return_pct = (current_price - entry_cost) / entry_cost
        
        # 1. HARD STOP-LOSS: Safety net (-0.10%)
        if return_pct <= -0.0010:
            exit_limit = round(current_price * 0.9999, 2)
            try:
                sell_order = LimitOrderRequest(
                    symbol=SYMBOL,
                    qty=qty_held,
                    side=OrderSide.SELL,
                    time_in_force=TimeInForce.DAY,
                    limit_price=exit_limit
                )
                trading_client.submit_order(order_data=sell_order)
                logger.info(f"⚡ [STOP-LOSS TRIGGERED] Closing via STOP | Selling {qty_held} shares at LIMIT ${exit_limit}")
            except Exception as e:
                logger.error(f"Exit transmission failure: {e}")
                
        # 2. DYNAMIC TRAILING PROFIT LOCK 
        elif return_pct >= 0.0020:
            if current_price < (entry_cost * 1.0020): 
                exit_limit = round(current_price * 0.9999, 2)
                try:
                    sell_order = LimitOrderRequest(
                        symbol=SYMBOL,
                        qty=qty_held,
                        side=OrderSide.SELL,
                        time_in_force=TimeInForce.DAY,
                        limit_price=exit_limit
                    )
                    trading_client.submit_order(order_data=sell_order)
                    logger.info(f"⚡ [TRAILING LOCK] Momentum stalled. Closing with profit at LIMIT ${exit_limit}")
                except Exception as e:
                    logger.error(f"Exit transmission failure: {e}")

# --- 8. INITIALIZE WEBSOCKET STREAM ---
try:
    wss_client.subscribe_bars(on_minute_candle, SYMBOL)
    logger.info(f"Monitoring {SYMBOL} infrastructure pipelines...")
    wss_client.run()
except KeyboardInterrupt:
    logger.info("Engine safely disconnected via user command.")
except Exception as e:
    logger.error(f"Stream interface crashed: {e}")