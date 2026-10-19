#include "core.hpp"
#include <stdexcept>
namespace wb {
std::vector<Page> layout(const std::string&t,size_t cols,size_t rows){
 if(cols<8||rows<2||cols>80||rows>80||t.size()>65536)throw std::runtime_error("Layout bounds exceeded");
 std::vector<Page> pages;Page p{0,{}};size_t i=0;
 while(i<t.size()){
   if(p.lines.empty())p.offset=i;
   size_t start=i,last_space=std::string::npos,n=0;
   while(i<t.size()&&n<cols&&t[i]!='\n'){
     if(t[i]==' ')last_space=i;
     unsigned char c=t[i];size_t bytes=c<0x80?1:(c&0xe0)==0xc0?2:(c&0xf0)==0xe0?3:4;
     i=std::min(t.size(),i+bytes);n++;
   }
   if(i<t.size()&&t[i]!='\n'&&last_space!=std::string::npos&&last_space>start)i=last_space;
   p.lines.push_back(t.substr(start,i-start));if(i<t.size()&&(t[i]==' '||t[i]=='\n'))i++;
   if(p.lines.size()==rows){pages.push_back(std::move(p));p={i,{}};}
 }
 if(!p.lines.empty())pages.push_back(std::move(p));return pages;
}
}
