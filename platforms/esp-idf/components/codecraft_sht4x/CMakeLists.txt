idf_component_register(SRCS "src/codecraft_sht4x.c"
    INCLUDE_DIRS "include"
    REQUIRES esp_driver_i2c
    PRIV_REQUIRES freertos)
