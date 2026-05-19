import os

os.add_dll_directory(r"C:/mingw64/bin") 

import nexus_engine

print("Booting up the C++ engine...")
book = nexus_engine.OrderBook()
bid = book.get_best_bid()
ask = book.get_best_ask()

print(f"Empty Market - Best Bid: {bid}")
print(f"Empty Market - Best Ask: {ask}")
print("Bridge is completely stable!")