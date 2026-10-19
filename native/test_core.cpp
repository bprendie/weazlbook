#include "core.hpp"
#include "markdown.hpp"
#include <stdexcept>
#include <cassert>
int main(){
 auto md=wb::markdown_text("# Heading\n\nParagraph\ncontinued.\n\n- Item\n\n```\n  code\n```\n");
 assert(md.find("Heading\n=======")!=std::string::npos);
 assert(md.find("Paragraph continued.")!=std::string::npos);
 assert(md.find("- Item")!=std::string::npos&&md.find("      code")!=std::string::npos);
 assert(wb::markdown_extension("NOTES.MARKDOWN"));
 for(auto text:{std::string(65537,'x'),std::string("\xff"),std::string("a\0b",3)}){bool rejected=false;try{wb::markdown_text(text);}catch(const std::runtime_error&){rejected=true;}assert(rejected);}
 wb::Storage s;int phase=0;
 assert(s.transfer([&]{return ++phase==1;},[&]{return ++phase==2;},[&]{return ++phase==3;}));
 assert(!s.readable()&&!s.sleepable());assert(!s.transfer([]{return true;},[]{return true;},[]{return true;}));
 assert(s.reclaim([]{return true;},[]{return true;},[]{return true;}));assert(s.readable());
 assert(!s.transfer([]{return false;},[]{assert(false);return true;},[]{return true;}));assert(s.owner==wb::Owner::Fault);
 wb::Debounce d;assert(!d.update(true,10));assert(!d.update(false,20));assert(!d.update(true,30));assert(d.update(true,60));assert(!d.update(true,1000));assert(!d.update(false,1001));assert(!d.update(false,1032));assert(!d.held());
 auto p=wb::layout("hello world\nnext line",10,2);assert(p.size()==2);assert(p[0].offset==0);assert(p[1].offset>0);
}
