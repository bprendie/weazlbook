/* Native conservative PDF spike: PDFio parses objects/xrefs/streams; this file
 * validates a narrow single-column text subset before emitting any page text. */
#include "pdf.h"
#include "pdfio.h"
#include "budget.h"
#include <math.h>
#include <string.h>
#include <ctype.h>
#include <sys/stat.h>
#include <stdint.h>

typedef struct { char *error;size_t size;bool failed; } errors;
static bool pdf_error(pdfio_file_t *pdf,const char *message,void *ctx){(void)pdf;errors*e=ctx;e->failed=true;snprintf(e->error,e->size,"PDF parser: %s",message);return false;}
static int fail(errors*e,const char*m){snprintf(e->error,e->size,"%s",m);return -1;}
static pdfio_dict_t *dict(pdfio_dict_t*d,const char*k){pdfio_dict_t*r=pdfioDictGetDict(d,k);if(!r){pdfio_obj_t*o=pdfioDictGetObj(d,k);if(o)r=pdfioObjGetDict(o);}return r;}
static int font_ok(pdfio_obj_t *page,const char *name){
    pdfio_dict_t*d=pdfioObjGetDict(page),*res=NULL;
    for(int i=0;i<32 && d;i++) { res=dict(d,"Resources"); if(res)break; d=dict(d,"Parent"); }
    pdfio_dict_t *fonts=res?dict(res,"Font"):NULL,*font=fonts?dict(fonts,name):NULL;
    if(!font)return 0;
    const char *sub=pdfioDictGetName(font,"Subtype"),*enc=pdfioDictGetName(font,"Encoding"),*base=pdfioDictGetName(font,"BaseFont");
    if(!sub || strcmp(sub,"Type1") || !base || pdfioDictGetObj(font,"ToUnicode"))return 0;
    if(enc && strcmp(enc,"WinAnsiEncoding"))return 0;
    if(pdfioDictGetDict(font,"Encoding") || pdfioDictGetObj(font,"Encoding"))return 0;
    return !strncmp(base,"Helvetica",9)||!strncmp(base,"Times-",6)||!strncmp(base,"Courier",7);
}
static size_t utf8(unsigned c,char*out){if(c<128){out[0]=(char)c;return 1;}if(c<2048){out[0]=0xc0|(c>>6);out[1]=0x80|(c&63);return 2;}out[0]=0xe0|(c>>12);out[1]=0x80|((c>>6)&63);out[2]=0x80|(c&63);return 3;}
static unsigned winansi(unsigned c){static const unsigned w[32]={0x20ac,0,0x201a,0x192,0x201e,0x2026,0x2020,0x2021,0x2c6,0x2030,0x160,0x2039,0x152,0,0x17d,0,0,0x2018,0x2019,0x201c,0x201d,0x2022,0x2013,0x2014,0x2dc,0x2122,0x161,0x203a,0x153,0,0x17e,0x178};return c>=128&&c<160?w[c-128]:c;}

