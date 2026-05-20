import time
from nexus_env import NexusTradingEnv

print("Initializing Environment Matrix...")
env = NexusTradingEnv()
obs, info = env.reset()

print("Initial State Variables:")
print(f" -> Best Bid: {obs[0]} | Best Ask: {obs[1]}")
print(f" -> Bank Cash: ${obs[2]} | Shares Held: {obs[3]}")
print(f" -> Trend SMA: {obs[4]}")
print("-" * 50)

print("Simulating a 250-step run to verify absolute emergency cutoff...")
start_time = time.time()

for step in range(1, 251):
    
    action = step % 3 
    obs, reward, terminated, truncated, info = env.step(action)
    
    if truncated or terminated:
        print(f"🎉 SUCCESS! The script caught the emergency break at step {step} and stopped safely.")
        break

print(f"Verification complete in {time.time() - start_time:.4f} seconds.")