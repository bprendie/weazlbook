#pragma once
#include <string>
void security_init();
bool device_locked();
bool unlock_configured();
void set_device_locked(bool locked);
void set_code(bool duress,const std::string& code);
int security_arrow(char arrow); // 0 unmatched, 1 unlocked, 2 duress