int wb_pdf(const char*path,size_t selected,wb_text_cb cb,void*ctx,char*error,size_t error_size){
    errors e={error,error_size,false}; if(error_size)error[0]=0;
    struct stat st;if(stat(path,&st)||st.st_size>8*1024*1024)return fail(&e,"Native PDF file limit is 8 MiB, or file unavailable");
    pdfio_file_t*f=pdfioFileOpen(path,NULL,NULL,pdf_error,&e);if(!f)return -1;
    int result=-1; char*out=NULL; pdfio_encryption_t encryption;
    pdfioFileGetPermissions(f,&encryption);
    if(encryption!=PDFIO_ENCRYPTION_NONE){fail(&e,"Encrypted PDF unsupported");goto done;}
    size_t pages=pdfioFileGetNumPages(f);
    if(!pages||pages>2000||pdfioFileGetNumObjs(f)>4096){fail(&e,"PDF page/object limit exceeded");goto done;}
    if(selected!=SIZE_MAX&&selected>=pages){fail(&e,"Source page out of range");goto done;}
    out=wb_malloc(65536);if(!out){fail(&e,"PDF memory budget exhausted");goto done;}
    for(size_t p=0;p<pages;p++){
        if(selected!=SIZE_MAX&&selected!=p)continue;
        pdfio_obj_t*page=pdfioFileGetPage(f,p);size_t len=0,steps=0;bool in_text=false,valid_font=false,in_array=false;
        double nums[6]={0},last_y=1e20;int nn=0; char name[256]="";
        for(size_t j=0;j<pdfioPageGetNumStreams(page);j++){
            pdfio_stream_t*s=pdfioPageOpenStream(page,j,true);if(!s){fail(&e,"Unsupported content filter or invalid stream");goto done;}
            char token[2048];bool bad=false;
            while(pdfioStreamGetToken(s,token,sizeof(token))){
                if(++steps>200000||len>64000){fail(&e,"Native PDF page work/text limit exceeded");bad=true;break;}
                if(!strcmp(token,"BT")){in_text=true;nn=0;continue;}
                if(!strcmp(token,"ET")){in_text=false;if(len&&out[len-1]!='\n')out[len++]='\n';continue;}
                if(!strcmp(token,"Do")){fail(&e,"XObject content needs desktop inspection (native subset)");bad=true;break;}
                if(token[0]=='/' ){snprintf(name,sizeof(name),"%.255s",token+1);continue;}
                if(!strcmp(token,"cm")){
                    if(nn!=6||fabs(nums[0]-1)>0.001||fabs(nums[1])>.001||fabs(nums[2])>.001||fabs(nums[3]-1)>.001||fabs(nums[4])>.001||fabs(nums[5])>.001){fail(&e,"Transformed PDF content unsupported");bad=true;break;}
                    nn=0;continue;
                }
                char *end; double number=strtod(token,&end);
                if(*token && !*end){
                    if(in_array&&in_text&&number < -100 && len)out[len++]=' ';
                    if(nn<6)nums[nn++]=number;else{memmove(nums,nums+1,5*sizeof(double));nums[5]=number;}
                    continue;
                }
                if(!in_text){nn=0;continue;}
                if(!strcmp(token,"Tf")){valid_font=font_ok(page,name);if(!valid_font){fail(&e,"Native PDF requires standard Type1 WinAnsi fonts; ToUnicode/CID/differences pending");bad=true;break;}}
                else if(!strcmp(token,"Tm")){
                    if(nn!=6||fabs(nums[1])>.001||fabs(nums[2])>.001||nums[0]<=0||nums[3]<=0||nums[5]>last_y+.1){fail(&e,"Rotated or non-monotonic PDF reading order unsupported");bad=true;break;}
                    last_y=nums[5];if(len&&out[len-1]!='\n')out[len++]='\n';
                }else if(!strcmp(token,"Td")||!strcmp(token,"TD")){
                    if(nn!=2||nums[1]>0.1){fail(&e,"Non-monotonic PDF text movement unsupported");bad=true;break;}
                    if(nums[1]<-.1&&len&&out[len-1]!='\n')out[len++]='\n';
                }else if(!strcmp(token,"T*")){if(len&&out[len-1]!='\n')out[len++]='\n';}
                else if(!strcmp(token,"["))in_array=true;
                else if(!strcmp(token,"]"))in_array=false;
                else if(token[0]=='('){
                    if(!valid_font){fail(&e,"Missing usable font mapping");bad=true;break;}
                    for(const unsigned char*c=(unsigned char*)token+1;*c;c++){
                        unsigned cp=winansi(*c);if(!cp){fail(&e,"Undefined character mapping");bad=true;break;}
                        len+=utf8(cp,out+len);
                        if(len>64000){fail(&e,"Page text limit exceeded");bad=true;break;}
                    }
                    if(bad)break;
                }else if(token[0]=='<'||!strcmp(token,"'")||!strcmp(token,"\"")){fail(&e,"Native PDF hex/quote text operators unsupported");bad=true;break;}
                nn=0;
            }
            pdfioStreamClose(s);if(bad||e.failed)goto done;
        }
        if(!len){fail(&e,"Source page has no usable text (no OCR); import stopped, not silently omitted");goto done;}
        if(!cb(ctx,p+1,out,len)){fail(&e,"Output cancelled");goto done;}
    }
    result=(int)pages;
done:
    wb_free(out);pdfioFileClose(f);return result;
}
