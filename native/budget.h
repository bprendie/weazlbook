#pragma once
#include <stddef.h>
#ifdef __cplusplus
extern "C" {
#endif
void *wb_malloc(size_t n);
void *wb_calloc(size_t count, size_t size);
void *wb_realloc(void *p, size_t n);
char *wb_strdup(const char *s);
void wb_free(void *p);
size_t wb_memory_peak(void);
size_t wb_memory_used(void);
#ifdef __cplusplus
}
#endif
