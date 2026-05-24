import sys
import ctypes
import time
import logging
import json
import os
import threading
import asyncio
from datetime import datetime
import pytz
from dhanhq import DhanContext, dhanhq, MarketFeed

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger("DhanWebSocketEngine")

print("\n" + "="*70)
print("⚡ DHAN QUANT ENGINE: MULTI-STOCK WEB SOCKET & C++ MATRIX v2.3")
print("="*70)

CLIENT_ID = "1111797766"
ACCESS_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJpc3MiOiJkaGFuIiwicGFydG5lcklkIjoiIiwiZXhwIjoxNzc5NjkyMTE3LCJpYXQiOjE3Nzk2MDU3MTcsInRva2VuQ29uc3VtZXJUeXBlIjoiU0VMRiIsIndlYmhvb2tVcmwiOiIiLCJkaGFuQ2xpZW50SWQiOiIxMTExNzk3NzY2In0.Pd8Uk2q3iy-AOu93oELy9LzbQxyOPhC-uIGq_0UQQDAO8QztaoxE12v5LHxr7NcDDzIIn-3Nh2_qaPKipDiQNA"
PAPER_TRADING = True
MEMORY_FILE = "bot_memory_india.json"
LOOKBACK_PERIOD = 20
SECURITY_ID = "11536" # ADANIENT Focus

price_history = []
volume_history = []
high_history = []
low_history = []

def load_memory():
    try:
        with open(MEMORY_FILE, 'r') as f: return json.load(f)
    except:
        return {"virtual_wallet": 10000.0, "selected_stocks": ["ADANIENT"], "active_trades": {}}

def save_memory(data):
    with open(MEMORY_FILE, 'w') as f: json.dump(data, f, indent=4)

bot_data = load_memory()

# Link C++ Shared Math Brain
try:
    if sys.platform.startswith("win"): cpp_lib = ctypes.CDLL("../nexus_math.dll")
    else: cpp_lib = ctypes.CDLL("../nexus_math.so")
    cpp_lib.calculate_std.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.c_int]
    cpp_lib.calculate_std.restype = ctypes.c_double
    cpp_lib.calculate_vwap.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double), ctypes.c_int]
    cpp_lib.calculate_vwap.restype = ctypes.c_double
    cpp_lib.check_volume_spike.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.c_int, ctypes.c_double]
    cpp_lib.check_volume_spike.restype = ctypes.c_int
    cpp_lib.calculate_atr.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double), ctypes.c_int]
    cpp_lib.calculate_atr.restype = ctypes.c_double
    logger.info("⚡ Shared C++ Math Engine linked perfectly.")
except Exception as e:
    logger.error(f"C++ Linking Error: {e}"); sys.exit(1)

dhan_context = DhanContext(CLIENT_ID, ACCESS_TOKEN)

def process_live_strategy():
    global bot_data
    if len(price_history) < LOOKBACK_PERIOD: return

    current_price = price_history[-1]
    current_vol = volume_history[-1]

    c_prices = (ctypes.c_double * LOOKBACK_PERIOD)(*price_history[-LOOKBACK_PERIOD:])
    c_volumes = (ctypes.c_double * LOOKBACK_PERIOD)(*volume_history[-LOOKBACK_PERIOD:])
    c_highs = (ctypes.c_double * LOOKBACK_PERIOD)(*high_history[-LOOKBACK_PERIOD:])
    c_lows = (ctypes.c_double * LOOKBACK_PERIOD)(*low_history[-LOOKBACK_PERIOD:])

    market_atr = cpp_lib.calculate_atr(c_highs, c_lows, c_prices, LOOKBACK_PERIOD)
    atr_pct = (market_atr / current_price) * 100

    # Read latest matrix rules from JSON notebook
    bot_data = load_memory()
    if "ADANIENT" not in bot_data["active_trades"]:
        bot_data["active_trades"]["ADANIENT"] = {"is_holding": False, "entry_price": 0.0, "shares_held": 0, "pnl": 0.0, "atr_pct": atr_pct}
    
    bot_data["active_trades"]["ADANIENT"]["atr_pct"] = atr_pct
    save_memory(bot_data)

    # Apply 1.5% target matrix requirement
    if atr_pct < 1.5:
        logger.info(f"💤 ADANIENT ATR is {atr_pct:.2f}% (Below 1.5% requirement). Skipping trade execution cycles.")
        return

    std_dev = cpp_lib.calculate_std(c_prices, LOOKBACK_PERIOD)
    vwap = cpp_lib.calculate_vwap(c_prices, c_volumes, LOOKBACK_PERIOD)
    is_vol_spike = cpp_lib.check_volume_spike(c_volumes, LOOKBACK_PERIOD, current_vol)

    logger.info(f"🟢 [TICK FEED] ADANIENT: ₹{current_price:.2f} | ATR: {atr_pct:.2f}% | VWAP: ₹{vwap:.2f}")

def on_connect(instance):
    logger.info("📡 Successfully established handshake connection to Dhan Stream Servers!")

def on_message(instance, message):
    global price_history, volume_history, high_history, low_history
    if 'last_traded_price' in message:
        ltp = float(message['last_traded_price'])
        price_history.append(ltp)
        volume_history.append(float(message.get('volume', 0)))
        high_history.append(float(message.get('high', ltp)))
        low_history.append(float(message.get('low', ltp)))
        if len(price_history) > 100:
            price_history.pop(0); volume_history.pop(0); high_history.pop(0); low_history.pop(0)
        process_live_strategy()

def start_websocket():
    subscription_instruments = [(MarketFeed.NSE, SECURITY_ID, MarketFeed.Ticker)]
    feed = MarketFeed(dhan_context, subscription_instruments, on_connect=on_connect, on_message=on_message)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(feed.connect())

ws_thread = threading.Thread(target=start_websocket, daemon=True)
ws_thread.start()
logger.info("🚀 Background streaming thread active. Awaiting real-time ticks...")

while True:
    time.sleep(1)