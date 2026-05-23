import json
from flask import Flask, render_template_string, request, redirect, url_for
from alpaca.trading.client import TradingClient

app = Flask(__name__)

API_KEY = "PKU2E7QDWC6JGEJVIPMW3OITPH"
SECRET_KEY = "76VqRXpZUc1v5PAwuW84fJMf5UnkWRKKVoE3yCBbFkr9"
trading_client = TradingClient(API_KEY, SECRET_KEY, paper=True)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Nexus Quant Dashboard</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #0f172a; color: #f8fafc; max-width: 800px; margin: 40px auto; padding: 0 20px; }
        .card { background: #1e293b; padding: 24px; border-radius: 12px; margin-bottom: 24px; border: 1px solid #334155; }
        h1, h2 { margin-top: 0; color: #38bdf8; }
        .flex { display: flex; justify-content: space-between; margin-bottom: 12px; }
        select, button { padding: 10px 16px; border-radius: 6px; font-size: 16px; border: 1px solid #475569; }
        select { background: #334155; color: white; width: 60%; }
        button { background: #0284c7; color: white; cursor: pointer; font-weight: bold; width: 35%; border: none; }
        button:hover { background: #0369a1; }
        .status { font-weight: bold; color: #4ade80; }
    </style>
</head>
<body>
    <h1>📊 Nexus Quant Control Panel</h1>
    
    <div class="card">
        <h2>Portfolio Summary</h2>
        <div class="flex"><span>Account Cash:</span><span class="status">${{ "{:,.2f}".format(cash) }}</span></div>
        <div class="flex"><span>Buying Power:</span><span>${{ "{:,.2f}".format(buying_power) }}</span></div>
    </div>

    <div class="card">
        <h2>Target Strategy Configuration</h2>
        <div class="flex"><span>Currently Scanning:</span><span class="status" style="color: #f43f5e;">{{ current_symbol }}</span></div>
        <hr style="border-color: #334155; margin: 20px 0;">
        <form action="/update_symbol" method="post" class="flex">
            <select name="symbol">
                <option value="SPY" {% if current_symbol == 'SPY' %}selected{% endif %}>SPY (S&P 500 ETF)</option>
                <option value="QQQ" {% if current_symbol == 'QQQ' %}selected{% endif %}>QQQ (Nasdaq 100 ETF)</option>
                <option value="IWM" {% if current_symbol == 'IWM' %}selected{% endif %}>IWM (Russell 2000 ETF)</option>
                <option value="AAPL" {% if current_symbol == 'AAPL' %}selected{% endif %}>AAPL (Apple Inc.)</option>
                <option value="TSLA" {% if current_symbol == 'TSLA' %}selected{% endif %}>TSLA (Tesla Inc.)</option>
            </select>
            <button type="submit">Switch Ticker</button>
        </form>
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    account = trading_client.get_account()
    
    with open("bot_memory.json", "r") as f:
        memory = json.load(f)
    current_symbol = memory.get("target_symbol", "SPY")
    
    return render_template_string(
        HTML_TEMPLATE, 
        cash=float(account.cash), 
        buying_power=float(account.buying_power), 
        current_symbol=current_symbol
    )

@app.route('/update_symbol', methods=['POST'])
def update_symbol():
    selected_symbol = request.form.get('symbol')
    
    with open("bot_memory.json", "r") as f:
        memory = json.load(f)
        
    memory["target_symbol"] = selected_symbol
    
    with open("bot_memory.json", "w") as f:
        json.dump(memory, f, indent=4)
        
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, port=5000)