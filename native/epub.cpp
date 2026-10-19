#include "epub.hpp"
#include "pugixml.hpp"
#include "budget.h"
#include <zlib.h>
#include <cstdio>
#include <cstring>
#include <map>
#include <memory>
#include <stdexcept>
#include <algorithm>
namespace wb {
namespace {
uint16_t u16(const unsigned char*p){return p[0]|unsigned(p[1])<<8;}
uint32_t u32(const unsigned char*p){return u16(p)|uint32_t(u16(p+2))<<16;}
struct Entry {uint32_t offset,packed,size,crc;uint16_t method;};
struct Zip {
 std::unique_ptr<FILE,decltype(&fclose)> f{nullptr,fclose};std::map<std::string,Entry> entries;
 explicit Zip(const std::string&path){
  f.reset(fopen(path.c_str(),"rb"));if(!f)throw std::runtime_error("Cannot open EPUB");
  fseek(f.get(),0,SEEK_END);long size=ftell(f.get());if(size<22||size>64*1024*1024)throw std::runtime_error("EPUB file size limit");
  size_t tail=std::min<long>(size,65557);std::vector<unsigned char>b(tail);fseek(f.get(),size-tail,SEEK_SET);if(fread(b.data(),1,tail,f.get())!=tail)throw std::runtime_error("Truncated EPUB");
  long e=-1;for(long i=tail-22;i>=0;i--)if(u32(b.data()+i)==0x06054b50 && i+22+u16(b.data()+i+20)==long(tail)){e=i;break;}
  if(e<0)throw std::runtime_error("Missing ZIP directory");auto*p=b.data()+e;
  uint16_t count=u16(p+10);uint32_t offset=u32(p+16);
  if(u16(p+4)||u16(p+6)||count>2048||count!=u16(p+8)||offset>uint32_t(size))throw std::runtime_error("ZIP64/multidisk/entry limit unsupported");
  fseek(f.get(),offset,SEEK_SET);uint64_t total=0;
  for(unsigned i=0;i<count;i++){
   unsigned char h[46];if(fread(h,1,46,f.get())!=46||u32(h)!=0x02014b50)throw std::runtime_error("Malformed ZIP directory");
   uint16_t nl=u16(h+28),extra=u16(h+30),comment=u16(h+32);
   if(nl>512||u16(h+8)&1)throw std::runtime_error("Encrypted ZIP or long path");
   std::string name(nl,'\0');if(fread(name.data(),1,nl,f.get())!=nl)throw std::runtime_error("Truncated ZIP name");
   if(entries.count(name))throw std::runtime_error("Duplicate ZIP member");
   Entry en{u32(h+42),u32(h+20),u32(h+24),u32(h+16),u16(h+10)};
   total+=en.size;if(total>32*1024*1024)throw std::runtime_error("EPUB expanded size limit");
   entries[name]=en;fseek(f.get(),extra+comment,SEEK_CUR);
  }
 }
 std::string read(const std::string&name){
  auto it=entries.find(name);if(it==entries.end())throw std::runtime_error("Missing EPUB member: "+name);auto e=it->second;
  if(e.size>512*1024||e.packed>1024*1024)throw std::runtime_error("Native EPUB member exceeds 512 KiB expanded/1 MiB compressed");
  unsigned char h[30];fseek(f.get(),e.offset,SEEK_SET);if(fread(h,1,30,f.get())!=30||u32(h)!=0x04034b50)throw std::runtime_error("Malformed ZIP local header");
  fseek(f.get(),u16(h+26)+u16(h+28),SEEK_CUR);std::string out(e.size,'\0');
  if(e.method==0){if(e.packed!=e.size||fread(out.data(),1,e.size,f.get())!=e.size)throw std::runtime_error("Truncated stored member");}
  else if(e.method==8){
   z_stream z{};if(inflateInit2(&z,-15)!=Z_OK)throw std::runtime_error("Inflater memory failure");
   unsigned char chunk[4096];uint32_t left=e.packed;int status=Z_OK;z.next_out=(Bytef*)out.data();z.avail_out=out.size();
   while(left&&status==Z_OK){size_t n=std::min<uint32_t>(left,sizeof(chunk));if(fread(chunk,1,n,f.get())!=n){inflateEnd(&z);throw std::runtime_error("Truncated deflate");}left-=n;z.next_in=chunk;z.avail_in=n;status=inflate(&z,Z_NO_FLUSH);}
   bool valid=status==Z_STREAM_END&&z.total_out==e.size&&z.total_in==e.packed;inflateEnd(&z);if(!valid)throw std::runtime_error("Invalid/oversized deflate stream");
  }else throw std::runtime_error("Unsupported ZIP compression");
  if(crc32(0,(const Bytef*)out.data(),out.size())!=e.crc)throw std::runtime_error("ZIP CRC mismatch");return out;
 }
};
std::string local(const char*s){std::string n=s;auto i=n.find(':');return i==std::string::npos?n:n.substr(i+1);}
std::string resolve(const std::string&base,const std::string&href){
 if(href.find(':')!=std::string::npos||href.find('\\')!=std::string::npos||(!href.empty()&&href[0]=='/'))throw std::runtime_error("External/absolute EPUB path");
 std::string path=base.substr(0,base.rfind('/')==std::string::npos?0:base.rfind('/')+1)+href.substr(0,href.find('#'));
 std::vector<std::string> segs;size_t i=0;while(i<=path.size()){auto j=path.find('/',i);if(j==std::string::npos)j=path.size();auto v=path.substr(i,j-i);if(v==".."){if(segs.empty())throw std::runtime_error("EPUB path escapes archive");segs.pop_back();}else if(v!="."&&!v.empty())segs.push_back(v);i=j+1;}
 std::string result;for(auto&v:segs){if(!result.empty())result+='/';result+=v;}return result;
}
void parse(pugi::xml_document&doc,const std::string&text){
 if(text.find("<!DOCTYPE")!=std::string::npos||text.find("<!ENTITY")!=std::string::npos)throw std::runtime_error("Native EPUB DTD/entity declarations unsupported");
 if(!doc.load_buffer(text.data(),text.size(),pugi::parse_default,pugi::encoding_utf8))throw std::runtime_error("Malformed EPUB XML");
 size_t count=0;std::vector<std::pair<pugi::xml_node,int>> stack{{doc,0}};
 while(!stack.empty()){auto [n,d]=stack.back();stack.pop_back();if(++count>20000||d>48)throw std::runtime_error("EPUB XML node/depth limit");for(auto c:n.children())stack.emplace_back(c,d+1);}
}
pugi::xml_node find(pugi::xml_node n,const char*tag){if(local(n.name())==tag)return n;for(auto c:n.children()){auto r=find(c,tag);if(r)return r;}return {};}
void text(pugi::xml_node n,std::string&out){
 auto tag=local(n.name());if(tag=="script"||tag=="style"||tag=="head")return;
 if(tag=="img"||tag=="svg"||tag=="math"){out+=" [Illustration omitted: ";out+=n.attribute("alt").as_string(tag.c_str());out+="] ";return;}
 bool block=tag=="p"||tag=="div"||tag=="li"||tag=="section"||tag=="tr"||(tag.size()==2&&tag[0]=='h');
 if(block&&!out.empty()&&out.back()!='\n')out+='\n';
 if(tag=="em"||tag=="i")out+='*';if(tag=="strong"||tag=="b")out+="**";
 if(n.type()==pugi::node_pcdata||n.type()==pugi::node_cdata){for(const char*c=n.value();*c;c++){if(*c=='\n'||*c=='\r'||*c=='\t'||*c==' '){if(!out.empty()&&out.back()!=' '&&out.back()!='\n')out+=' ';}else out+=*c;}}
 for(auto c:n.children())text(c,out);
 if(tag=="em"||tag=="i")out+='*';if(tag=="strong"||tag=="b")out+="**";
 if(block||tag=="br")out+='\n';if(out.size()>65536)throw std::runtime_error("Native chapter text exceeds 64 KiB");
}
}
Epub::Epub(const std::string&path):file(path){
 pugi::set_memory_management_functions(wb_malloc,wb_free);
 Zip z(path);
 if(z.entries.count("META-INF/encryption.xml")){
  pugi::xml_document encryption;parse(encryption,z.read("META-INF/encryption.xml"));
  std::vector<pugi::xml_node> nodes{encryption};while(!nodes.empty()){auto n=nodes.back();nodes.pop_back();if(local(n.name())=="EncryptionMethod"){
   std::string a=n.attribute("Algorithm").as_string();if(a!="http://www.idpf.org/2008/embedding"&&a!="http://ns.adobe.com/pdf/enc#RC")throw std::runtime_error("Protected EPUB content unsupported");}for(auto c:n.children())nodes.push_back(c);}
 }
 pugi::xml_document container;parse(container,z.read("META-INF/container.xml"));auto root=find(container,"rootfile");if(!root)throw std::runtime_error("No EPUB package");
 auto package=resolve("",root.attribute("full-path").as_string());pugi::xml_document opf;parse(opf,z.read(package));title=find(opf,"title").text().as_string("Untitled");
 auto manifest=find(opf,"manifest");std::map<std::string,Chapter> items;
 for(auto item:manifest.children())if(local(item.name())=="item"){
  if(std::string(item.attribute("media-type").as_string())=="application/xhtml+xml")items[item.attribute("id").as_string()]={resolve(package,item.attribute("href").as_string()),item.attribute("id").as_string()};
 }
 for(auto n:find(opf,"spine").children())if(local(n.name())=="itemref"){
  auto it=items.find(n.attribute("idref").as_string());if(it==items.end())throw std::runtime_error("Unsupported/non-XHTML spine member");spine.push_back(it->second);
 }
 if(spine.empty()||spine.size()>1024)throw std::runtime_error("Native EPUB spine limit or empty book");
}
std::string Epub::chapter(size_t index)const{
 if(index>=spine.size())throw std::runtime_error("Spine index out of range");Zip z(file);pugi::xml_document doc;parse(doc,z.read(spine[index].path));std::string out;text(doc,out);if(out.empty())throw std::runtime_error("Chapter has no text");return out;
}
}
