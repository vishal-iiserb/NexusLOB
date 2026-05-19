from nexus_env import NexusTradingEnv

print("Testing the env...")
env = NexusTradingEnv()
obs, info = env.reset()
print(f"Initial state: {obs}")

# Run 5 random steps to make sure it doesn't segfault
for i in range(5):
    random_action = env.action_space.sample() # picks 0, 1, or 2 randomly
    obs, reward, terminated, truncated, info = env.step(random_action)
    
    actions = ["HOLD", "BUY", "SELL"]
    print(f"Step {i+1} | AI did: {actions[random_action]} | New state: {obs}")

print("It didn't crash!! Printing the C++ book:")
print("-" * 30)

env.engine.print_order_book()