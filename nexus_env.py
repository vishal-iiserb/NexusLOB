import os
os.add_dll_directory(r"C:\mingw64\bin") 

import gymnasium as gym
from gymnasium import spaces
import numpy as np
import time 
import random 
import math
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
            low=-np.inf, high=np.inf, shape=(5,), dtype=np.float32
        )
        self.initial_balance = 10000.0  
        self.balance = self.initial_balance
        self.position = 0               
        self.net_worth = self.initial_balance
        self.price_history = []
        self.current_step = 0
        self.max_episode_steps = 200 # Fixed cutoff to prevent endless loops
        
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
 
        self._inject_noise_traders(mid_price=100.0, num_bots=5)
        return self._get_obs(), {}
        
    def _get_obs(self):
        bid, ask = 100.0, 100.0
        if self.engine is not None:
            try:
                bid = self.engine.get_best_bid()
                ask = self.engine.get_best_ask()
            except:
                pass
                
       
        if bid <= 0: bid = 100.0
        if ask <= 0: ask = 100.0
        
        sma = 100.0
        if len(self.price_history) > 0:
            sma = sum(self.price_history) / len(self.price_history)
            
        return np.array([bid, ask, self.balance, self.position, sma], dtype=np.float32)

    def _inject_noise_traders(self, mid_price, num_bots=2):
        if self.engine is None or self.current_step > self.max_episode_steps:
            return
            
        wave = 5.0 * math.sin(self.current_step / 15.0)
        trend_price = mid_price + wave
        
        for _ in range(num_bots):
            try:
                order = nexus_engine.Order()
                order.orderId = "BOT_" + str(int(time.time() * 1000000))[-6:] + str(random.randint(10, 99))
                order.symbol = "NEXUS"
                order.quantity = 10 
                order.timestamp = int(time.time() * 1000)
                
                if random.random() > 0.4:
                    order.type = nexus_engine.OrderType.BUY
                    order.price = round(trend_price - random.uniform(0.05, 0.2), 2)
                else:
                    order.type = nexus_engine.OrderType.SELL
                    order.price = round(trend_price + random.uniform(0.05, 0.2), 2)
                    
                self.engine.insert_order(order)
            except:
                pass
            
    def step(self, action):
        self.current_step += 1
        prev_net_worth = self.net_worth
        
        obs = self._get_obs()
        bid, ask = obs[0], obs[1]
        mid_price = (bid + ask) / 2.0
            
        self.price_history.append(mid_price)
        if len(self.price_history) > 10:
            self.price_history.pop(0)
            
        trade_executed = False
        
        # Action execution logic
        if action == 1: # BUY 10 shares
            estimated_cost = ask * 10
            if self.balance >= estimated_cost:
                if self.engine is not None:
                    try:
                        order = nexus_engine.Order()
                        order.orderId = "AI_" + str(int(time.time() * 1000))[-6:]
                        order.symbol = "NEXUS"
                        order.quantity = 10
                        order.type = nexus_engine.OrderType.BUY
                        order.price = ask
                        self.engine.insert_order(order)
                    except:
                        pass
                self.balance -= estimated_cost
                self.position += 10
                trade_executed = True
                
        elif action == 2: # SELL 10 shares
            if self.position >= 10:
                if self.engine is not None:
                    try:
                        order = nexus_engine.Order()
                        order.orderId = "AI_" + str(int(time.time() * 1000))[-6:]
                        order.symbol = "NEXUS"
                        order.quantity = 10
                        order.type = nexus_engine.OrderType.SELL
                        order.price = bid
                        self.engine.insert_order(order)
                    except:
                        pass
                self.balance += (bid * 10)
                self.position -= 10
                trade_executed = True
            
    
        self._inject_noise_traders(mid_price, num_bots=random.randint(1, 2))
            
      
        new_obs = self._get_obs()
        self.net_worth = self.balance + (self.position * new_obs[0])
        
        # Reward design
        reward = self.net_worth - prev_net_worth
        if (action == 1 or action == 2) and not trade_executed:
            reward -= 2.0 
        if action == 0:
            reward -= 0.1  
            
        terminated = False
        truncated = False
        
      
        if self.current_step >= self.max_episode_steps:
            truncated = True
            
        info = {
            "balance": self.balance,
            "position": self.position,
            "net_worth": self.net_worth
        }
        
        return new_obs, reward, terminated, truncated, info