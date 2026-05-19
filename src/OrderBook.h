#pragma once
#include <iostream>
#include <string>
#include <vector>

enum class OrderType { BUY, SELL };

struct Order {
    std::string orderId;
    std::string symbol;
    OrderType type;
    double price;
    int quantity;
    long long timestamp;
};

struct PriceLevel {
    double price;
    int totalVolume;
    std::vector<Order> orders;
};

class OrderBook {
private:
    std::vector<PriceLevel> bids;
    std::vector<PriceLevel> asks;

public:
    void insertOrder(const Order& order);
    void printOrderBook() const;

    // Fetch the highest active buy price for the Python AI
    double getBestBid() const {
        if (bids.empty()) {
            return 0.0; 
        }
        double bestPrice = bids[0].price;
        for (const auto& level : bids) {
            if (level.price > bestPrice) {
                bestPrice = level.price;
            }
        }
        return bestPrice;
    }

    // Fetch the lowest active sell price for the Python AI
    double getBestAsk() const {
        if (asks.empty()) {
            return 0.0; 
        }
        double bestPrice = asks[0].price;
        for (const auto& level : asks) {
            if (level.price < bestPrice) {
                bestPrice = level.price;
            }
        }
        return bestPrice;
    }
};