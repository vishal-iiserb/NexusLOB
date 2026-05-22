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
        except Exception as e:
            print(f"Error loading C++ Engine: {e}")
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
        
        # Load the real historical CSV data into memory using simple loops
        self.csv_prices = []
        try:
            with open("real_market_data.csv", mode="r") as f:
                reader = csv.reader(f)
                header = next(reader) 
                for row in reader:
                    close_price = float(row[4])
                    self.csv_prices.append(close_price)
        except Exception as e:
            print(f"Error loading CSV file: {e}")
        
        self.max_episode_steps = len(self.csv_prices) - 1
        if self.max_episode_steps <= 0:
            self.max_episode_steps = 200 # fallback

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        
        if self.engine is not None:
            try:
                self.engine = nexus_engine.OrderBook()
            except:
                pass
                
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
        # Read the active real price from our loaded historical list
        current_real_price = 100.0
        if self.current_step < len(self.csv_prices):
            current_real_price = self.csv_prices[self.current_step]
            
        # Since we are backtesting offline, simulate spread around the historical price
        bid = current_real_price - 0.02
        ask = current_real_price + 0.02
        
        sma = current_real_price
        if len(self.price_history) > 0:
            sma = sum(self.price_history[-10:]) / len(self.price_history[-10:])
            
        rsi = 50.0
        if len(self.price_history) >= 14:
            gains, losses = 0, 0
            for i in range(len(self.price_history) - 13, len(self.price_history)):
                change = self.price_history[i] - self.price_history[i-1]
                if change > 0:
                    gains += change
                else:
                    losses += abs(change)
            if losses == 0:
                rsi = 100.0
            else:
                rsi = 100.0 - (100.0 / (1.0 + (gains / losses)))
                
        macd = 0.0
        if len(self.price_history) >= 26:
            ema12 = sum(self.price_history[-12:]) / 12
            ema26 = sum(self.price_history[-26:]) / 26
            macd = ema12 - ema26
            
        return np.array([bid, ask, self.balance, self.position, sma, rsi, macd], dtype=np.float32)

    def step(self, action):
        self.current_step += 1
        prev_net_worth = self.net_worth
        
        obs = self._get_obs()
        bid, ask = obs[0], obs[1]
        mid_price = (bid + ask) / 2.0
            
        self.price_history.append(mid_price)
        if len(self.price_history) > 35:
            self.price_history.pop(0)
            
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
        
        # Reward function focused on net worth changes
        reward = self.net_worth - prev_net_worth
        if (action == 1 or action == 2) and not trade_executed:
            reward -= 2.0 
        if action == 0:
            reward -= 0.05 # minor holding fee
            
        terminated = False
        truncated = False
        
        if self.current_step >= self.max_episode_steps:
            terminated = True
            truncated = True
            
        info = {
            "balance": self.balance,
            "position": self.position,
            "net_worth": self.net_worth
        }
        
        return new_obs, reward, terminated, truncated, info