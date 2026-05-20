from stable_baselines3 import PPO
from nexus_env import NexusTradingEnv
import os
os.add_dll_directory(r"C:/mingw64/bin") 

print("Booting up the trading environment...")
env = NexusTradingEnv()

print("Attaching the PPO brain...")
model = PPO("MlpPolicy", env, verbose=1)

print("Starting the training montage... (10,000 steps)")
model.learn(total_timesteps=100000)

print("Training finished! Saving the data to disk...")
model.save("nexus_quant_brain")

print("SUCCESS: Brain saved as 'nexus_quant_brain.zip'!")