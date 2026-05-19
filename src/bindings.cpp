#include <pybind11/pybind11.h>
#include "OrderBook.h"

namespace py = pybind11;
PYBIND11_MODULE(nexus_engine, m) {
    m.doc() = "Nexus Limit Order Book - Core C++ Engine";
  // 1. Tell Python what an OrderType is (BUY/SELL)
    py::enum_<OrderType>(m, "OrderType")
        .value("BUY", OrderType::BUY)
        .value("SELL", OrderType::SELL)
        .export_values();
    py::class_<Order>(m, "Order")
        .def(py::init<std::string, std::string, OrderType, double, int, long long>());
    py::class_<OrderBook>(m, "OrderBook")
        .def(py::init<>()) // Allows Python to create an OrderBook()
        .def("insert_order", &OrderBook::insertOrder)
        .def("print_order_book", &OrderBook::printOrderBook);
}