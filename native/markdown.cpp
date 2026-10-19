#include "markdown.hpp"
#include <algorithm>
#include <cctype>
#include <cstdio>
#include <memory>
#include <sstream>
#include <stdexcept>
namespace wb {
bool markdown_extension(const std::string& path){auto p=path.rfind('.');if(p==std::string::npos)return false;auto ext=path.substr(p);for(auto&c:ext)c=std::tolower((unsigned char)c);auto base=path.substr(path.find_last_of("/\\")==std::string::npos?0:path.find_last_of("/\\")+1);for(auto&c:base)c=std::tolower((unsigned char)c);return ext==".md"||ext==".markdown"||base=="file_id.diz";}
std::string markdown_text(const std::string& input){
 if(input.size()>65536||input.find('\0')!=std::string::npos)throw std::runtime_error("Markdown limit 64 KiB; no NUL bytes");
 // Reject malformed UTF-8 rather than corrupting pagination anchors.
 for(size_t i=0;i<input.size();){unsigned char c=input[i++];if(c<128)continue;int n=c>=0xc2&&c<=0xdf?1:c>=0xe0&&c<=0xef?2:c>=0xf0&&c<=0xf4?3:-1;unsigned cp=c&((1<<(6-std::max(n,0)))-1);int count=n;if(n<0)throw std::runtime_error("Markdown must be UTF-8");while(n--){if(i>=input.size()||(input[i]&0xc0)!=0x80)throw std::runtime_error("Markdown must be UTF-8");cp=(cp<<6)|(input[i++]&63);}if((count==2&&cp<0x800)||(count==3&&cp<0x10000)||cp>0x10ffff||(cp>=0xd800&&cp<=0xdfff))throw std::runtime_error("Markdown must be UTF-8");}
 std::istringstream stream(input.substr(input.compare(0,3,"\xef\xbb\xbf")==0?3:0));std::string line,out,fence;bool paragraph=false,any=false;
 auto blank=[&](){if(!out.empty()&&out.back()!='\n')out+='\n';if(!out.empty()&&(out.size()<2||out[out.size()-2]!='\n'))out+='\n';paragraph=false;};
 while(std::getline(stream,line)){
  if(!line.empty()&&line.back()=='\r')line.pop_back();auto first=line.find_first_not_of(" \t");std::string t=first==std::string::npos?"":line.substr(first);
  if(!fence.empty()){if(t.size()>=fence.size()&&t.find_first_not_of(fence[0])>=fence.size()&&(t.find_first_not_of(fence[0])==std::string::npos||t.substr(t.find_first_not_of(fence[0])).find_first_not_of(" \t")==std::string::npos)){fence.clear();blank();}else{out+="    "+line+'\n';any|=!t.empty();}continue;}
  if(t.compare(0,3,"```")==0||t.compare(0,3,"~~~")==0){blank();fence=t.substr(0,t.find_first_not_of(t[0]));continue;}
  if(t.empty()){blank();continue;}any=true;
  size_t hashes=t.find_first_not_of('#');
  if(hashes>=1&&hashes<=6&&hashes<t.size()&&t[hashes]==' '){blank();auto heading=t.substr(hashes+1);out+=heading+'\n'+std::string(std::min(size_t(28),heading.size()),'=')+'\n';paragraph=false;continue;}
  bool list=t.size()>1&&(t[0]=='-'||t[0]=='*'||t[0]=='+')&&t[1]==' ';
  auto digit=t.find_first_not_of("0123456789");bool ordered=digit>0&&digit<t.size()&&digit+1<t.size()&&(t[digit]=='.'||t[digit]==')')&&t[digit+1]==' ';
  bool structural=list||ordered||t[0]=='>'||first>=4||(!line.empty()&&line[0]=='\t')||t.find_first_not_of("-*_=")==std::string::npos;
  if(structural){if(paragraph)out+='\n';out+=line+'\n';paragraph=false;}
  else{if(paragraph)out+=' ';out+=t;paragraph=true;}
 }
 if(!any)throw std::runtime_error("Markdown has no readable text");
 if(out.size()>65536)throw std::runtime_error("Normalized Markdown exceeds 64 KiB");return out;
}
std::string markdown_file(const std::string& path){std::unique_ptr<FILE,decltype(&fclose)> f(fopen(path.c_str(),"rb"),fclose);if(!f)throw std::runtime_error("Markdown unavailable");std::string data(65537,'\0');size_t n=fread(data.data(),1,data.size(),f.get());if(ferror(f.get()))throw std::runtime_error("Markdown read failed");data.resize(n);return markdown_text(data);}
Markdown::Markdown(const std::string& path):path_(path){
 std::unique_ptr<FILE,decltype(&fclose)> f(fopen(path.c_str(),"rb"),fclose);if(!f)throw std::runtime_error("Markdown unavailable");
 fseek(f.get(),0,SEEK_END);long length=ftell(f.get());if(length<1||length>2*1024*1024)throw std::runtime_error("Markdown size limit 2 MiB");rewind(f.get());
 boundaries_.push_back(0);char buffer[8194];std::string fence;
 while(fgets(buffer,sizeof(buffer),f.get())){
  std::string line=buffer;if(line.size()>8192)throw std::runtime_error("Markdown line exceeds 8 KiB");auto first=line.find_first_not_of(" \t");auto t=first==std::string::npos?std::string():line.substr(first);
  if(fence.empty()){if(t.compare(0,3,"```")==0||t.compare(0,3,"~~~")==0)fence=t.substr(0,t.find_first_not_of(t[0]));}
  else if(t.compare(0,fence.size(),fence)==0&&t.find_first_not_of(std::string(1,fence[0])+" \r\n\t")==std::string::npos)fence.clear();
  long end=ftell(f.get());if(end-boundaries_.back()>48000)throw std::runtime_error("Markdown section exceeds 48 KiB; add paragraph breaks");
  if(fence.empty()&&end-boundaries_.back()>=16000&&line.find_first_not_of(" \r\n\t")==std::string::npos&&end<length)boundaries_.push_back(end);
 }
 if(ferror(f.get()))throw std::runtime_error("Markdown read failed");boundaries_.push_back(length);
}
std::string Markdown::chapter(size_t index)const{
 if(index>=chapters())throw std::runtime_error("End of document");
 std::unique_ptr<FILE,decltype(&fclose)> f(fopen(path_.c_str(),"rb"),fclose);if(!f||fseek(f.get(),boundaries_[index],SEEK_SET))throw std::runtime_error("Markdown unavailable");
 size_t n=boundaries_[index+1]-boundaries_[index];std::string text(n,'\0');if(fread(text.data(),1,n,f.get())!=n)throw std::runtime_error("Markdown read failed");return markdown_text(text);
}

}
