#include <iostream>
#include "OrderBook.h"

int main() {
    OrderBook engine;
    std::cout << "\n[1] Setting up the initial market...\n";
    // We add a buyer at $100 and a seller at $105. They do NOT match yet.
    engine.insertOrder({"B1", "VISHAL_COIN", OrderType::BUY, 100.00, 50, 1});
    engine.insertOrder({"S1", "VISHAL_COIN", OrderType::SELL, 105.00, 50, 2});
    engine.printOrderBook();

    std::cout << "\n[2] Aggressive Buyer Enters! Wants to buy 20 shares at $105...\n";
    // This buyer matches the seller's price! A trade should execute.
    engine.insertOrder({"B2", "VISHAL_COIN", OrderType::BUY, 105.00, 20, 3});
      // Print the book to see that 20 shares were permanently removed from the seller!
    engine.printOrderBook();

    return 0;
}