import json
import logging
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import GetOrdersRequest
from alpaca.trading.enums import OrderSide

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger("Optimizer")

print("\n" + "="*70)
print("🔬 NEXUS OPTIMIZER: WALK-FORWARD RE-TUNING SYSTEM v1.0")
print("="*70)

API_KEY = "PKU2E7QDWC6JGEJVIPMW3OITPH"
SECRET_KEY = "76VqRXpZUc1v5PAwuW84fJMf5UnkWRKKVoE3yCBbFkr9"

trading_client = TradingClient(API_KEY, SECRET_KEY, paper=True)

try:
    filter_params = GetOrdersRequest(status='closed', limit=100)
    closed_orders = trading_client.get_orders(filter_params)
    
    total_trades = 0
    winning_trades = 0
    
    for order in closed_orders:
        if order.side == OrderSide.SELL and order.filled_avg_price is not None:
            if float(order.filled_qty) > 0:
                total_trades += 1
                
                fill_price = float(order.filled_avg_price)
                limit_baseline = float(order.limit_price) if order.limit_price is not None else fill_price
                
                if fill_price > limit_baseline:
                    winning_trades += 1

    if total_trades > 0:
        calculated_win_rate = round(winning_trades / total_trades, 2)
        logger.info(f"Analysis complete. Found {total_trades} historical strategy cycles.")
        logger.info(f"Verified Wins: {winning_trades} | Calculated Win Rate: {calculated_win_rate * 100:.1f}%")
        
        if calculated_win_rate >= 0.55:
            new_stop_mult = 1.5
            new_profit_mult = 3.0
            regime = "stable_trend"
        else:
            new_stop_mult = 1.2
            new_profit_mult = 3.6
            regime = "high_volatility_shakeout"

        with open("bot_memory.json", "r") as f:
            memory = json.load(f)

        memory["market_regime"] = regime
        memory["win_rate"] = calculated_win_rate
        memory["atr_stop_multiplier"] = new_stop_mult
        memory["atr_profit_multiplier"] = new_profit_mult

        with open("bot_memory.json", "w") as f:
            json.dump(memory, f, indent=4)

        logger.info("✅ `bot_memory.json` has been updated with optimized risk parameters.")
    else:
        logger.warning("No historical closed orders found to run optimization models against yet.")

except Exception as e:
    logger.error(f"Walk-forward optimization routine failed: {e}")