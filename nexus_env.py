import os
os.add_dll_directory(r"C:\mingw64\bin") 

import gymnasium as gym
from gymnasium import spaces
import numpy as np
import csv
import nexus_engine 

class NexusTradingEnv(gym.Env):
    def __init__(self):
        super(NexusTradingEnv, self).__init__()
        try:
            self.engine = nexus_engine.OrderBook()
        except:
            self.engine = None
            
        self.action_space = spaces.Discrete(3)
        self.observation_space = spaces.Box(
            low=-np.inf, high=np.inf, shape=(7,), dtype=np.float32
        )
        
        self.initial_balance = 10000.0  
        self.balance = self.initial_balance
        self.position = 0               
        self.net_worth = self.initial_balance
        self.price_history = []
        self.current_step = 0
        
        # Load timestamps AND prices to detect day changes
        self.csv_timestamps = []
        self.csv_prices = []
        
        try:
            with open("real_market_data.csv", mode="r") as f:
                reader = csv.reader(f)
                header = next(reader)
                for row in reader:
                    # row[0] is timestamp (e.g., "2026-05-20T14:35:00Z")
                    # We just take the first 10 characters to get the date: "2026-05-20"
                    self.csv_timestamps.append(row[0][:10])
                    self.csv_prices.append(float(row[4]))
        except Exception as e:
            print(f"Error loading CSV file: {e}")
            
        self.max_episode_steps = len(self.csv_prices) - 1

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self.balance = self.initial_balance
        self.position = 0
        self.net_worth = self.initial_balance
        self.price_history = []
        self.current_step = 0
        
        for i in range(min(35, len(self.csv_prices))):
            self.price_history.append(self.csv_prices[i])
            self.current_step += 1
            
        return self._get_obs(), {}
        
    def _get_obs(self):
        current_real_price = self.csv_prices[self.current_step] if self.current_step < len(self.csv_prices) else 100.0
        bid, ask = current_real_price - 0.01, current_real_price + 0.01
        
        sma = current_real_price
        if len(self.price_history) > 0:
            sma = sum(self.price_history[-10:]) / len(self.price_history[-10:])
            
        rsi = 50.0
        if len(self.price_history) >= 14:
            gains, losses = 0, 0
            for i in range(len(self.price_history) - 13, len(self.price_history)):
                change = self.price_history[i] - self.price_history[i-1]
                if change > 0: gains += change
                else: losses += abs(change)
            rsi = 100.0 if losses == 0 else 100.0 - (100.0 / (1.0 + (gains / losses)))
                
        macd = 0.0
        if len(self.price_history) >= 26:
            macd = (sum(self.price_history[-12:]) / 12) - (sum(self.price_history[-26:]) / 26)
            
        return np.array([bid, ask, self.balance, self.position, sma, rsi, macd], dtype=np.float32)

    def step(self, action):
        self.current_step += 1
        prev_net_worth = self.net_worth
        
        obs = self._get_obs()
        bid, ask = obs[0], obs[1]
        mid_price = (bid + ask) / 2.0
        self.price_history.append(mid_price)
        if len(self.price_history) > 35: self.price_history.pop(0)
            
        # 1. Check if the trading day is ending right now!
        day_ended = False
        if self.current_step < len(self.csv_timestamps) - 1:
            current_day = self.csv_timestamps[self.current_step]
            next_minute_day = self.csv_timestamps[self.current_step + 1]
            
            # If the next row is a different date, the market is closing!
            if current_day != next_minute_day:
                day_ended = True

        # 2. Force liquidation rule for day-trading
        if day_ended and self.position > 0:
            # Emergency auto-sell at market close bid price
            self.balance += (bid * self.position)
            print(f"🚨 Market Close! Force-liquidating position of {self.position} shares.")
            self.position = 0
            action = 0 # Force override action to hold since we are flat
            trade_executed = True
        else:
            # Normal trading actions
            trade_executed = False
            if action == 1: # BUY 10 shares
                estimated_cost = ask * 10
                if self.balance >= estimated_cost:
                    self.balance -= estimated_cost
                    self.position += 10
                    trade_executed = True
            elif action == 2: # SELL 10 shares
                if self.position >= 10:
                    self.balance += (bid * 10)
                    self.position -= 10
                    trade_executed = True
            
        new_obs = self._get_obs()
        self.net_worth = self.balance + (self.position * new_obs[0])
        
        # Reward design
        reward = self.net_worth - prev_net_worth
        if (action == 1 or action == 2) and not trade_executed:
            reward -= 2.0 
        if action == 0:
            reward -= 0.01 # minor penalty to keep it moving
            
        terminated = False
        truncated = False
        
        if self.current_step >= self.max_episode_steps:
            terminated = True
            truncated = True
            
        return new_obs, reward, terminated, truncated, {"net_worth": self.net_worth}