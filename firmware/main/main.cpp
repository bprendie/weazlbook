#include "hardware.hpp"
#include "security.hpp"
#include "purge.hpp"
#if CONFIG_BT_ENABLED
#error "WeazlBook firmware forbids radio support"
#endif
#include "ui.hpp"
#include "display.hpp"
#include "pdf.h"
#include "core.hpp"
#include "budget.h"
#include "esp_log.h"
#include "esp_psram.h"
#include "esp_heap_caps.h"
#include "esp_flash.h"
#include "esp_system.h"
#include "nvs_flash.h"
#include "nvs.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include <cstdio>
#include <dirent.h>
#include <string>
#include <vector>
static bool page(void*,size_t source,const char*t,size_t n){auto pages=wb::layout(std::string(t,n),30,21);ESP_LOGI("pdf","source=%u reader_pages=%u bytes=%u",unsigned(source),unsigned(pages.size()),unsigned(n));return true;}
static void purge_worker(void*){
 while(purge_pending()){auto e=storage_purge_step();if(e!=ESP_OK){ESP_LOGE("wipe","Wipe paused: %s",esp_err_to_name(e));vTaskDelay(pdMS_TO_TICKS(5000));}}
 esp_restart();
}
extern "C" void app_main(){
 ESP_ERROR_CHECK(nvs_flash_init());ESP_ERROR_CHECK(nvs_flash_init_partition("state"));
 uint32_t flash=0;ESP_ERROR_CHECK(esp_flash_get_size(nullptr,&flash));
 ESP_LOGI("boot","flash=%lu PSRAM=%u internal_free=%u",(unsigned long)flash,unsigned(esp_psram_get_size()),unsigned(heap_caps_get_free_size(MALLOC_CAP_INTERNAL)));
 if(flash!=16*1024*1024||esp_psram_get_size()!=8*1024*1024){ESP_LOGE("boot","Memory configuration mismatch");return;}
 purge_init();
 if(!purge_pending()){try{security_init();}catch(...){ESP_LOGE("security","Fail closed: security state unavailable");return;}}
 inputs_init();esp_err_t e=storage_init();if(e!=ESP_OK){ESP_LOGE("storage","SD initialization failed: %s",esp_err_to_name(e));return;}
 e=display_init();ESP_LOGW("display","Panel bring-up status: %s",esp_err_to_name(e));
 // Native spike is opt-in by filename. Reader UI integration is tracked separately.
 if(purge_pending()){
  if(xTaskCreate(purge_worker,"card_wipe",8192,nullptr,1,nullptr)!=pdPASS){ESP_LOGE("wipe","Worker allocation failed; restart to resume");return;}
  // No new card writes or USB export until the entire overwrite is finished.
  for(;;){ESP_LOGI("wipe","Stage %d, overwrite %d%%",purge_phase(),purge_percent());vTaskDelay(pdMS_TO_TICKS(30000));}
 }
 char error[256];int pages=wb_pdf("/books/native-test.pdf",SIZE_MAX,page,nullptr,error,sizeof(error));
 ESP_LOGI("pdf","pages=%d peak=%u result=%s",pages,unsigned(wb_memory_peak()),pages<0?error:"OK");
 reader_run();
}
