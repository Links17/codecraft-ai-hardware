cmake_minimum_required(VERSION 3.22)
set(EXTRA_COMPONENT_DIRS
    "${CMAKE_CURRENT_SOURCE_DIR}/../../bsp"
    "${CMAKE_CURRENT_SOURCE_DIR}/../../../../components/codecraft_sht4x")
include($ENV{IDF_PATH}/tools/cmake/project.cmake)
idf_build_set_property(MINIMAL_BUILD ON)
project(sht4x)
