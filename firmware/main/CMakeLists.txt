set(ROOT "${CMAKE_CURRENT_LIST_DIR}/../..")
file(GLOB PDF_SOURCES "${ROOT}/vendor/pdfio/pdfio-*.c")
set(ZLIB_SOURCES adler32.c crc32.c deflate.c infback.c inffast.c inflate.c inftrees.c trees.c zutil.c compress.c uncompr.c)
list(TRANSFORM ZLIB_SOURCES PREPEND "${ROOT}/vendor/zlib/")
idf_component_register(
 SRCS security.cpp purge.cpp main.cpp hardware.cpp display.cpp ui.cpp "${ROOT}/native/core.cpp" "${ROOT}/native/markdown.cpp" "${ROOT}/native/epub.cpp" "${ROOT}/vendor/pugixml/pugixml.cpp" "${ROOT}/native/pdf.c" "${ROOT}/native/budget.c" ${PDF_SOURCES} "${ROOT}/vendor/pdfio/ttf.c" ${ZLIB_SOURCES}
 INCLUDE_DIRS "." "${ROOT}/native" "${ROOT}/vendor/pdfio" "${ROOT}/vendor/zlib" "${ROOT}/vendor/pugixml"
 REQUIRES esp_driver_gpio esp_driver_spi esp_driver_sdspi fatfs sdmmc nvs_flash esp_psram esp_timer esp_adc mbedtls json esp_pm spi_flash)
target_compile_options(${COMPONENT_LIB} PRIVATE -Wno-error=misleading-indentation -Wno-error=format-truncation -Wno-error=unused-variable -Wno-error=char-subscripts)
