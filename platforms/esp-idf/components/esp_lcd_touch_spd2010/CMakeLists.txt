idf_component_register(SRCS "esp_lcd_touch_spd2010.c" INCLUDE_DIRS "include" REQUIRES "esp_driver_i2c" PRIV_REQUIRES "esp_rom")

include(package_manager)
cu_pkg_define_version(${CMAKE_CURRENT_LIST_DIR})
