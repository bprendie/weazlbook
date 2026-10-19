#include "budget.h"
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <stdalign.h>
// Single parser owner only. Limit counts requested bytes, including PDFio state.
typedef union { size_t n; max_align_t alignment; } header;
static size_t used, peak;
void *wb_malloc(size_t n) {
    if (n > 2*1024*1024-used || n > SIZE_MAX-sizeof(header)) return NULL;
    header *h=malloc(n+sizeof(header)); if(!h) return NULL;
    h->n=n; used+=n; if(used>peak) peak=used; return h+1;
}
void wb_free(void *p) { if(p) {header *h=(header*)p-1; used-=h->n; free(h);} }
void *wb_calloc(size_t n,size_t s) {if(s && n>SIZE_MAX/s)return NULL; void*p=wb_malloc(n*s);if(p)memset(p,0,n*s);return p;}
void *wb_realloc(void *p,size_t n) {
    if(!p)return wb_malloc(n); if(!n){wb_free(p);return NULL;}
    header*h=(header*)p-1; size_t old=h->n;
    if(n>2*1024*1024-(used-old))return NULL;
    h=realloc(h,n+sizeof(header));if(!h)return NULL;h->n=n;used=used-old+n;if(used>peak)peak=used;return h+1;
}
char *wb_strdup(const char*s){size_t n=strlen(s)+1;char*p=wb_malloc(n);if(p)memcpy(p,s,n);return p;}
size_t wb_memory_peak(void){return peak;}
size_t wb_memory_used(void){return used;}
