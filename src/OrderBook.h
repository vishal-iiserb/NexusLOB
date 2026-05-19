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
};