#pragma once
#include "esp_err.h"
#include "sdmmc_cmd.h"
esp_err_t storage_init();
esp_err_t usb_transfer_begin();
esp_err_t usb_transfer_end();
bool host_owns_storage();
void inputs_init();
int input_event();
bool controls_released();
bool vbus_present();

esp_err_t storage_purge_begin();
esp_err_t storage_purge_step();

void idle_light_sleep();
