cmake_minimum_required (VERSION 3.10)
project (rwvolt VERSION 1.0)

include_directories (${PROJECT_BINARY_DIR}/../inc)

aux_source_directory (${PROJECT_BINARY_DIR}/../src SRC_LIST)

add_library(rwvolt_shared SHARED ${SRC_LIST})

set_target_properties(rwvolt_shared PROPERTIES OUTPUT_NAME "rwvolt")

set(LIBRARY_OUTPUT_PATH ${PROJECT_BINARY_DIR}/..)