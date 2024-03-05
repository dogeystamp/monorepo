cmake_minimum_required(VERSION 3.13)

project(sandbox)

include(pico_sdk_import.cmake)

add_executable(test)

target_sources(test PUBLIC
        ${CMAKE_CURRENT_LIST_DIR}/test.c
        ${CMAKE_CURRENT_LIST_DIR}/usb_descriptors.c
        )

# Make sure TinyUSB can find tusb_config.h
target_include_directories(test PUBLIC
        ${CMAKE_CURRENT_LIST_DIR})

pico_sdk_init()

pico_enable_stdio_usb(test 1)

target_link_libraries(test PUBLIC pico_stdlib tinyusb_device pico_unique_id)

pico_add_extra_outputs(test)
