# Portable reading state

## Desktop format v1

UTF-8 JSON: `{"version":1,"books":{"<sha256>":{"resume":{...},"bookmarks":[]}}}`.
Book identity is SHA-256 over the exact original file bytes. Move/rename preserves
identity; modified content intentionally creates a distinct identity and does not
delete the original record.

An anchor has `source` (EPUB archive path or `page:N`), `block` (normalized block
index), `id` (XHTML ID if present), `offset` (Unicode code point offset in that
block), and `context` (surrounding text for future anchor migration). Each bookmark
has a `name` and `anchor`. Source page labels appear in PDF contents entries.
The renderer derives page numbers; they are never authoritative state.

Two files, `state-0.json` and `state-1.json`, contain `sequence`, `payload`, and
SHA-256 of canonical payload JSON (sorted keys, UTF-8, no whitespace). Save writes
only the inactive slot, fsyncs its data and then its parent directory. Recovery
checks both slots and chooses the highest valid sequence. A torn newest slot falls
back to the prior slot. Tests truncate newest records at several write boundaries.
This is host-filesystem evidence, not proof of FAT/card power-loss behavior.

Import validates the full incoming document before mutation. It merges books and
distinct bookmarks, preserving local resume for already known books. Missing
source files do not delete state. Pagination is disposable and presently computed
in memory; a persistent pagination cache is not yet implemented.

## Native prototype format v1

The firmware uses `coordinates: "native-r05-source-utf8"`, `version: 1`, and
`books` keyed by original-file SHA-256. Each record has title, source path/page,
`source_index` (zero-based spine/page), `offset_utf8` in normalized chapter/page
text, and a bookmark list with the same coordinates and a name.

This coordinate format is explicitly distinct from desktop v1. Cross-runtime
anchor conversion is pending; do not import one as the other. Both survive font
changes and source renames within their own runtime.

Authoritative native state lives in the internal `state` NVS partition, namespace
`reader`, independent of host SD ownership. Two string slots carry sequence,
FNV-1a accidental-corruption checksum and serialized payload. NVS commits occur
before transfer. A human-readable snapshot is exported to
`/books/weazlbook-state-native-v1.json` before exposing the card. That snapshot is
not authoritative, and host interruption cannot overwrite NVS bookmarks.
Native import from `weazlbook-state-native-import.json` is invoked with LEFT in the library; it validates and merges records, preserving existing resume. Arbitrary on-device bookmark naming remains unfinished. Flash power-cut
recovery and wear measurements are bench gates.

### Device lock, duress and simulator reset

See [device controls](DEVICE_CONTROLS.md) for the authoritative current behavior.
The browser-local lock prototype has been replaced by server-enforced simulator
state. Firmware security uses NVS; the two-stage wipe has a separate journal so
it can erase user settings and still resume after power loss. Original host book
files are never deleted by the simulator.
