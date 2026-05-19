import sys
import os
import numpy as np
import gymnasium as gym
from gymnasium import spaces

build_dir_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'build'))
sys.path.append(build_dir_path)
os.add_dll_directory(r"C:\mingw64\bin") # typical windows environment variable fix

import nexus_engine

class NexusTradingEnv(gym.Env):
    """
    my custom gym environment wrapper for vishal_coin trading.
    written to check if reinforcement learning models can interact with our core cpp engine.
    """
    def __init__(self):
        super(NexusTradingEnv, self).__init__()
        self.cpp_book = nexus_engine.OrderBook()
        
        # 3 buttons: 0 = hold, 1 = market buy, 2 = market sell
        self.action_space = spaces.Discrete(3)
        
        # what the model sees - [current_cash, current_inventory, mock_price]
        self.observation_space = spaces.Box(
            low=-np.inf, high=np.inf, shape=(3,), dtype=np.float32
        )
        
        # dynamic TRACKING var for accounting
        self.wallet_cash = 10000.0
        self.held_coins = 0
        self.time_ticker = 0
        self.game_length = 100 # max ticks per game round

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        
        # restore baseline for new ROUND
        self.cpp_book = nexus_engine.OrderBook() # instantiate fresh book to clear data
        self.wallet_cash = 10000.0
        self.held_coins = 0
        self.time_ticker = 0
    
        obs_vector = np.array([self.wallet_cash, self.held_coins, 100.0], dtype=np.float32)
        return obs_vector, {}

    def step(self, action_choice):
        self.time_ticker += 1
        
        temp_price = 100.0 # simple fallback price for testing the data loops
        score_gain = 0.0   # placeholder tracking reward points
        
        # checking what the ai decided to do
        if action_choice == 1:   # buy order
            self.wallet_cash -= temp_price
            self.held_coins += 1
        elif action_choice == 2: # sell order
            self.wallet_cash += temp_price
            self.held_coins -= 1
        else:
            pass # zero means hold, do nothing this loop
            
        # condition to stop the iteration
        is_over = self.time_ticker >= self.game_length
        
        # update the vector with our new math
        obs_vector = np.array([self.wallet_cash, self.held_coins, temp_price], dtype=np.float32)
        
        # returning the exact 5 things gymnasium expects or it breaks
        return obs_vector, float(score_gain), is_over, False, {}


#   QUICK TEST TO MAKE SURE I DIDN'T BREAK ANYTHING 
if __name__ == "__main__":
    print("--- initializing my gym sandbox ---")
    my_sandbox = NexusTradingEnv()
    
    print("testing execution of reset()...")
    start_state, debug_info = my_sandbox.reset()
    print("starting setup numbers match:", start_state)
    
    print("\nrunning 5 manual test steps with completely random choices...")
    for turn in range(1, 6):
        rand_act = my_sandbox.action_space.sample() # grab a random choice (0, 1, or 2)
        next_obs, reward_value, is_done, is_trunc, metadata = my_sandbox.step(rand_act)
        
        act_label = ["HOLD", "BUY", "SELL"][rand_act]
        print(f"Turn {turn} | Selection: {act_label} | Engine Vector State: {next_obs}")
        
    print("\n✅ framework checks out! matrix simulation is valid and ready.")