import os

os.add_dll_directory(r"C:/mingw64/bin") 

import gymnasium as gym
from gymnasium import spaces
import numpy as np
import time 

import nexus_engine # My custom C++ engine!

class NexusTradingEnv(gym.Env):
    def __init__(self):
        super(NexusTradingEnv, self).__init__()
        
        # Boot up the C++ Order Book object
        self.engine = nexus_engine.OrderBook()
        
        # Action space: 3 buttons - 0 = Hold, 1 = Buy, 2 = Sell
        self.action_space = spaces.Discrete(3)
        
        # Observation is just a 1D array: [Best Bid, Best Ask]
        self.observation_space = spaces.Box(
            low=0.0, high=np.inf, shape=(2,), dtype=np.float32
        )
        
    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self.engine = nexus_engine.OrderBook()
        return self._get_obs(), {}
        
    def _get_obs(self):
        bid = self.engine.get_best_bid()
        ask = self.engine.get_best_ask()
        return np.array([bid, ask], dtype=np.float32)
        
    def step(self, action):
        if action == 1 or action == 2:
            order = nexus_engine.Order()
            order.orderId = "AI_" + str(int(time.time() * 1000))[-6:] 
            order.symbol = "NEXUS"
            order.quantity = 100 
            order.timestamp = int(time.time() * 1000)
            
            bid = self.engine.get_best_bid()
            ask = self.engine.get_best_ask()

            if action == 1: 
                order.type = nexus_engine.OrderType.BUY
                order.price = 100.0 if bid == 0.0 else bid + 0.1 
            elif action == 2: 
                order.type = nexus_engine.OrderType.SELL
                order.price = 105.0 if ask == 0.0 else ask - 0.1

            self.engine.insert_order(order)
            
        obs = self._get_obs()
        reward = 0.0
        terminated = False
        truncated = False
        
        return obs, reward, terminated, truncated, {}