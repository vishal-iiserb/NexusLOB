import os
os.add_dll_directory(r"C:\mingw64\bin")

import gymnasium as gym
from gymnasium import spaces
import numpy as np
import time 
import random 
import nexus_engine 

class NexusTradingEnv(gym.Env):
    def __init__(self):
        super(NexusTradingEnv, self).__init__()
        self.engine = nexus_engine.OrderBook()
        self.action_space = spaces.Discrete(3)
        self.observation_space = spaces.Box(
            low=-np.inf, high=np.inf, shape=(4,), dtype=np.float32
        )
        self.initial_balance = 10000.0  
        self.balance = self.initial_balance
        self.position = 0               
        self.net_worth = self.initial_balance
        
    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self.engine = nexus_engine.OrderBook()
        self.balance = self.initial_balance
        self.position = 0
        self.net_worth = self.initial_balance
        self._inject_noise_traders(mid_price=100.0, num_bots=10)
        return self._get_obs(), {}
        
    def _get_obs(self):
        bid = self.engine.get_best_bid()
        ask = self.engine.get_best_ask()
        return np.array([bid, ask, self.balance, self.position], dtype=np.float32)

    def _inject_noise_traders(self, mid_price, num_bots=3):
        for _ in range(num_bots):
            order = nexus_engine.Order()
            order.orderId = "BOT_" + str(int(time.time() * 1000000))[-6:] + str(random.randint(10, 99))
            order.symbol = "NEXUS"
            order.quantity = random.randint(1, 5) * 10 
            order.timestamp = int(time.time() * 1000)
            
            if random.random() > 0.5:
                order.type = nexus_engine.OrderType.BUY
                order.price = round(mid_price - random.uniform(0.1, 1.5), 2)
            else:
                order.type = nexus_engine.OrderType.SELL
                order.price = round(mid_price + random.uniform(0.1, 1.5), 2)
                
            self.engine.insert_order(order)
            
    def step(self, action):
        prev_net_worth = self.net_worth
        bid = self.engine.get_best_bid()
        ask = self.engine.get_best_ask()
        
        if bid > 0 and ask > 0:
            mid_price = (bid + ask) / 2.0
        else:
            mid_price = bid if bid > 0 else 100.0
            
        if action == 1 or action == 2:
            order = nexus_engine.Order()
            order.orderId = "AI_" + str(int(time.time() * 1000))[-6:] 
            order.symbol = "NEXUS"
            order.quantity = 10 
            order.timestamp = int(time.time() * 1000)

            if action == 1: 
                estimated_cost = round(mid_price + 0.1, 2) * order.quantity
                if self.balance >= estimated_cost:
                    order.type = nexus_engine.OrderType.BUY
                    order.price = round(mid_price + 0.1, 2) 
                    self.balance -= estimated_cost
                    self.position += order.quantity
                    self.engine.insert_order(order)
                
            elif action == 2: 
                if self.position >= order.quantity:
                    order.type = nexus_engine.OrderType.SELL
                    order.price = round(mid_price - 0.1, 2) 
                    revenue = order.price * order.quantity
                    self.balance += revenue
                    self.position -= order.quantity
                    self.engine.insert_order(order)
            
        self._inject_noise_traders(mid_price, num_bots=random.randint(1, 4))
            
        obs = self._get_obs()
        new_bid = obs[0] if obs[0] > 0 else mid_price
        
        self.net_worth = self.balance + (self.position * new_bid)
        raw_profit = self.net_worth - prev_net_worth 
        
        time_tax = 0.05
        reward = raw_profit - time_tax
        
        terminated = False
        truncated = False
        
        info = {
            "balance": self.balance,
            "position": self.position,
            "net_worth": self.net_worth,
            "profit": reward
        }
        
        return obs, reward, terminated, truncated, info