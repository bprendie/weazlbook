#include "purge.hpp"
#include "nvs.h"
#include "nvs_flash.h"
#include "esp_heap_caps.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include <algorithm>
#include <atomic>
#include <cstdio>
#include <cstring>
#include <dirent.h>
#include <sys/stat.h>
#include <unistd.h>
#include <string>
static nvs_handle_t journal;
static std::atomic<uint8_t> phase{0};
static std::atomic<uint32_t> cursor{0};static uint32_t total;
static sdmmc_cid_t cid;
void purge_init(){ESP_ERROR_CHECK(nvs_flash_init_partition("wipe"));ESP_ERROR_CHECK(nvs_open_from_partition("wipe","journal",NVS_READWRITE,&journal));uint8_t saved_phase=0;auto e=nvs_get_u8(journal,"phase",&saved_phase);phase=saved_phase;if(e!=ESP_ERR_NVS_NOT_FOUND)ESP_ERROR_CHECK(e);if(phase){if(phase>3)ESP_ERROR_CHECK(ESP_ERR_INVALID_STATE);size_t n=sizeof(cid);ESP_ERROR_CHECK(nvs_get_blob(journal,"cid",&cid,&n));ESP_ERROR_CHECK(nvs_get_u32(journal,"total",&total));uint32_t saved_cursor=0;ESP_ERROR_CHECK(nvs_get_u32(journal,"cursor",&saved_cursor));cursor=saved_cursor;if(cursor>total)ESP_ERROR_CHECK(ESP_ERR_INVALID_STATE);}}
bool purge_pending(){return phase!=0;}
int purge_phase(){return phase;}
int purge_percent(){return total?int(uint64_t(cursor)*100/total):0;}
esp_err_t purge_begin(const sdmmc_card_t&card){if(phase)return ESP_ERR_INVALID_STATE;cid=card.cid;total=card.csd.capacity;cursor=0;esp_err_t e=nvs_set_blob(journal,"cid",&cid,sizeof(cid));if(e==ESP_OK)e=nvs_set_u32(journal,"total",total);if(e==ESP_OK)e=nvs_set_u32(journal,"cursor",0);if(e==ESP_OK)e=nvs_set_u8(journal,"phase",1);if(e==ESP_OK)e=nvs_commit(journal);if(e==ESP_OK)phase=1;return e;}
esp_err_t purge_check_card(const sdmmc_card_t&card){return card.csd.capacity==total&&memcmp(&card.cid,&cid,sizeof(cid))==0?ESP_OK:ESP_ERR_INVALID_STATE;}
static bool remove_tree(const std::string&path,unsigned depth){if(depth>32)return false;DIR*d=opendir(path.c_str());if(!d)return false;bool ok=true;while(auto*entry=readdir(d)){std::string name=entry->d_name;if(name=="."||name=="..")continue;std::string child=path+"/"+name;struct stat st;if(stat(child.c_str(),&st)){ok=false;break;}if(S_ISDIR(st.st_mode)){if(!remove_tree(child,depth+1)||rmdir(child.c_str())){ok=false;break;}}else if(unlink(child.c_str())){ok=false;break;}vTaskDelay(1);}closedir(d);return ok;}
esp_err_t purge_logical(){if(phase!=1)return ESP_ERR_INVALID_STATE; // Journal survives both user partitions.
 esp_err_t e=nvs_flash_erase_partition("state");if(e==ESP_OK)e=nvs_flash_erase_partition("nvs");if(e!=ESP_OK)return e;
 if(!remove_tree("/books",0))return ESP_FAIL;
 e=nvs_set_u8(journal,"phase",2);if(e==ESP_OK)e=nvs_commit(journal);if(e==ESP_OK)phase=2;return e;}
esp_err_t purge_overwrite_step(sdmmc_card_t&card){if(phase!=2||purge_check_card(card)!=ESP_OK)return ESP_ERR_INVALID_STATE;if(card.csd.sector_size!=512)return ESP_ERR_NOT_SUPPORTED;
 auto*zero=(uint8_t*)heap_caps_calloc(1,4096,MALLOC_CAP_DMA|MALLOC_CAP_INTERNAL);if(!zero)return ESP_ERR_NO_MEM;
 // Checkpoint only completed writes. A power cut repeats at most 4 MiB.
 uint32_t end=std::min(uint64_t(total),uint64_t(cursor)+8192),next=cursor;esp_err_t e=ESP_OK;
 while(next<end){uint32_t count=std::min(uint32_t(8),end-next);e=sdmmc_write_sectors(&card,zero,next,count);if(e!=ESP_OK)break;next+=count;vTaskDelay(1);}free(zero);if(e!=ESP_OK)return e;
 e=nvs_set_u32(journal,"cursor",next);if(e==ESP_OK&&next==total)e=nvs_set_u8(journal,"phase",3);if(e==ESP_OK)e=nvs_commit(journal);if(e==ESP_OK){cursor=next;if(next==total)phase=3;}return e;}
esp_err_t purge_finish(){if(phase!=3)return ESP_ERR_INVALID_STATE;auto e=nvs_erase_all(journal);if(e==ESP_OK)e=nvs_commit(journal);if(e==ESP_OK)phase=0;return e;}
