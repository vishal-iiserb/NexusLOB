import sys
import os
import random
import time

build_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'build'))
sys.path.append(build_path)
os.add_dll_directory(r"C:\mingw64\bin") # fix for windows dll error

import nexus_engine

print("Testing Nexus Quant Engine speed...")

engine = nexus_engine.OrderBook()
num_orders = 50000  # testing with 50k 

print(f"Generating {num_orders} random orders for VISHAL_COIN...")

orders = [] 
for i in range(num_orders):
    order_id = f"R{i}"
    
    # flip coin for buy or sell
    if random.random() > 0.5:
        order_type = nexus_engine.OrderType.BUY
    else:
        order_type = nexus_engine.OrderType.SELL
        
    price = round(random.uniform(95.00, 105.00), 2)
    qty = random.randint(1, 100)
    
    orders.append((order_id, order_type, price, qty, i))

print("Starting the test...")

# start timer
start = time.perf_counter()

# insert all orders
for o_id, o_type, price, qty, ts in orders:
    # print(f"inserting {o_id}")  # DON'T UNCOMMENT THIS! freezes the terminal lol
    engine.insert_order(nexus_engine.Order(o_id, "VISHAL_COIN", o_type, price, qty, ts))

# stop timer
end = time.perf_counter()

# calculate stats
total_time = end - start
tps = num_orders / total_time
latency = (total_time / num_orders) * 1_000_000

print("\n--- RESULTS ---")
print(f"Total orders: {num_orders}")
print(f"Time taken: {total_time:.4f} sec")
print(f"Avg latency: {latency:.2f} microseconds")
print(f"TPS (Trades Per Second): {tps:.2f}")