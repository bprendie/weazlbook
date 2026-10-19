#include "hardware.hpp"
#include "security.hpp"
#include "purge.hpp"
#include "esp_system.h"
#include "esp_sleep.h"
#include <sys/stat.h>
#include "board.hpp"
#include "core.hpp"
#include "driver/spi_master.h"
#include "driver/sdspi_host.h"
#include "tinyusb.h"
#include "tinyusb_default_config.h"
#include "tinyusb_msc.h"
#include "tusb.h"
#include "diskio_sdmmc.h"
#include "ff.h"
#include "esp_timer.h"
#include "esp_log.h"
#include "esp_check.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include <cstring>
static tinyusb_msc_storage_handle_t storage;
static sdmmc_card_t card;
static bool installed=false,host=false;
static wb::Debounce debounce[7];
static const tusb_desc_device_t desc={sizeof(tusb_desc_device_t),TUSB_DESC_DEVICE,0x0200,0,0,0,64,0x303a,0x4002,0x0100,1,2,3,1};
static const uint8_t config[]={TUD_CONFIG_DESCRIPTOR(1,1,0,TUD_CONFIG_DESC_LEN+TUD_MSC_DESC_LEN,TUSB_DESC_CONFIG_ATT_SELF_POWERED,500),TUD_MSC_DESCRIPTOR(0,4,0x01,0x81,64)};
static const char*strings[]={"\x09\x04","WeazlBook","R05 transfer prototype","R05-UNQUALIFIED","Book storage"};
static esp_err_t require_fat32(){
 BYTE drive=ff_diskio_get_pdrv_card(&card);if(drive==0xff)return ESP_ERR_INVALID_STATE;
 char path[12];snprintf(path,sizeof(path),"%u:",unsigned(drive));DWORD free_clusters;FATFS*fs=nullptr;
 if(f_getfree(path,&free_clusters,&fs)!=FR_OK||!fs||fs->fs_type!=FS_FAT32){ESP_LOGE("storage","Use a preformatted FAT32 SD card; card was not formatted");return ESP_ERR_NOT_SUPPORTED;}return ESP_OK;
}
static esp_err_t mount_card(bool fresh=false){
 tinyusb_msc_storage_config_t c={};c.mount_point=TINYUSB_MSC_STORAGE_MOUNT_APP;c.medium.card=&card;c.fat_fs.base_path="/books";c.fat_fs.config.max_files=5;c.fat_fs.config.format_if_mount_failed=fresh;c.fat_fs.do_not_format=!fresh;c.fat_fs.format_flags=FM_FAT32;
 return tinyusb_msc_new_storage_sdmmc(&c,&storage);
}
static void about_template(){
 struct stat st;if(!stat("/books/about.md",&st))return;
 FILE*f=fopen("/books/about.md","w");if(!f)return;
 fputs("# About this We4zLbo0k\n\n## Reader name\nYour name or nickname\n\n## If found\nPlease contact me using the details below.\n\n## Contact\nEmail or phone (optional)\n\n## Return instructions\nAdd a safe way to return this reader.\n",f);fclose(f);
}
esp_err_t storage_init(){
 spi_bus_config_t bus={};bus.mosi_io_num=board::mosi;bus.miso_io_num=board::miso;bus.sclk_io_num=board::sck;bus.quadwp_io_num=-1;bus.quadhd_io_num=-1;bus.max_transfer_sz=4096;
 ESP_RETURN_ON_ERROR(spi_bus_initialize(SPI2_HOST,&bus,SPI_DMA_CH_AUTO),"storage","SPI");
 gpio_set_direction(board::epd_cs,GPIO_MODE_OUTPUT);gpio_set_level(board::epd_cs,1);
 sdmmc_host_t h=SDSPI_HOST_DEFAULT();h.slot=SPI2_HOST;h.max_freq_khz=10000;
 sdspi_device_config_t d=SDSPI_DEVICE_CONFIG_DEFAULT();d.host_id=SPI2_HOST;d.gpio_cs=board::sd_cs;
 sdspi_dev_handle_t device;
 ESP_RETURN_ON_ERROR(sdspi_host_init(),"storage","SDSPI");
 ESP_RETURN_ON_ERROR(sdspi_host_init_device(&d,&device),"storage","SD device");h.slot=device;
 ESP_RETURN_ON_ERROR(sdmmc_card_init(&h,&card),"storage","Card unavailable; no automatic formatting");
 if(purge_pending()){
  ESP_RETURN_ON_ERROR(purge_check_card(card),"wipe","Original SD card required; no other card will be wiped");
  if(purge_phase()==1)return mount_card();
  return ESP_OK;
 }
 ESP_RETURN_ON_ERROR(mount_card(),"storage","Mount existing FAT32");
 ESP_RETURN_ON_ERROR(require_fat32(),"storage","FAT32 required");about_template();return ESP_OK;
}
esp_err_t usb_transfer_begin(){
 if(device_locked()||purge_pending())return ESP_ERR_INVALID_STATE;
 if(host||!storage)return ESP_ERR_INVALID_STATE;
 // Caller has committed NVS state and destroyed parser objects/closed all files.
 esp_err_t e=tinyusb_msc_set_storage_mount_point(storage,TINYUSB_MSC_STORAGE_MOUNT_USB);if(e!=ESP_OK)return e;
 host=true;
 tinyusb_config_t c=TINYUSB_DEFAULT_CONFIG();c.phy.self_powered=true;c.phy.vbus_monitor_io=board::vbus;
 c.descriptor.device=&desc;c.descriptor.full_speed_config=config;c.descriptor.string=strings;c.descriptor.string_count=5;
 e=tinyusb_driver_install(&c);if(e!=ESP_OK){host=false;tinyusb_msc_set_storage_mount_point(storage,TINYUSB_MSC_STORAGE_MOUNT_APP);return e;}installed=true;return ESP_OK;
}
esp_err_t usb_transfer_end(){
 if(!host)return ESP_ERR_INVALID_STATE;
 // Caller only invokes after physical detach. Host eject alone is not yet used.
 if(vbus_present())return ESP_ERR_INVALID_STATE;
 if(installed){tud_disconnect();vTaskDelay(pdMS_TO_TICKS(20));ESP_RETURN_ON_ERROR(tinyusb_driver_uninstall(),"usb","stop");installed=false;}
 esp_err_t e=tinyusb_msc_set_storage_mount_point(storage,TINYUSB_MSC_STORAGE_MOUNT_APP);if(e==ESP_OK){host=false;e=require_fat32();}return e;
}
bool host_owns_storage(){return host;}
void inputs_init(){gpio_config_t c={};for(auto p:board::keys)c.pin_bit_mask|=1ULL<<p;c.mode=GPIO_MODE_INPUT;c.pull_up_en=GPIO_PULLUP_ENABLE;ESP_ERROR_CHECK(gpio_config(&c));gpio_set_direction(board::vbus,GPIO_MODE_INPUT);gpio_set_pull_mode(board::vbus,GPIO_FLOATING);}
int input_event(){
 static bool previous[7]={},chord=false;static uint32_t mark_start=0;
 uint32_t now=esp_timer_get_time()/1000;int event=-1;
 for(int i=0;i<7;i++)debounce[i].update(gpio_get_level(board::keys[i])==0,now);
 if(debounce[5].held()&&debounce[6].held()&&!chord){chord=true;event=7;}
 for(int i=0;i<7;i++){bool down=debounce[i].held();if(i<5&&down&&!previous[i]&&event!=7)event=i;
 if(i==6&&down&&!previous[i])mark_start=now;
 if(i>=5&&!down&&previous[i]&&!chord)event=i==6&&uint32_t(now-mark_start)>=600?8:i;
 previous[i]=down;}
 if(!debounce[5].held()&&!debounce[6].held())chord=false;return event;
}
bool controls_released(){for(auto p:board::keys)if(!gpio_get_level(p))return false;return true;}
bool vbus_present(){return gpio_get_level(board::vbus)!=0;}

