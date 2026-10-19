#pragma once
#include "driver/gpio.h"
namespace board {
constexpr auto mosi=GPIO_NUM_11,miso=GPIO_NUM_13,sck=GPIO_NUM_12,sd_cs=GPIO_NUM_46;
constexpr auto epd_cs=GPIO_NUM_48,epd_dc=GPIO_NUM_47,epd_reset=GPIO_NUM_21,epd_busy=GPIO_NUM_18;
constexpr auto vbus=GPIO_NUM_17;
constexpr gpio_num_t keys[]={GPIO_NUM_4,GPIO_NUM_5,GPIO_NUM_6,GPIO_NUM_7,GPIO_NUM_8,GPIO_NUM_9,GPIO_NUM_10};
// UP DOWN LEFT RIGHT SELECT BACK MARK. Physical module pins require continuity mapping.
}
