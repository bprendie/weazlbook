// SSD1677 transport and bounded BUSY handling. Panel initialization is gated
// until a matching delivered GDEY0397T81P command sequence is validated.
#include "display.hpp"
#include "board.hpp"
#include "driver/spi_master.h"
#include "esp_timer.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
static spi_device_handle_t dev;
static esp_err_t send(bool data,const void*p,size_t n){
 gpio_set_level(board::epd_dc,data);spi_transaction_t t={};t.length=n*8;t.tx_buffer=p;return spi_device_transmit(dev,&t);
}
static esp_err_t command(uint8_t c){return send(false,&c,1);}
static esp_err_t ready(){int64_t end=esp_timer_get_time()+15000000;while(gpio_get_level(board::epd_busy)){if(esp_timer_get_time()>end)return ESP_ERR_TIMEOUT;vTaskDelay(pdMS_TO_TICKS(10));}return ESP_OK;}
esp_err_t display_init(){
 gpio_set_direction(board::epd_dc,GPIO_MODE_OUTPUT);gpio_set_direction(board::epd_reset,GPIO_MODE_OUTPUT);gpio_set_direction(board::epd_busy,GPIO_MODE_INPUT);
 spi_device_interface_config_t c={};c.clock_speed_hz=4000000;c.mode=0;c.spics_io_num=board::epd_cs;c.queue_size=1;
 esp_err_t e=spi_bus_add_device(SPI2_HOST,&c,&dev);if(e!=ESP_OK)return e;
 gpio_set_level(board::epd_reset,0);vTaskDelay(pdMS_TO_TICKS(10));gpio_set_level(board::epd_reset,1);vTaskDelay(pdMS_TO_TICKS(10));
 e=ready();if(e!=ESP_OK)return e;
 // Transport available; no guessed waveform/power settings sent to raw panel.
 return ESP_ERR_NOT_SUPPORTED;
}
esp_err_t display_update(const uint8_t*){return ESP_ERR_NOT_SUPPORTED;}
esp_err_t display_sleep(){if(!dev)return ESP_ERR_INVALID_STATE;esp_err_t e=ready();if(e!=ESP_OK)return e;e=command(0x10);uint8_t deep=1;if(e==ESP_OK)e=send(true,&deep,1);return e;}
