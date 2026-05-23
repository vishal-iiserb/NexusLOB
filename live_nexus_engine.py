import os
import sys
import ctypes
import logging
import json
from datetime import datetime
import pytz

from alpaca.data.live import StockDataStream
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import LimitOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger("NexusEngine")

print("\n" + "="*70)
print("🚀 NEXUS QUANT ENGINE: MTF EAGLE EYE v3.1 (WEB CONNECTED)")
print("="*70)

API_KEY = "PKU2E7QDWC6JGEJVIPMW3OITPH"
SECRET_KEY = "76VqRXpZUc1v5PAwuW84fJMf5UnkWRKKVoE3yCBbFkr9"

try:
    with open("bot_memory.json", "r") as f:
        memory = json.load(f)
    SYMBOL = memory.get("target_symbol", "SPY")
except Exception:
    SYMBOL = "SPY"

logger.info(f"🎯 Target Symbol Acquired from Web Dashboard: {SYMBOL}")

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

    cpp_lib.calculate_atr.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double), ctypes.c_int]
    cpp_lib.calculate_atr.restype = ctypes.c_double
    
    cpp_lib.calculate_sma.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.c_int]
    cpp_lib.calculate_sma.restype = ctypes.c_double
    
    logger.info("⚡ Smart C++ Library with MTF capability loaded.")
except Exception as e:
    logger.error(f"Failed to load C++ library: {e}")
    sys.exit(1)

trading_client = TradingClient(API_KEY, SECRET_KEY, paper=True)
wss_client = StockDataStream(API_KEY, SECRET_KEY)
historical_client = StockHistoricalDataClient(API_KEY, SECRET_KEY)

LOOKBACK_PERIOD = 20  
MACRO_PERIOD = 200

price_history = []
volume_history = []
high_history = []
low_history = []

try:
    account = trading_client.get_account()
    logger.info(f"Connected. Running paper portfolio. Cash: ${float(account.cash):,.2f}")
except Exception as e:
    logger.error(f"Broker connection failed: {e}")
    sys.exit(1)

logger.info(f"🔥 Syncing {SYMBOL} history since morning bell to calculate daily ATR and Macro Trend...")
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
                high_history.append(float(bar.high))
                low_history.append(float(bar.low))
                
        logger.info(f"✅ Cache Loaded: Synced {len(price_history)} minutes of open market data.")
    else:
        logger.info("Market is closed. Waiting for data feeds.")
except Exception as e:
    logger.error(f"Warmup failed, collecting arrays dynamically. Error: {e}")

async def on_minute_candle(bar):
    global price_history, volume_history, high_history, low_history
    
    current_price = float(bar.close)
    current_vol = float(bar.volume)
    current_high = float(bar.high)
    current_low = float(bar.low)
    
    price_history.append(current_price)
    volume_history.append(current_vol)
    high_history.append(current_high)
    low_history.append(current_low)
    
    if len(price_history) > 500:
        price_history.pop(0)
        volume_history.pop(0)
        high_history.pop(0)
        low_history.pop(0)
        
    if len(price_history) < MACRO_PERIOD:
        logger.info(f"📊 Building initial lookback data framework... ({len(price_history)}/{MACRO_PERIOD})")
        return

    c_prices = (ctypes.c_double * LOOKBACK_PERIOD)(*price_history[-LOOKBACK_PERIOD:])
    c_volumes = (ctypes.c_double * LOOKBACK_PERIOD)(*volume_history[-LOOKBACK_PERIOD:])
    c_highs = (ctypes.c_double * LOOKBACK_PERIOD)(*high_history[-LOOKBACK_PERIOD:])
    c_lows = (ctypes.c_double * LOOKBACK_PERIOD)(*low_history[-LOOKBACK_PERIOD:])
    
    c_macro_prices = (ctypes.c_double * MACRO_PERIOD)(*price_history[-MACRO_PERIOD:])
    
    std_dev = cpp_lib.calculate_std(c_prices, LOOKBACK_PERIOD)
    vwap = cpp_lib.calculate_vwap(c_prices, c_volumes, 15)
    is_vol_spike = cpp_lib.check_volume_spike(c_volumes, LOOKBACK_PERIOD, current_vol)
    market_atr = cpp_lib.calculate_atr(c_highs, c_lows, c_prices, LOOKBACK_PERIOD)
    macro_sma = cpp_lib.calculate_sma(c_macro_prices, MACRO_PERIOD)

    trend_status = "UPTREND" if current_price > macro_sma else "DOWNTREND"
    logger.info(f"📊 {SYMBOL}: ${current_price:.2f} | VWAP: ${vwap:.2f} | ATR: ${market_atr:.2f} | 200-SMA: ${macro_sma:.2f} [{trend_status}]")

    positions = trading_client.get_all_positions()
    portfolio = {p.symbol: p for p in positions}
    is_holding = SYMBOL in portfolio

    try:
        with open("bot_memory.json", "r") as f:
            memory = json.load(f)
        win_rate = memory["win_rate"]
        stop_multiplier = memory["atr_stop_multiplier"]
        profit_multiplier = memory["atr_profit_multiplier"]
        risk_limit = memory["max_account_risk_limit"]
    except Exception:
        win_rate = 0.55
        stop_multiplier = 1.5
        profit_multiplier = 3.0
        risk_limit = 0.50

    if not is_holding:
        buy_threshold = vwap - (std_dev * 1.0)
        
        if current_price < buy_threshold and is_vol_spike == 1 and current_price > macro_sma:
            account_data = trading_client.get_account()
            buying_power = float(account_data.buying_power)
            
            risk_reward_ratio = profit_multiplier / stop_multiplier
            kelly_fraction = win_rate - ((1.0 - win_rate) / risk_reward_ratio)
            safe_allocation = max(0.05, min(kelly_fraction, risk_limit))
            
            target_allocation = buying_power * safe_allocation
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
                    logger.info(f"🔥 [ENTRY] Trend Verified. Kelly Allocation ({safe_allocation*100:.1f}%) triggered. Buying {shares_to_buy} shares at LIMIT ${limit_price}")
                except Exception as e:
                    logger.error(f"Entry order failed: {e}")
                    
    else:
        current_position = portfolio[SYMBOL]
        qty_held = int(current_position.qty)
        entry_cost = float(current_position.avg_entry_price)
        
        stop_loss_target = round(entry_cost - (market_atr * stop_multiplier), 2)
        profit_lock_target = round(entry_cost + (market_atr * profit_multiplier), 2)
        
        if current_price <= stop_loss_target:
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
                logger.info(f"⚡ [ATR STOP-LOSS HIT] Cutting loss at ${exit_limit}")
            except Exception as e:
                logger.error(f"Stop loss dispatch failure: {e}")
                
        elif current_price >= profit_lock_target:
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
                logger.info(f"💰 [ATR PROFIT CAPTURED] Selling at ${exit_limit}")
            except Exception as e:
                logger.error(f"Profit lock dispatch failure: {e}")

try:
    wss_client.subscribe_bars(on_minute_candle, SYMBOL)
    logger.info(f"Websocket pipelines active. Monitoring {SYMBOL} metrics streams...")
    wss_client.run()
except KeyboardInterrupt:
    logger.info("Engine turned off cleanly by user.")
except Exception as e:
    logger.error(f"Websocket stream disconnected: {e}")