# Supported document paths — R05

The Python desktop reference reader and C/C++ device parser are separate
implementations. Desktop success does not establish device compatibility.

| Feature | Desktop reference reader | Native C/C++ / firmware |
|---|---|---|
| Markdown `.md` / `.markdown` | UTF-8, headings/TOC, bold, underlined emphasis, lists, quotes, code indentation, literal offline link destinations and image labels | Bounded section loading; reflowed paragraphs, underlined ATX headings, list/quote/code structure; inline Markdown markers remain visible |
| Reflowable EPUB 2/3 | ZIP/container/OPF/spine/XHTML; chapter headings, emphasis and links | ZIP stored/deflate, CRC, container/OPF/spine, XHTML; headings and emphasis |
| Font obfuscation metadata | Allowed, embedded fonts ignored | Allowed, embedded fonts ignored |
| EPUB navigation | EPUB3 nav plus derived headings and internal text links | Spine navigation; NCX/nav/link following still pending |
| EPUB fonts | IBM Plex Mono 20/24/28 px | Generated Plex Mono 20/24/28 px atlas |
| Native PDF | Not applicable: Python pypdf is desktop only | PDFio 1.6.5 object/xref parser, unfiltered or Flate streams; standard Type1 Helvetica/Times/Courier with WinAnsi mapping; sequential, unrotated text |
| PDF Unicode/CID/ToUnicode, custom encodings | pypdf coverage; inspect reading order | Explicit rejection; implementation pending |
| PDF mixed/images | Useful text extracted, blank/image-only pages reported | XObject content rejected; blank page stops import with a reason |
| Scans / encrypted content | Rejected; no OCR / no DRM removal | Rejected; no OCR / no DRM removal |
| Tables/math/illustrations | Simplified text and notices, not page-faithful | Text/notice subset; complex layout unsupported |
| Reading order | EPUB spine; PDF content-stream order | EPUB spine; conservative monotonic PDF positioning check |
| Resume/bookmarks | Independent SHA-256 identity, semantic anchors, named marks, JSON import/export | SHA-256 identity; source index and UTF-8 text offset; numbered named marks, NVS slots, JSON import/export; edit naming pending |

Desktop PDF extraction runs in an isolated process limited to 512 MiB address
space, 20 CPU seconds and 25 wall seconds. Desktop books: 64 MiB source; EPUB
32 MiB total expanded, 2 MiB per member, 4096 entries, 64 XML levels, 50,000 nodes.
Desktop imports materialize normalized text, so this is a reference reader, not
the device's memory architecture. Books containing non-text XML body tails,
complex CSS/writing modes or footnote semantics need additional coverage.

Native EPUB reads one source chapter at a time: 64 MiB archive, 2048 entries,
32 MiB declared expansion, 512 KiB extracted member, 64 KiB normalized chapter,
20,000 XML nodes and 48 levels. DTD/entity declarations and ZIP64 are rejected.
Native percent-encoded archive links, fixed-layout detection and full navigation
metadata are still incomplete. Pugixml does not fetch network resources.

Native PDF: 8 MiB source, 4096 objects, 2000 pages, 64 KiB text/page,
200,000 content tokens/page. PDFio allocations have a 2 MiB budget; its maximum
token string was reduced from 128 KiB to 4 KiB. This does not measure total
firmware RAM: C++ strings, zlib, stacks, font flash and framebuffers are additional.
Library recursion and malformed-file work limits require further adversarial
coverage before untrusted device imports are considered hardened.

The firmware framebuffer is exactly 48,000 bytes in PSRAM. No whole-book image
conversion or online service participates in either reading path.


Markdown files are limited to 2 MiB. Desktop block styles use the supplied Plex
Mono SemiBold; emphasis is underlined rather than italicized. Raw HTML, tables,
nested inline markup and other unsupported constructs remain literal text;
no HTML, script, remote image, or URL is executed/fetched. Code wraps to fit the
screen. This is a documented subset rather than a complete CommonMark renderer.

Native Markdown indexes paragraph boundaries without loading the whole book.
Sections target 16 KiB and are limited to 48 KiB source / 64 KiB normalized text;
source lines are limited to 8 KiB. Fenced code is not split between sections.
Invalid UTF-8 and NUL bytes are rejected. Resume stores section index plus the
normalized UTF-8 offset. Inline bold/italic/link syntax remains readable source
notation in firmware; the desktop typography does not imply native rich styling.
The supplied Alice file passes both import paths: 315 desktop pages at 24 px,
15 heading links, and 10 native sections. These page counts differ because the
renderers and their spacing differ.
