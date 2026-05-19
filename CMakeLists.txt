cmake_minimum_required(VERSION 3.15)
project(NexusLOB)

set(CMAKE_CXX_STANDARD 17)
include(FetchContent)
FetchContent_Declare(
  pybind11
  GIT_REPOSITORY https://github.com/pybind/pybind11.git
  GIT_TAG v2.11.1
)
FetchContent_MakeAvailable(pybind11)
pybind11_add_module(nexus_engine src/OrderBook.cpp src/bindings.cpp)