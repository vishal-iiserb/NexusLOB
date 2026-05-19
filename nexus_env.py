import os
# TODO: 
os.add_dll_directory(r"C:/mingw64/bin") 

import gymnasium as gym
from gymnasium import spaces
import numpy as np
import time 

import nexus_engine # my custom C++ baby

class NexusTradingEnv(gym.Env):
    def __init__(self):
        super(NexusTradingEnv, self).__init__()
        self.engine = nexus_engine.OrderBook()
        
        # 0 = Hold, 1 = Buy, 2 = Sell
        self.action_space = spaces.Discrete(3)
        self.observation_space = spaces.Box(
            low=0.0, high=np.inf, shape=(2,), dtype=np.float32
        )
        
        # --- THE WALLET ---
        # Giving the AI a 10k paper trading account so it has something to lose
        self.initial_balance = 10000.0  
        self.balance = self.initial_balance
        self.position = 0               # tracking how many shares it currently holds
        self.net_worth = self.initial_balance
        
    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self.engine = nexus_engine.OrderBook()
        
        # Gotta wipe the bank account clean every time the game restarts
        self.balance = self.initial_balance
        self.position = 0
        self.net_worth = self.initial_balance
        
        return self._get_obs(), {}
        
    def _get_obs(self):
        bid = self.engine.get_best_bid()
        ask = self.engine.get_best_ask()
        return np.array([bid, ask], dtype=np.float32)
        
    def step(self, action):
        # Snapshot the net worth before the trade to calculate profit later
        prev_net_worth = self.net_worth
        
        bid = self.engine.get_best_bid()
        ask = self.engine.get_best_ask()
        
        # If order book is empty, just pretend the stock is $100 so it doesn't break
        current_market_price = bid if bid > 0 else 100.0 
        
        if action == 1 or action == 2:
            order = nexus_engine.Order()
            
            # Lazy random id generation just for fun
            order.orderId = "AI_" + str(int(time.time() * 1000))[-6:] 
            order.symbol = "NEXUS"
            order.quantity = 10  # Let's just trade 10 shares at a time for now
            order.timestamp = int(time.time() * 1000)

            if action == 1: # BUY
                order.type = nexus_engine.OrderType.BUY
                order.price = 100.0 if bid == 0.0 else bid + 0.1 
                
                # Pay for the shares: Cash goes down, shares go up
                cost = order.price * order.quantity
                self.balance -= cost
                self.position += order.quantity
                
            elif action == 2: # SELL
                # NOTE TO SELF: Only let it sell if it actually owns shares! 
                # (No naked shorting yet, too complicated)
                if self.position >= order.quantity:
                    order.type = nexus_engine.OrderType.SELL
                    order.price = 105.0 if ask == 0.0 else ask - 0.1
                    
                    # Get paid: Cash goes up, shares go down
                    revenue = order.price * order.quantity
                    self.balance += revenue
                    self.position -= order.quantity

            # Fire it into the C++ engine
            self.engine.insert_order(order)
            
        # 3. Calculate new net worth AFTER the trade
        obs = self._get_obs()
        new_bid = obs[0] if obs[0] > 0 else current_market_price
        
        # Net Worth = Pure Cash + (Shares Owned * Current Share Price)
        # Using the bid price to value inventory to be conservative
        self.net_worth = self.balance + (self.position * new_bid)
        
        # 4. THE REWARD FUNCTION
        # If it made money, reward is positive. If it lost money, reward is negative.
        reward = self.net_worth - prev_net_worth
        
        terminated = False
        truncated = False
        
        # Shoving all this extra data into info so I can print it and debug it
        info = {
            "balance": self.balance,
            "position": self.position,
            "net_worth": self.net_worth,
            "profit": reward
        }
        
        return obs, reward, terminated, truncated, info