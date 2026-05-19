#include <pybind11/pybind11.h>
#include "OrderBook.h"

namespace py = pybind11;

PYBIND11_MODULE(nexus_engine, m) {

    py::enum_<OrderType>(m, "OrderType")
        .value("BUY", OrderType::BUY)
        .value("SELL", OrderType::SELL)
        .export_values();

    py::class_<Order>(m, "Order")
        .def(py::init<>()) // Allows Python to create an empty order: order = nexus_engine.Order()
        .def_readwrite("orderId", &Order::orderId)
        .def_readwrite("symbol", &Order::symbol)
        .def_readwrite("type", &Order::type)
        .def_readwrite("price", &Order::price)
        .def_readwrite("quantity", &Order::quantity)
        .def_readwrite("timestamp", &Order::timestamp);


    py::class_<OrderBook>(m, "OrderBook")
        .def(py::init<>())
        .def("insert_order", &OrderBook::insertOrder)
        .def("print_order_book", &OrderBook::printOrderBook)
        .def("get_best_bid", &OrderBook::getBestBid)  
        .def("get_best_ask", &OrderBook::getBestAsk); 
}