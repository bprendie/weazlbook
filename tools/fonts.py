"""Generate Plex Mono bitmap atlases: Latin-1, punctuation and missing-glyph box."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1]
codes=list(range(32,127))+list(range(160,256))+list(range(0x2010,0x2027))+[0x25a1]
out=['// IBM Plex Mono: SIL OFL, baseline/research/fonts/OFL.txt.','#pragma once','#include <cstdint>',f'constexpr int glyph_count={len(codes)};','static const uint32_t glyph_codes[]={'+','.join(map(str,codes))+'};']
for size in (20,24,28):
 f=ImageFont.truetype(str(ROOT/'baseline/research/fonts/IBMPlexMono-Regular.ttf'),size);w=round(f.getlength('M'));h=size+8;data=[]
 for code in codes:
  im=Image.new('1',(w,h));ImageDraw.Draw(im).text((0,0),chr(code),font=f,fill=1)
  for y in range(h):
   bits=0
   for x in range(w):bits=(bits<<1)|int(bool(im.getpixel((x,y))))
   data.append(bits)
 out.append(f'constexpr int font_{size}_w={w},font_{size}_h={h};')
 out.append(f'static const uint32_t font_{size}[]={{'+','.join(map(str,data))+'};')
(ROOT/'firmware/main/font_atlas.hpp').write_text('\n'.join(out))
