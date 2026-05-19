import sys
import os
build_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'build'))
sys.path.append(build_path)
os.add_dll_directory(r"C:\mingw64\bin")

#importing c++ as a python library
import nexus_engine

print("\n🤖 --- PYTHON TRADING BOT INITIALIZED ---")
engine = nexus_engine.OrderBook()

print("\n[Python] Setting up the market for VISHAL_COIN...")
engine.insert_order(nexus_engine.Order("S1", "VISHAL_COIN", nexus_engine.OrderType.SELL, 105.00, 50, 1))
engine.insert_order(nexus_engine.Order("B1", "VISHAL_COIN", nexus_engine.OrderType.BUY, 100.00, 20, 2))

print("\n[Python] Asking C++ to print the Order Book:")
engine.print_order_book()

print("\n[Python] ⚡ AGGRESSIVE ALGO TRIGGERED: Crossing the spread!")
engine.insert_order(nexus_engine.Order("B2", "VISHAL_COIN", nexus_engine.OrderType.BUY, 105.00, 30, 3))

print("\n[Python] Final Order Book state:")
engine.print_order_book()