from alpaca.trading.client import TradingClient
API_KEY = "PKU2E7QDWC6JGEJVIPMW3OITPH"
SECRET_KEY = "76VqRXpZUc1v5PAwuW84fJMf5UnkWRKKVoE3yCBbFkr9"


print("🔄 Attempting to handshake with Alpaca Sandbox Servers...")

try:
    client = TradingClient(API_KEY, SECRET_KEY, paper=True)
    
    # Request my account details from the server
    account = client.get_account()
    
    print("\n🎉 CONNECTION SUCCESSFUL!")
    print(f" -> Account Status: {account.status}")
    print(f" -> Sandbox Currency: {account.currency}")
    print(f" -> Available Buying Power: ${float(account.buying_power):,.2f}")
    print(f" -> Starting Cash Balance: ${float(account.cash):,.2f}")
    print("\nYour Python environment is now officially talking to the live market pipeline!")

except Exception as e:
    print("\n❌ CONNECTION FAILED!")
    print(f"Error Details: {e}")
    print("Please double-check that you copied the keys exactly and didn't leave out any characters.")