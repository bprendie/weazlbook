from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps
R=Path(__file__).resolve().parents[1]
F=R.parent/'research/fonts'
BG=(17,21,22); FG=(222,229,220); MUTED=(151,168,161); ACID=(169,233,36); CYAN=(35,192,202)
im=Image.new('RGB',(2560,1840),BG); d=ImageDraw.Draw(im)
def f(size,b=False): return ImageFont.truetype(str(F/('IBMPlexMono-SemiBold.ttf' if b else 'IBMPlexMono-Regular.ttf')),size)
def txt(x,y,s,size=28,c=FG,b=False): d.text((x,y),s,font=f(size,b),fill=c)
def place(name,box):
    a=Image.open(R/'render'/name).convert('RGB'); arr=np.asarray(a).astype(int)
    mask=np.max(np.abs(arr-arr[0,0]),axis=2)>9
    yy,xx=np.where(mask)
    a=a.crop((max(0,int(xx.min())-20),max(0,int(yy.min())-20),min(a.width,int(xx.max())+21),min(a.height,int(yy.max())+21)))
    a=ImageOps.contain(a,(box[2]-box[0],box[3]-box[1]),method=Image.Resampling.LANCZOS)
    im.paste(a,(box[0]+(box[2]-box[0]-a.width)//2,box[1]+(box[3]-box[1]-a.height)//2))
txt(70,55,'WEAZLBOOK',76,ACID,True)
txt(1980,85,'R04 / FIT STUDY',32,CYAN)
txt(75,158,'80 × 156 mm   /   14 → 26 mm taper   /   acid-green portrait deck',31,MUTED)
d.line((70,221,2490,221),fill=(58,74,69),width=2)
for x,s in [(75,'01 / FACE'),(1210,'02 / WEDGE'),(1705,'03 / OPEN REAR')]: txt(x,245,s,29,CYAN)
place('assembled.png',(70,305,1140,1550))
place('left_profile.png',(1220,346,1590,1505))
place('rear_open.png',(1695,305,2490,1550))
txt(1224,302,'14 mm / TOP',24,FG)
txt(1206,1524,'26 mm / GRIP',24,FG)
for x in (1170,1650): d.line((x,285,x,1580),fill=(41,54,49),width=1)
txt(1710,1554,'Rear view reverses left and right.',20,MUTED)
d.rectangle((70,1620,2490,1755),fill=(25,33,31))
txt(96,1645,'RAW 3.97-INCH E-PAPER',29,ACID,True)
txt(96,1694,'480 × 800 / IBM Plex Mono',25,MUTED)
txt(900,1645,'NUB + BACK / MARK',29,ACID,True)
txt(900,1694,'Native USB-C at lower left',25,MUTED)
txt(1712,1645,'COMPONENT ENVELOPES',29,ACID,True)
txt(1712,1694,'Published XY; reserved depths',25,MUTED)
txt(75,1787,'Dimensioned approval blockout. Flex fold, connector fit and installed heights await part measurements.',23,MUTED)
im.save(R/'WeazlBook_R04_mockup.png')
print(str(R/'WeazlBook_R04_mockup.png'))
