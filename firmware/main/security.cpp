#include "security.hpp"
#include "nvs.h"
#include "esp_random.h"
#include "bootloader_random.h"
#include "mbedtls/pkcs5.h"
#include "mbedtls/platform_util.h"
#include <cstring>
#include <stdexcept>
// Versioned independent salts; device-local, never exported to the SD card.
static constexpr uint32_t rounds=100000;
struct Verifier {uint32_t version=0,iterations=0,length=0;uint8_t salt[16]={},digest[32]={};};
static_assert(sizeof(Verifier)==60);
static nvs_handle_t h;
static Verifier unlock_code,duress_code;
static std::string attempt;
static bool locked=true;
static void check(esp_err_t e){if(e!=ESP_OK)throw std::runtime_error("Device security storage failed");}
static void clear_attempt(){if(!attempt.empty())mbedtls_platform_zeroize(attempt.data(),attempt.size());attempt.clear();}
static void derive(const Verifier&r,const char*code,size_t n,uint8_t*out){if(mbedtls_pkcs5_pbkdf2_hmac_ext(MBEDTLS_MD_SHA256,(const unsigned char*)code,n,r.salt,sizeof(r.salt),r.iterations,32,out))throw std::runtime_error("Code verification failed");}
static Verifier make_verifier(const char*code,size_t n){
 Verifier r;r.version=2;r.iterations=rounds;r.length=n;
 // No RF: temporarily enable the internal SAR ADC entropy source. No ADC
 // consumers are currently active; future battery ADC use must serialize here.
 bootloader_random_enable();esp_fill_random(r.salt,sizeof(r.salt));bootloader_random_disable();
 derive(r,code,n,r.digest);return r;
}
static bool matches(const Verifier&r,const char*code,size_t n){
 if(!r.version||n!=r.length)return false;uint8_t digest[32];derive(r,code,n,digest);
 volatile uint8_t difference=0;for(size_t i=0;i<32;i++)difference=difference|(digest[i]^r.digest[i]);
 mbedtls_platform_zeroize(digest,sizeof(digest));return difference==0;
}
static void erase_legacy(const char*key){auto e=nvs_erase_key(h,key);if(e!=ESP_ERR_NVS_NOT_FOUND)check(e);check(nvs_commit(h));}
static Verifier read_code(const char*key,const char*new_key){
 Verifier r;size_t n=sizeof(r);auto e=nvs_get_blob(h,new_key,&r,&n);
 if(e==ESP_OK){if(n!=sizeof(r)||r.version!=2||r.iterations!=rounds||r.length<4||r.length>16)throw std::runtime_error("Invalid code verifier");erase_legacy(key);return r;}
 if(e!=ESP_ERR_NVS_NOT_FOUND)check(e); // Never fall back to plaintext after corrupt v2 data.
 char legacy[17]={};n=sizeof(legacy);e=nvs_get_str(h,key,legacy,&n);
 if(e==ESP_ERR_NVS_NOT_FOUND)return {};check(e);
 size_t length=strlen(legacy);if(length<4||length>16||strspn(legacy,"UDLR")!=length){mbedtls_platform_zeroize(legacy,sizeof(legacy));throw std::runtime_error("Invalid legacy code");}
 try{r=make_verifier(legacy,length);}catch(...){mbedtls_platform_zeroize(legacy,sizeof(legacy));throw;}
 mbedtls_platform_zeroize(legacy,sizeof(legacy));
 // Commit verifier before removing the old key; interrupted migration resumes.
 check(nvs_set_blob(h,new_key,&r,sizeof(r)));check(nvs_commit(h));erase_legacy(key);return r;
}
void security_init(){
 check(nvs_open("security",NVS_READWRITE,&h));unlock_code=read_code("unlock","unlock_v2");duress_code=read_code("duress","duress_v2");
 uint8_t flag=0;auto e=nvs_get_u8(h,"locked",&flag);if(e!=ESP_OK&&e!=ESP_ERR_NVS_NOT_FOUND)check(e);
 if(flag>1||(flag&&!unlock_code.version)||(duress_code.version&&(!unlock_code.version||duress_code.length!=unlock_code.length)))throw std::runtime_error("Invalid security state");locked=flag!=0;
}
bool device_locked(){return locked;}
bool unlock_configured(){return unlock_code.version!=0;}
void set_device_locked(bool value){if(value&&!unlock_configured())throw std::runtime_error("Set unlock code in Settings");check(nvs_set_u8(h,"locked",value));check(nvs_commit(h));locked=value;clear_attempt();}
void set_code(bool duress,const std::string&code){
 if(locked)throw std::runtime_error("Locked");if(code.size()<4||code.size()>16||code.find_first_not_of("UDLR")!=std::string::npos)throw std::runtime_error("Use 4-16 arrows");
 const auto&other=duress?unlock_code:duress_code;if(duress&&!other.version)throw std::runtime_error("Set unlock code first");
 if(other.version&&(other.length!=code.size()||matches(other,code.data(),code.size())))throw std::runtime_error("Different code; same length");
 auto r=make_verifier(code.data(),code.size());check(nvs_set_blob(h,duress?"duress_v2":"unlock_v2",&r,sizeof(r)));check(nvs_commit(h));
 (duress?duress_code:unlock_code)=r;clear_attempt();erase_legacy(duress?"duress":"unlock");
}
int security_arrow(char arrow){
 if(!locked)return 0;if(!strchr("UDLR",arrow)||arrow==0)return 0;attempt+=arrow;if(attempt.size()>16)attempt.erase(0,attempt.size()-16);
 bool nuke=false,unlock=false;
 if(duress_code.version&&attempt.size()>=duress_code.length)nuke=matches(duress_code,attempt.data()+attempt.size()-duress_code.length,duress_code.length);
 if(unlock_code.version&&attempt.size()>=unlock_code.length)unlock=matches(unlock_code,attempt.data()+attempt.size()-unlock_code.length,unlock_code.length);
 if(nuke){clear_attempt();return 2;}if(unlock){set_device_locked(false);return 1;}return 0;
}
