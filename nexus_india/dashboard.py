import streamlit as st
import json
import os
import time

st.set_page_config(page_title="Nexus Quant Dashboard", layout="wide", initial_sidebar_state="expanded")

# Custom CSS for a beautiful dark theme
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    div[data-testid="stMetricValue"] { font-size: 28px; color: #00ffcc; }
    .stDataFrame { background-color: #161b22; border-radius: 10px; }
    </style>
""", unsafe_allow_html=True)

st.title("🏹 NEXUS QUANT DESK: INDIA")
st.subheader("High-ATR Live WebSocket Portfolio Router")
st.markdown("---")

# Load Memory Function
def load_portfolio():
    if os.path.exists("bot_memory_india.json"):
        with open("bot_memory_india.json", "r") as f:
            return json.load(f)
    return {"virtual_wallet": 10000.0, "selected_stocks": [], "active_trades": {}}

data = load_portfolio()

# --- SIDEBAR: STOCK SELECTOR ---
st.sidebar.header("⚙️ Core Controls")
all_available_tickers = {
    "ADANIENT": "11536",
    "RELIANCE": "2885",
    "TATASTEEL": "3499",
    "INFY": "1594",
    "TCS": "11536"
}

chosen_tickers = st.sidebar.multiselect(
    "Select Target Assets to Trade:",
    options=list(all_available_tickers.keys()),
    default=data.get("selected_stocks", ["ADANIENT"])
)

# Save selected stocks back to JSON so the bot engine sees them instantly
if chosen_tickers != data.get("selected_stocks"):
    data["selected_stocks"] = chosen_tickers
    with open("bot_memory_india.json", "w") as f:
        json.dump(data, f, indent=4)
    st.sidebar.success("Engine tracking list updated!")

# --- MAIN METRICS PANEL ---
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Virtual Wallet Balance", f"₹{data['virtual_wallet']:.2f}")
with col2:
    total_pnl = sum(stock.get("pnl", 0.0) for stock in data["active_trades"].values())
    st.metric("Total Realized P&L", f"₹{total_pnl:+.2f}", delta=f"{total_pnl:.2f}")
with col3:
    active_positions = sum(1 for stock in data["active_trades"].values() if stock.get("is_holding"))
    st.metric("Active Working Tasks", f"{active_positions} Running")

st.markdown("### 📊 Performance Ranking (Highest Profit to Lowest)")

# --- SORTING, FILTERING & CLASSIFYING TRADES ---
rows = []
for ticker, details in data["active_trades"].items():
    if ticker in chosen_tickers:
        atr = details.get("atr_pct", 0.0)
        # Classify based on the golden 1.5% requirement discussed earlier
        volatility_status = "🔥 HIGH ATR (>1.5%)" if atr >= 1.5 else "⚠️ LOW ATR (<1.5%)"
        
        rows.append({
            "Stock Ticker": ticker,
            "Volatility Status": volatility_status,
            "Live ATR %": f"{atr:.2f}%",
            "Trading Status": "📈 HOLDING" if details["is_holding"] else "💤 IDLE",
            "Entry Price": f"₹{details['entry_price']:.2f}" if details["is_holding"] else "—",
            "Units Held": details["shares_held"],
            "Net Profit/Loss (INR)": details["pnl"]
        })

if rows:
    # Sort dynamically by Net Profit/Loss from High to Low
    sorted_rows = sorted(rows, key=lambda x: x["Net Profit/Loss (INR)"], reverse=True)
    st.dataframe(sorted_rows, use_container_width=True)
else:
    st.info("No stocks currently selected in the control sidebar panel.")

# Auto refresh the page every 2 seconds to grab updates from the core engine
time.sleep(2)
st.rerun()