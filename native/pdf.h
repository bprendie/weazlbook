#pragma once
#include <stddef.h>
#include <stdbool.h>
#ifdef __cplusplus
extern "C" {
#endif
typedef bool (*wb_text_cb)(void *ctx, size_t source_page, const char *utf8, size_t length);
// Extract one selected page, zero based, or SIZE_MAX for all pages.
int wb_pdf(const char *path, size_t selected, wb_text_cb callback, void *ctx, char *error, size_t error_size);
#ifdef __cplusplus
}
#endif
