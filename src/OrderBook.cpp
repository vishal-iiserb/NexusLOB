#include "OrderBook.h"
#include <algorithm>
#include <iomanip>

void OrderBook::insertOrder(const Order& order) {
    // Make a copy of the order because its quantity might decrease as it trades!
    Order currentOrder = order;

    // ==========================================
    // 1. THE MATCHING ENGINE
    // ==========================================
    if (currentOrder.type == OrderType::BUY) {
        // A Buyer wants to buy. Check the Asks (Sells) to see if we can match
        // Asks are sorted cheapest first (asks.front()), which is exactly what buyers want.
        while (currentOrder.quantity > 0 && !asks.empty() && currentOrder.price >= asks.front().price) {
            
            PriceLevel& bestAsk = asks.front();
            Order& restingOrder = bestAsk.orders.front(); // First-Come, First-Served
            
            // Decide how many shares we can actually trade
            int tradeQty = std::min(currentOrder.quantity, restingOrder.quantity);
            
            // PRINT THE TRADE RECEIPT
            std::cout << "  -> [TRADE EXECUTED] " << tradeQty << " shares of " 
                      << currentOrder.symbol << " @ $" << std::fixed << std::setprecision(2) 
                      << bestAsk.price << "\n";
            
            // Deduct the traded shares from both orders
            currentOrder.quantity -= tradeQty;
            restingOrder.quantity -= tradeQty;
            bestAsk.totalVolume -= tradeQty;
            
            // If the resting order is empty remove it from the queue
            if (restingOrder.quantity == 0) {
                bestAsk.orders.erase(bestAsk.orders.begin());
            }
            // If the whole price level is empty remove the shelf
            if (bestAsk.orders.empty()) {
                asks.erase(asks.begin());
            }
        }
    } 
    else { // OrderType:SELL
        // A Seller wants to sell. Check the Bids (Buys) to see if we can match
        // Bids are sorted highest first (bids.front()), which is exactly what sellers want.
        while (currentOrder.quantity > 0 && !bids.empty() && currentOrder.price <= bids.front().price) {
            
            PriceLevel& bestBid = bids.front();
            Order& restingOrder = bestBid.orders.front();
            
            int tradeQty = std::min(currentOrder.quantity, restingOrder.quantity);
            
            std::cout << "  -> [TRADE EXECUTED] " << tradeQty << " shares of " 
                      << currentOrder.symbol << " @ $" << std::fixed << std::setprecision(2) 
                      << bestBid.price << "\n";
            
            currentOrder.quantity -= tradeQty;
            restingOrder.quantity -= tradeQty;
            bestBid.totalVolume -= tradeQty;
            
            if (restingOrder.quantity == 0) {
                bestBid.orders.erase(bestBid.orders.begin());
            }
            if (bestBid.orders.empty()) {
                bids.erase(bids.begin());
            }
        }
    }

    // ==========================================
    // 2. ADD TO BOOK (If shares are leftover)
    // ==========================================
    if (currentOrder.quantity > 0) {
        std::vector<PriceLevel>& levels = (currentOrder.type == OrderType::BUY) ? bids : asks;

        // Check if price shelf exists
        bool shelfFound = false;
        for (auto& level : levels) {
            if (level.price == currentOrder.price) {
                level.orders.push_back(currentOrder);
                level.totalVolume += currentOrder.quantity;
                shelfFound = true;
                break;
            }
        }

        // Create new shelf if it doesn't exist
        if (!shelfFound) {
            PriceLevel newLevel;
            newLevel.price = currentOrder.price;
            newLevel.totalVolume = currentOrder.quantity;
            newLevel.orders.push_back(currentOrder);
            levels.push_back(newLevel);
            
            // Sort the book
            if (currentOrder.type == OrderType::BUY) {
                std::sort(levels.begin(), levels.end(), [](const PriceLevel& a, const PriceLevel& b) {
                    return a.price > b.price; // Descending becuase seller want highest price first.
                });
            } else {
                std::sort(levels.begin(), levels.end(), [](const PriceLevel& a, const PriceLevel& b) {
                    return a.price < b.price; // Ascending becuase byer wants lowest price first.
                });
            }
        }
    }
}

void OrderBook::printOrderBook() const {
    std::cout << "\n=========================================\n";
    std::cout << "       NEXUS QUANT ENGINE V1.0            \n";
    std::cout << "=========================================\n";

    std::cout << "[ASKS / SELLS]\n";
    if (asks.empty()) std::cout << "  (No Ask Orders)\n";
    else {
        for (auto it = asks.rbegin(); it != asks.rend(); ++it) {
            std::cout << "  Price: $" << std::fixed << std::setprecision(2) << it->price 
                      << " | Vol: " << it->totalVolume << "\n";
        }
    }

    std::cout << "-----------------------------------------\n";

    std::cout << "[BIDS / BUYS]\n";
    if (bids.empty()) std::cout << "  (No Bid Orders)\n";
    else {
        for (const auto& level : bids) {
            std::cout << "  Price: $" << std::fixed << std::setprecision(2) << level.price 
                      << " | Vol: " << level.totalVolume << "\n";
        }
    }
    std::cout << "=========================================\n\n";
}