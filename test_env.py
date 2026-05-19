from nexus_env import NexusTradingEnv

print("Testing the new PnL tracking...")
env = NexusTradingEnv()
obs, info = env.reset()

print(f"Starting Bank Account: ${env.balance:.2f} | Shares Owned: {env.position}")
print("-" * 50)

# Let's run 5 random steps to see if the math actually works
for i in range(5):
    random_action = env.action_space.sample() 
    obs, reward, terminated, truncated, info = env.step(random_action)
    
    actions = ["HOLD", "BUY", "SELL"]
    print(f"Step {i+1} | AI randomly pressed: {actions[random_action]}")
    print(f"   Reward (PnL) : ${reward:.2f}")
    print(f"   Net Worth    : ${info['net_worth']:.2f}")
    print(f"   Shares Owned : {info['position']}")
    print("-" * 50)

print("Test done! Hopefully net worth changed correctly.")