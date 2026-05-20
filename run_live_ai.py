import os
os.add_dll_directory(r"C:/mingw64/bin") 

from stable_baselines3 import PPO
from nexus_env import NexusTradingEnv

print("1. Booting up the Matrix...")
env = NexusTradingEnv()

print("2. Waking up the trained AI brain...")
# This loads the 'nexus_quant_brain.zip' file
model = PPO.load("nexus_quant_brain")

# Reset the environment to give the AI a fresh $10,000 account
obs, info = env.reset()

print(f"Starting Bank Account: ${env.balance:.2f}")
print("=" * 50)

for i in range(15):
  # ai look at the observation and predict 
    action, _states = model.predict(obs, deterministic=True)
    
   
    obs, reward, terminated, truncated, info = env.step(int(action))
    
    actions = ["HOLD", "BUY", "SELL"]
    print(f"Step {i+1} | AI Decision: {actions[action]}")
    print(f"   Reward (PnL) : ${reward:.2f}")
    print(f"   Net Worth    : ${info['net_worth']:.2f}")
    print(f"   Shares Owned : {info['position']}")
    print("-" * 50)

print("Simulation complete! Check the final Net Worth above.")