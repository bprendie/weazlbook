#include "pdf.h"
#include "core.hpp"
#include "budget.h"
#include "epub.hpp"
#include "markdown.hpp"
#include <cstdio>
#include <chrono>
static bool emit(void*,size_t page,const char*t,size_t n){auto pages=wb::layout(std::string(t,n),30,21);printf("SOURCE_PAGE %zu READER_PAGES %zu\n",page,pages.size());for(auto&p:pages)for(auto&line:p.lines)puts(line.c_str());return true;}
int main(int argc,char**argv){if(argc!=2){fprintf(stderr,"Usage: wb-native book.pdf|book.epub\n");return 2;}char error[256];auto start=std::chrono::steady_clock::now();int r=0;try{std::string path=argv[1];if(path.size()>5&&path.substr(path.size()-5)==".epub"){wb::Epub book(path);for(size_t i=0;i<book.spine.size();i++){auto text=book.chapter(i);emit(nullptr,i+1,text.data(),text.size());}r=book.spine.size();}else if(wb::markdown_extension(path)){wb::Markdown book(path);for(size_t i=0;i<book.chapters();i++){auto text=book.chapter(i);emit(nullptr,i+1,text.data(),text.size());}r=book.chapters();}else r=wb_pdf(argv[1],SIZE_MAX,emit,nullptr,error,sizeof(error));}catch(const std::exception&e){snprintf(error,sizeof(error),"%s",e.what());r=-1;}fprintf(stderr,"pages=%d pdfio_peak_bytes=%zu live_bytes=%zu elapsed_ms=%lld\n",r,wb_memory_peak(),wb_memory_used(),(long long)std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::steady_clock::now()-start).count());if(r<0){fprintf(stderr,"%s\n",error);return 1;}return 0;}
