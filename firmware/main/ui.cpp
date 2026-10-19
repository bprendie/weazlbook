#include "ui.hpp"
#include "security.hpp"
#include "purge.hpp"
#include "hardware.hpp"
#include "display.hpp"
#include "core.hpp"
#include "epub.hpp"
#include "markdown.hpp"
#include <cctype>
#include "pdf.h"
#include "font_atlas.hpp"
#include "esp_log.h"
#include "esp_timer.h"
#include "esp_heap_caps.h"
#include "nvs.h"
#include "cJSON.h"
#include "mbedtls/sha256.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include <algorithm>
#include <cstdio>
#include <dirent.h>
#include <memory>
#include <stdexcept>
#include <cstring>
#include <unistd.h>
namespace {
using Json=std::unique_ptr<cJSON,decltype(&cJSON_Delete)>;
Json state{nullptr,cJSON_Delete};nvs_handle_t handle;uint32_t sequence=0;
std::string identity(const std::string&path);
std::vector<std::string> library,library_ids;std::vector<wb::Page> pages;std::unique_ptr<wb::Epub> epub;std::unique_ptr<wb::Markdown> markdown;
std::string file,id,title,source,notice;size_t chapter=0,page_index=0,selected=0;int size=24;
bool reading=false,marks=false,settings=false;int code_mode=0;bool code_confirm=false;std::string draft_code,first_code;size_t total_sources=1;uint8_t*frame;
uint32_t hash32(const char*p){uint32_t h=2166136261;for(;*p;p++)h=(h^uint8_t(*p))*16777619;return h;}
cJSON *record(){auto*b=cJSON_GetObjectItem(state.get(),"books");auto*r=cJSON_GetObjectItem(b,id.c_str());if(!r){r=cJSON_CreateObject();cJSON_AddStringToObject(r,"title",title.c_str());cJSON_AddItemToObject(r,"bookmarks",cJSON_CreateArray());cJSON_AddItemToObject(b,id.c_str(),r);}return r;}
void number(cJSON*r,const char*k,double n){cJSON_DeleteItemFromObject(r,k);cJSON_AddNumberToObject(r,k,n);}
void save(){
 char*payload=cJSON_PrintUnformatted(state.get());if(!payload)throw std::runtime_error("State memory exhausted");
 if(strlen(payload)>60000){free(payload);throw std::runtime_error("Native state limit 60 KiB");}
 Json root(cJSON_CreateObject(),cJSON_Delete);cJSON_AddNumberToObject(root.get(),"sequence",sequence+1);cJSON_AddNumberToObject(root.get(),"checksum_fnv1a",hash32(payload));cJSON_AddStringToObject(root.get(),"payload",payload);free(payload);
 char*data=cJSON_PrintUnformatted(root.get());if(!data)throw std::runtime_error("State allocation failed");
 esp_err_t e=nvs_set_str(handle,(sequence+1)%2?"slot1":"slot0",data);free(data);if(e==ESP_OK)e=nvs_commit(handle);if(e!=ESP_OK)throw std::runtime_error("State commit failed");sequence++;
}
void resume(){if(pages.empty())return;auto*r=record();number(r,"source_index",chapter);number(r,"offset_utf8",pages[page_index].offset);number(r,"progress",std::min(99,int(100.0*(chapter+double(page_index)/std::max(size_t(1),pages.size()))/std::max(size_t(1),total_sources))));cJSON_DeleteItemFromObject(r,"source");cJSON_AddStringToObject(r,"source",source.c_str());save();}
void restore(){
 ESP_ERROR_CHECK(nvs_open_from_partition("state","reader",NVS_READWRITE,&handle));
 for(const char*key:{"slot0","slot1"}){
  size_t n=0;if(nvs_get_str(handle,key,nullptr,&n)!=ESP_OK||n>125000)continue;std::vector<char> data(n);if(nvs_get_str(handle,key,data.data(),&n)!=ESP_OK)continue;
  Json r(cJSON_Parse(data.data()),cJSON_Delete);if(!r)continue;
  auto*s=cJSON_GetObjectItem(r.get(),"sequence"),*crc=cJSON_GetObjectItem(r.get(),"checksum_fnv1a"),*p=cJSON_GetObjectItem(r.get(),"payload");
  if(!cJSON_IsNumber(s)||!cJSON_IsNumber(crc)||!cJSON_IsString(p)||s->valuedouble<sequence||hash32(p->valuestring)!=uint32_t(crc->valuedouble))continue;
  Json candidate(cJSON_Parse(p->valuestring),cJSON_Delete);if(!candidate||!cJSON_IsObject(cJSON_GetObjectItem(candidate.get(),"books")))continue;
  state=std::move(candidate);sequence=s->valuedouble;
 }
 if(!state){state.reset(cJSON_CreateObject());cJSON_AddNumberToObject(state.get(),"version",1);cJSON_AddStringToObject(state.get(),"coordinates","native-r05-source-utf8");cJSON_AddItemToObject(state.get(),"books",cJSON_CreateObject());}
}
void scan(){library.clear();DIR*d=opendir("/books");if(!d)throw std::runtime_error("Card filesystem unavailable");while(auto*e=readdir(d)){std::string n=e->d_name;std::string lower=n;for(auto&c:lower)c=std::tolower((unsigned char)c);if(lower=="file_id.diz")continue;if((lower.size()>=5&&lower.substr(lower.size()-5)==".epub")||(lower.size()>=4&&lower.substr(lower.size()-4)==".pdf")||wb::markdown_extension(lower)){if(library.size()==512){closedir(d);throw std::runtime_error("Library limit 512 books");}library.push_back(n);}}closedir(d);std::sort(library.begin(),library.end());selected=0;library_ids.clear();for(auto&n:library)library_ids.push_back(identity("/books/"+n));}
std::string identity(const std::string&path){FILE*f=fopen(path.c_str(),"rb");if(!f)throw std::runtime_error("Book missing");mbedtls_sha256_context ctx;mbedtls_sha256_init(&ctx);mbedtls_sha256_starts(&ctx,0);uint8_t b[4096],digest[32];size_t n;while((n=fread(b,1,sizeof(b),f)))mbedtls_sha256_update(&ctx,b,n);bool bad=ferror(f);fclose(f);mbedtls_sha256_finish(&ctx,digest);mbedtls_sha256_free(&ctx);if(bad)throw std::runtime_error("Book read error");char out[65];for(int i=0;i<32;i++)snprintf(out+i*2,3,"%02x",digest[i]);return out;}
bool collect(void*ctx,size_t,const char*t,size_t n){*static_cast<std::string*>(ctx)=std::string(t,n);return true;}
void load_chapter(size_t offset=0){
 std::string text;if(markdown){text=markdown->chapter(chapter);source="markdown:"+std::to_string(chapter+1);}else if(epub){text=epub->chapter(chapter);source=epub->spine[chapter].path;}else{char error[256];int count=wb_pdf(file.c_str(),chapter,collect,&text,error,sizeof(error));if(count<0)throw std::runtime_error(error);total_sources=count;source="page:"+std::to_string(chapter+1);}
 if(epub)total_sources=epub->spine.size();if(markdown)total_sources=markdown->chapters();
 auto next=wb::layout(text,432/(size==20?font_20_w:size==24?font_24_w:font_28_w),680/(size+8));if(next.empty())throw std::runtime_error("Empty source page");pages=std::move(next);page_index=0;
 for(size_t i=0;i<pages.size();i++)if(pages[i].offset<=offset)page_index=i;
}
void open_book(bool about=false){file="/books/"+(about?std::string("file_id.diz"):library[selected]);title=about?"file_id.diz":library[selected];id=identity(file);epub.reset();markdown.reset();std::string lower=file;for(auto&c:lower)c=std::tolower((unsigned char)c);if(lower.size()>=5&&lower.substr(lower.size()-5)==".epub"){epub=std::make_unique<wb::Epub>(file);title=epub->title;}
 if(wb::markdown_extension(file))markdown=std::make_unique<wb::Markdown>(file);
 auto*r=record();auto*c=cJSON_GetObjectItem(r,"source_index"),*o=cJSON_GetObjectItem(r,"offset_utf8");chapter=cJSON_IsNumber(c)?std::max(0,c->valueint):0;load_chapter(cJSON_IsNumber(o)?std::max(0,o->valueint):0);reading=true;}
uint32_t decode(const char*&p){unsigned char c=*p++;if(c<128)return c;int n=(c&0xe0)==0xc0?1:(c&0xf0)==0xe0?2:(c&0xf8)==0xf0?3:0;uint32_t cp=c&((1<<(6-n))-1);if(!n)return 0x25a1;while(n--){unsigned char d=*p;if((d&0xc0)!=0x80)return 0x25a1;p++;cp=(cp<<6)|(d&63);}return cp;}
void line(int x,int y,const std::string&s){const uint32_t*atlas=size==20?font_20:size==24?font_24:font_28;int w=size==20?font_20_w:size==24?font_24_w:font_28_w,h=size+8;const char*p=s.c_str();while(*p&&x+w<=480){auto cp=decode(p);int g=glyph_count-1;for(int i=0;i<glyph_count;i++)if(glyph_codes[i]==cp){g=i;break;}for(int dy=0;dy<h&&y+dy<800;dy++)for(int dx=0;dx<w;dx++)if(atlas[g*h+dy]&(1U<<(w-dx-1))){int bit=(y+dy)*480+x+dx;if(bit>=0)frame[bit/8]&=~(0x80>>(bit%8));}x+=w;}}
void draw(){memset(frame,0xff,48000);
 if(device_locked()){line(24,200,"We4zLbo0k");line(24,300,"LOCKED");line(24,350,"Enter your arrow sequence");display_update(frame);return;}
 if(code_mode){line(24,40,code_mode==1?"UNLOCK CODE":"NUKE CODE");line(24,100,code_confirm?"Repeat the same code":"Enter 4-16 arrows");line(24,160,draft_code);line(24,260,"SELECT confirms / BACK exits");line(24,320,"Nuke: immediate wipe");if(!notice.empty())line(24,400,notice.substr(0,28));display_update(frame);return;}
 if(settings){line(24,40,"SETTINGS");line(24,110,(selected==0?"> ":"  ")+std::string("Unlock code"));line(24,160,(selected==1?"> ":"  ")+std::string("Nuke Code"));display_update(frame);return;}
line(24,12,title.empty()?"LOCAL LIBRARY":title.substr(0,28));if(!notice.empty()){line(24,80,notice.substr(0,28));if(notice.size()>28)line(24,120,notice.substr(28,28));}else if(reading&&!marks){for(size_t i=0;i<pages[page_index].lines.size();i++)line(24,60+i*(size+8),pages[page_index].lines[i]);line(24,752,std::to_string(chapter+1)+":"+std::to_string(page_index+1)+" MARK saves");}else if(marks){auto*a=cJSON_GetObjectItem(record(),"bookmarks");for(int i=0;i<cJSON_GetArraySize(a)&&i<18;i++){auto*m=cJSON_GetArrayItem(a,i);const char*n=cJSON_GetStringValue(cJSON_GetObjectItem(m,"name"));line(24,60+i*32,(size_t(i)==selected?"> ":"  ")+std::string(n?n:"Unnamed"));}}else{
 line(24,12,"MAIN MENU");auto*books=cJSON_GetObjectItem(state.get(),"books");
 for(size_t i=selected>8?selected-8:0,j=0;i<library.size()+2&&j<9;i++,j++){
  std::string label=i==library.size()?"Settings":i==library.size()+1?"file_id.diz":library[i];
  line(24,65+j*70,(i==selected?"> ":"  ")+label.substr(0,25));
  if(i<library.size()){auto*r=cJSON_GetObjectItem(books,library_ids[i].c_str());auto*p=cJSON_GetObjectItem(r,"progress");bool done=cJSON_IsTrue(cJSON_GetObjectItem(r,"read"));line(50,95+j*70,done?"100% READ":"~"+std::to_string(cJSON_IsNumber(p)?p->valueint:0)+"% complete");}
 }
 line(24,752,"SELECT opens / BACK returns");}esp_err_t e=display_update(frame);if(e!=ESP_OK)ESP_LOGW("ui","Frame rendered; panel update %s",esp_err_to_name(e));}
void export_state(){char*p=cJSON_Print(state.get());if(!p)throw std::runtime_error("Export memory");FILE*f=fopen("/books/weazlbook-state-native-v1.json","wb");if(!f){free(p);throw std::runtime_error("Export open failed");}size_t n=strlen(p);bool ok=fwrite(p,1,n,f)==n;free(p);if(fflush(f))ok=false;if(fsync(fileno(f)))ok=false;if(fclose(f))ok=false;if(!ok)throw std::runtime_error("Export failed; transfer cancelled");}
void import_state(){
 std::unique_ptr<FILE,decltype(&fclose)> f(fopen("/books/weazlbook-state-native-import.json","rb"),fclose);
 if(!f)throw std::runtime_error("No native import file");fseek(f.get(),0,SEEK_END);long n=ftell(f.get());if(n<1||n>60000)throw std::runtime_error("Import size limit");rewind(f.get());std::string data(n,'\0');if(fread(data.data(),1,n,f.get())!=size_t(n))throw std::runtime_error("Import read failed");
 Json incoming(cJSON_ParseWithLength(data.data(),data.size()),cJSON_Delete);if(!incoming)throw std::runtime_error("Malformed import JSON");
 auto*v=cJSON_GetObjectItem(incoming.get(),"version"),*coord=cJSON_GetObjectItem(incoming.get(),"coordinates"),*books=cJSON_GetObjectItem(incoming.get(),"books");
 if(!cJSON_IsNumber(v)||v->valueint!=1||!cJSON_IsString(coord)||strcmp(coord->valuestring,"native-r05-source-utf8")||!cJSON_IsObject(books))throw std::runtime_error("Unsupported native state format");
 for(auto*r=books->child;r;r=r->next){
  if(!r->string||strlen(r->string)!=64||strspn(r->string,"0123456789abcdef")!=64||!cJSON_IsObject(r))throw std::runtime_error("Invalid book identity");
  auto*marks=cJSON_GetObjectItem(r,"bookmarks");if(!cJSON_IsArray(marks)||cJSON_GetArraySize(marks)>64)throw std::runtime_error("Invalid bookmark array");
  std::vector<cJSON*> anchors{r};for(auto*m=marks->child;m;m=m->next){auto*name=cJSON_GetObjectItem(m,"name");if(!cJSON_IsString(name)||strlen(name->valuestring)>120)throw std::runtime_error("Invalid bookmark name");anchors.push_back(m);}
  for(auto*a:anchors){auto*s=cJSON_GetObjectItem(a,"source_index"),*o=cJSON_GetObjectItem(a,"offset_utf8");if(!s&&!o&&a==r)continue;if(!cJSON_IsNumber(s)||!cJSON_IsNumber(o)||s->valuedouble<0||s->valuedouble>2000||o->valuedouble<0||o->valuedouble>65536)throw std::runtime_error("Invalid native anchor");}
 }
 Json merged(cJSON_Duplicate(state.get(),true),cJSON_Delete);auto*dest=cJSON_GetObjectItem(merged.get(),"books");
 for(auto*r=books->child;r;r=r->next){auto*existing=cJSON_GetObjectItem(dest,r->string);if(!existing)cJSON_AddItemToObject(dest,r->string,cJSON_Duplicate(r,true));else{auto*a=cJSON_GetObjectItem(existing,"bookmarks");auto*source=cJSON_GetObjectItem(r,"bookmarks");for(auto*m=source->child;m;m=m->next){bool found=false;for(auto*old=a->child;old;old=old->next)if(cJSON_Compare(m,old,true))found=true;if(!found){if(cJSON_GetArraySize(a)>=64)throw std::runtime_error("Merged bookmark limit");cJSON_AddItemToArray(a,cJSON_Duplicate(m,true));}}}}
 auto previous=std::move(state);state=std::move(merged);try{save();}catch(...){state=std::move(previous);throw;}
}
}
void reader_run(){
 frame=(uint8_t*)heap_caps_malloc(48000,MALLOC_CAP_SPIRAM|MALLOC_CAP_8BIT);if(!frame){ESP_LOGE("ui","No framebuffer");return;}
 try{restore();scan();draw();}catch(const std::exception&e){ESP_LOGE("reader","%s",e.what());return;}
 bool transfer_armed=false;wb::Debounce cable;int64_t last_activity=esp_timer_get_time();
 for(;;){
  if(!controls_released())last_activity=esp_timer_get_time();
  int key=input_event();bool connected=cable.update(vbus_present(),esp_timer_get_time()/1000);
  if(key>=0||connected)last_activity=esp_timer_get_time();
  if(!code_mode&&!host_owns_storage()&&esp_timer_get_time()-last_activity>2000000){idle_light_sleep();last_activity=esp_timer_get_time();}
  try{
   if(host_owns_storage()){if(!cable.held()&&!vbus_present()){auto e=usb_transfer_end();if(e!=ESP_OK){notice="Card unavailable. Use FAT32; restart.";draw();return;}scan();notice.clear();draw();}vTaskDelay(pdMS_TO_TICKS(20));continue;}
   if(connected&&!device_locked()&&!code_mode){
    if(reading)resume();else save();export_state();
    pages.clear();epub.reset();markdown.reset();reading=false;marks=false;title.clear();transfer_armed=false;
    if(usb_transfer_begin()!=ESP_OK)throw std::runtime_error("USB transfer failed; reconnect cable");
    notice="USB disk ready. Eject then unplug.";draw();continue;
   }
   if(key==7){if(device_locked()){continue;}if(!unlock_configured()){settings=true;reading=false;marks=false;selected=0;notice="Set unlock code first";}else set_device_locked(true);draw();continue;}
   if(device_locked()){
    if(key>=0&&key<=3){int match=security_arrow("UDLR"[key]);if(match==2){pages.clear();epub.reset();markdown.reset();auto e=storage_purge_begin();if(e!=ESP_OK)throw std::runtime_error("Wipe could not start");}if(match==1){notice="Unlocked. Reconnect USB to transfer.";draw();}}
    vTaskDelay(pdMS_TO_TICKS(10));continue;
   }
   if(code_mode){
    if(key>=0&&key<=3&&draft_code.size()<16)draft_code+="UDLR"[key];
    if(key==5){code_mode=0;draft_code.clear();first_code.clear();}
    if(key==4){if(draft_code.size()<4)notice="Use at least four arrows";else if(!code_confirm){first_code=draft_code;draft_code.clear();code_confirm=true;}else if(draft_code!=first_code){draft_code.clear();notice="Codes differ; repeat again";}else{set_code(code_mode==2,draft_code);code_mode=0;draft_code.clear();first_code.clear();notice="Code saved";}}
    if(key>=0)draw();vTaskDelay(pdMS_TO_TICKS(10));continue;
   }
   if(key<0){vTaskDelay(pdMS_TO_TICKS(10));continue;}
   if(!notice.empty()){notice.clear();if(!transfer_armed){draw();continue;}}
   if(settings){if(key==0)selected=0;if(key==1)selected=1;if(key==5){settings=false;selected=0;}if(key==4){code_mode=selected?2:1;code_confirm=false;draft_code.clear();first_code.clear();}draw();continue;}
   if(key==8&&reading){marks=true;selected=0;draw();continue;}
   if(!reading){
    if(key==2){import_state();notice="Imported native bookmarks.";}
    if(key==0&&selected)selected--;if(key==1&&selected+1<library.size()+2)selected++;
    if(key==6){transfer_armed=true;notice="SELECT: transfer. BACK cancels.";}
    if(key==4){if(transfer_armed){if(!vbus_present())throw std::runtime_error("Attach USB cable first");save();export_state();pages.clear();epub.reset();markdown.reset();if(usb_transfer_begin()!=ESP_OK)throw std::runtime_error("USB transfer failed");transfer_armed=false;notice="USB transfer. Eject then unplug.";}else if(selected==library.size()){settings=true;selected=0;}else if(selected==library.size()+1)open_book(true);else if(!library.empty())open_book();}
    if(key==5)transfer_armed=false;
   }else if(marks){
    auto*a=cJSON_GetObjectItem(record(),"bookmarks");if(key==0&&selected)selected--;if(key==1&&selected+1<size_t(cJSON_GetArraySize(a)))selected++;
    if(key==4&&cJSON_GetArraySize(a)){auto*m=cJSON_GetArrayItem(a,selected);chapter=cJSON_GetObjectItem(m,"source_index")->valueint;load_chapter(cJSON_GetObjectItem(m,"offset_utf8")->valueint);marks=false;resume();}if(key==5)marks=false;
   }else{
    if(key==3){if(page_index+1<pages.size())page_index++;else if(chapter+1>=total_sources){auto*r=record();cJSON_DeleteItemFromObject(r,"read");cJSON_AddBoolToObject(r,"read",true);notice="Book complete. Marked READ.";}else{chapter++;try{load_chapter();}catch(...){chapter--;throw;}}resume();}
    if(key==2){if(page_index)page_index--;else if(chapter){chapter--;load_chapter(SIZE_MAX);}resume();}
    if(key==0){size_t off=pages[page_index].offset;size=size==28?20:size+4;load_chapter(off);}
    if(key==1){marks=true;selected=0;}
    if(key==6){auto*a=cJSON_GetObjectItem(record(),"bookmarks");if(cJSON_GetArraySize(a)>=64)throw std::runtime_error("64 bookmarks per book limit");auto*m=cJSON_CreateObject();auto name="Mark "+std::to_string(cJSON_GetArraySize(a)+1);cJSON_AddStringToObject(m,"name",name.c_str());cJSON_AddStringToObject(m,"source",source.c_str());cJSON_AddNumberToObject(m,"source_index",chapter);cJSON_AddNumberToObject(m,"offset_utf8",pages[page_index].offset);cJSON_AddItemToArray(a,m);resume();}
    if(key==5){resume();reading=false;epub.reset();markdown.reset();pages.clear();title.clear();selected=0;}
   }
   draw();
  }catch(const std::exception&e){notice=e.what();ESP_LOGE("reader","%s",e.what());draw();}
 }
}
