import os
os.add_dll_directory(r"C:\mingw64\bin") 

from stable_baselines3 import PPO
from nexus_env import NexusTradingEnv

print("Loading environment...")
env = NexusTradingEnv()

# 1. Create the model normally
model = PPO("MlpPolicy", env, verbose=1)

print("Starting training... It will stop automatically very quickly.")
# 2. Run for a very small number of steps to ensure it stops
model.learn(total_timesteps=5000)

# 3. Save and close
model.save("nexus_quant_brain")
print("Done! The script has stopped completely.")