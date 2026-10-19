#pragma once
#include "esp_err.h"
#include "sdmmc_cmd.h"
void purge_init();
bool purge_pending();
int purge_phase();
int purge_percent();
esp_err_t purge_begin(const sdmmc_card_t& card);
esp_err_t purge_check_card(const sdmmc_card_t& card);
esp_err_t purge_logical();
esp_err_t purge_overwrite_step(sdmmc_card_t& card);
esp_err_t purge_finish();
