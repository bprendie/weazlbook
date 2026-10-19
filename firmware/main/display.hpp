#pragma once
#include "esp_err.h"
#include <cstdint>
esp_err_t display_init();
esp_err_t display_update(const uint8_t *portrait_frame);
esp_err_t display_sleep();
