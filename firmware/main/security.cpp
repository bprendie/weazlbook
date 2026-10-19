#include "security.hpp"
#include "nvs.h"
#include <stdexcept>
static nvs_handle_t h;
static std::string unlock_code,duress_code,attempt;
static bool locked=true;
static void check(esp_err_t e){if(e!=ESP_OK)throw std::runtime_error("Device security storage failed");}
static std::string read_code(const char*key){char b[17]={};size_t n=sizeof(b);auto e=nvs_get_str(h,key,b,&n);if(e==ESP_ERR_NVS_NOT_FOUND)return {};check(e);std::string s=b;if(s.size()<4||s.size()>16||s.find_first_not_of("UDLR")!=std::string::npos)throw std::runtime_error("Invalid stored code");return s;}
void security_init(){check(nvs_open("security",NVS_READWRITE,&h));unlock_code=read_code("unlock");duress_code=read_code("duress");uint8_t flag=0;auto e=nvs_get_u8(h,"locked",&flag);if(e!=ESP_OK&&e!=ESP_ERR_NVS_NOT_FOUND)check(e);locked=flag!=0;}
bool device_locked(){return locked;}
bool unlock_configured(){return !unlock_code.empty();}
void set_device_locked(bool value){if(value&&unlock_code.empty())throw std::runtime_error("Set unlock code in Settings");check(nvs_set_u8(h,"locked",value));check(nvs_commit(h));locked=value;attempt.clear();}
void set_code(bool duress,const std::string&code){if(locked)throw std::runtime_error("Locked");if(code.size()<4||code.size()>16||code.find_first_not_of("UDLR")!=std::string::npos)throw std::runtime_error("Use 4-16 arrows");auto other=duress?unlock_code:duress_code;if(duress&&other.empty())throw std::runtime_error("Set unlock code first");if(!other.empty()&&(other==code||other.size()!=code.size()))throw std::runtime_error("Different code; same length");check(nvs_set_str(h,duress?"duress":"unlock",code.c_str()));check(nvs_commit(h));(duress?duress_code:unlock_code)=code;}
int security_arrow(char arrow){if(!locked)return 0;attempt+=arrow;if(attempt.size()>16)attempt.erase(0,attempt.size()-16);for(int which:{2,1}){auto&code=which==2?duress_code:unlock_code;if(!code.empty()&&attempt.size()>=code.size()&&attempt.compare(attempt.size()-code.size(),code.size(),code)==0){attempt.clear();if(which==1)set_device_locked(false);return which;}}return 0;}
