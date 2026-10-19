#pragma once
#include <cstdint>
#include <functional>
#include <string>
#include <vector>
namespace wb {
enum class Owner { Reader, Transition, Host, Fault };
// Callbacks execute synchronously; only a successful full handoff changes owner.
class Storage {
public:
 Owner owner=Owner::Reader;
 bool transfer(const std::function<bool()>&save,const std::function<bool()>&close,const std::function<bool()>&unmount){
   if(owner!=Owner::Reader)return false;owner=Owner::Transition;
   if(!save()||!close()||!unmount()){owner=Owner::Fault;return false;}owner=Owner::Host;return true;
 }
 bool reclaim(const std::function<bool()>&disconnect,const std::function<bool()>&mount,const std::function<bool()>&scan){
   if(owner!=Owner::Host)return false;owner=Owner::Transition;
   if(!disconnect()||!mount()||!scan()){owner=Owner::Fault;return false;}owner=Owner::Reader;return true;
 }
 bool readable()const{return owner==Owner::Reader;}
 bool sleepable()const{return owner==Owner::Reader;}
};
class Debounce {
 bool sample_=false,stable_=false;uint32_t since_=0;
public:
 bool update(bool pressed,uint32_t now){if(pressed!=sample_){sample_=pressed;since_=now;}if(uint32_t(now-since_)>=30&&stable_!=sample_){stable_=sample_;return stable_;}return false;}
 bool held()const{return stable_;}
};
struct Page {size_t offset;std::vector<std::string> lines;};
std::vector<Page> layout(const std::string&text,size_t columns,size_t rows);
}
