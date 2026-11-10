"""Render original README art and motion; Lucide icons retain their license."""
from pathlib import Path
import math
import os
import re
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'assets' / 'brand'
BG = '#0C171B'
MINT = '#C4F46E'
INK = '#EAF0E7'
MUTED = '#8BA29D'

def font(size, bold=False, mono=False):
    base=Path(os.environ.get('WINDIR','C:/Windows'))/'Fonts'
    paths=[base/('consola.ttf' if mono else 'segoeuib.ttf' if bold else 'segoeui.ttf'),
           Path('/usr/share/fonts/truetype/dejavu')/('DejaVuSansMono.ttf' if mono else 'DejaVuSans-Bold.ttf' if bold else 'DejaVuSans.ttf')]
    for p in paths:
        if p.exists(): return ImageFont.truetype(str(p),size)
    return ImageFont.load_default(size=size)

def hero(t):
    im=Image.new('RGB',(1200,580),BG);d=ImageDraw.Draw(im)
    for x in range(650,1200,32):
        for y in range(30,580,32):d.ellipse((x,y,x+1,y+1),fill='#25403C')
    d.line((44,76,1156,76),fill='#30463D')
    d.text((44,29),'P H A N T O M  /  R E S U M E',font=font(17,True),fill=INK)
    d.rounded_rectangle((962,25,1156,55),radius=15,fill='#223B2F')
    d.ellipse((976,36,984,44),fill=MINT)
    d.text((995,30),'1.3 / DEVELOPMENT',font=font(13,mono=True),fill=MINT)
    d.text((42,112),'See beneath',font=font(69,True),fill=INK)
    d.text((42,189),'the resume.',font=font(69,True),fill=MINT)
    d.text((46,296),'Explore the text. Trace the metadata.',font=font(23),fill='#B9CAC1')
    d.text((46,332),'Make your local experiments visible.',font=font(23),fill='#B9CAC1')
    # Orbit and stacked document planes. All motion is illustrative.
    cx,cy=933,297
    for rad in [150,195]:d.ellipse((cx-rad,cy-rad,cx+rad,cy+rad),outline='#2D443B',width=1)
    a=2*math.pi*t
    x,y=cx+195*math.cos(a),cy+195*math.sin(a)
    d.ellipse((x-5,y-5,x+5,y+5),fill=MINT)
    for idx,(dx,dy) in enumerate([(44,-29),(22,-14),(0,0)]):
        bob=math.sin(2*math.pi*t+idx*.45)*5
        x0,y0=820+dx,169+dy+bob
        d.rounded_rectangle((x0,y0,x0+216,y0+269),radius=14,fill=['#1B302A','#254033','#12251F'][idx],outline=['#3A5547','#57704E',MINT][idx],width=1)
        if idx==2:
            d.text((x0+20,y0+17),'DOCUMENT / 001',font=font(13,mono=True),fill=MINT)
            d.line((x0+20,y0+48,x0+196,y0+48),fill='#3E5143')
            d.rounded_rectangle((x0+20,y0+67,x0+62,y0+109),radius=8,fill=MINT)
            d.text((x0+32,y0+70),'P',font=font(24,True),fill=BG)
            for k,w in enumerate([96,70]):d.rounded_rectangle((x0+77,y0+76+k*18,x0+77+w,y0+81+k*18),radius=2,fill='#8C9F87')
            for k,w in enumerate([175,155,168,115,175]):d.rounded_rectangle((x0+20,y0+137+k*17,x0+20+w,y0+141+k*17),radius=2,fill='#3E5545')
            scan=y0+61+(1-math.cos(2*math.pi*t))*84
            d.rectangle((x0+1,scan,x0+215,scan+12),fill='#254936')
            d.line((x0+1,scan,x0+215,scan),fill=MINT,width=2)
            d.text((x0+20,y0+247),'TEXT + METADATA',font=font(13,mono=True),fill=MINT)
    d.rounded_rectangle((733,375,887,413),radius=8,fill=MINT)
    d.text((748,384),'LOCAL INSPECTION',font=font(13,True),fill=BG)
    d.line((44,481,1156,481),fill='#30463D')
    d.text((46,505),'WINDOWS   /   ANDROID   /   PYTHON CLI',font=font(16,mono=True),fill=INK)
    d.text((46,537),'OPEN SOURCE. EXPERIMENTAL BY DESIGN.',font=font(12,mono=True),fill=MUTED)
    d.text((900,514),'INSPECT â†’ VERIFY',font=font(16,mono=True),fill=MINT)
    return im

def icon(name,x,y,color,size=28):
    s=(OUT/'icons'/f'{name}.svg').read_text()
    body=s[s.index('>')+1:s.rfind('</svg>')]
    return f'<g transform="translate({x} {y}) scale({size/24})" fill="none" stroke="{color}" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">{body}</g>'

def svg(name,w,h,content):
    (OUT/name).write_text(f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img"><g font-family="Segoe UI,Arial,sans-serif">{content}</g></svg>',encoding='utf-8')

def cards():
    for name,title,detail,ic,accent in [
        ('windows','Windows','DOWNLOAD EXE Â· v1.3','monitor',MINT),
        ('android','Android','DOWNLOAD APK Â· v1.3','smartphone','#C4D7FF'),
        ('source','Source code','EXPLORE THE BUILD','terminal','#F4DAB0')]:
        svg(name+'.svg',380,132,f'<rect x="1" y="1" width="378" height="130" rx="15" fill="{BG}" stroke="#3B5045"/>'+icon(ic,23,27,accent,29)+icon('arrow-up-right',331,26,accent,21)+f'<text x="69" y="48" font-size="26" font-weight="600" fill="{INK}">{title}</text><text x="24" y="100" font-size="14" letter-spacing="1" fill="{accent}">{detail}</text>')
    parts=['<rect width="1200" height="226" rx="18" fill="#F1F0E7"/>']
    for i,(ic,n,title,desc) in enumerate([
        ('scan-text','01','Read the document','Text, structure, and local scores.'),
        ('layers','02','Explore the layers','Document and media experiments.'),
        ('shield-check','03','Check the result','Extraction, diffs, and reports.')]):
        x=30+i*400
        if i:parts.append(f'<path d="M{x-15}30V196" stroke="#CCCEC2"/>')
        parts.extend([icon(ic,x+4,31,'#385C41',30),f'<text x="{x+304}" y="53" fill="#7B8576" font-size="16">{n}</text>',f'<text x="{x+4}" y="118" fill="#14271E" font-size="27" font-weight="600">{title}</text>',f'<text x="{x+4}" y="162" fill="#53624F" font-size="17">{desc}</text>'])
    svg('capabilities.svg',1200,226,''.join(parts))
    svg('footer.svg',1200,150,f'<rect width="1200" height="150" rx="18" fill="{MINT}"/><text x="36" y="66" fill="{BG}" font-size="32" font-weight="600">Build experiments. Keep the evidence.</text><text x="38" y="108" fill="#426036" font-size="18">PhantomResume / Open source / Made by ansh2807</text>'+icon('ghost',1080,44,BG,60))

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    frames=[hero(i/48) for i in range(48)]
    frames[0].save(OUT/'cover.png',optimize=True)
    frames[0].save(OUT/'cover.gif',save_all=True,append_images=frames[1:],duration=90,loop=0,optimize=True)
    cards()
    print('Rendered cover, motion, three download cards, capability panel and footer.')

if __name__=='__main__':main()