esp_err_t storage_purge_begin(){if(host||!storage)return ESP_ERR_INVALID_STATE;auto e=purge_begin(card);if(e==ESP_OK)esp_restart();return e;}
esp_err_t storage_purge_step(){
 if(host||!purge_pending())return ESP_ERR_INVALID_STATE;
 if(purge_phase()==1){auto e=purge_logical();if(e!=ESP_OK)return e;}
 if(storage&&purge_phase()==2){auto e=tinyusb_msc_delete_storage(storage);if(e!=ESP_OK)return e;storage=nullptr;}
 if(purge_phase()==2){auto e=purge_overwrite_step(card);ESP_LOGI("wipe","Card overwrite %d%%",purge_percent());return e;}
 if(purge_phase()==3){if(!storage){auto e=mount_card(true);if(e!=ESP_OK)return e;}auto e=require_fat32();if(e!=ESP_OK)return e;about_template();return purge_finish();}
 return ESP_ERR_INVALID_STATE;
}

void idle_light_sleep(){
 if(host||purge_pending()||!controls_released())return;
 for(auto pin:board::keys)gpio_wakeup_enable(pin,GPIO_INTR_LOW_LEVEL);
 gpio_wakeup_enable(board::vbus,vbus_present()?GPIO_INTR_LOW_LEVEL:GPIO_INTR_HIGH_LEVEL);
 if(esp_sleep_enable_gpio_wakeup()==ESP_OK)esp_light_sleep_start();
}
