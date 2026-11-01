"""Native vector/text rasterization at 1080p or 4K; matches rEFInd 0.14.2 layout."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps
import argparse,json,hashlib
p=argparse.ArgumentParser(description='Generate local rEFInd theme assets; never installs them.')
p.add_argument('--scale',type=int,choices=(1,2),default=1)
p.add_argument('--config',type=Path,required=True)
p.add_argument('--output',type=Path,required=True)
a=p.parse_args()
S=a.scale;HERE=Path(__file__).resolve().parent
cfg=json.loads(a.config.read_text(encoding='utf-8-sig'))
entries=cfg['entries'];tool_ids=cfg['tools'];labels=cfg['labels']
if not 1 <= len(entries) <= 4: p.error('Use 1 to 4 entries')
allowed_tools=['about','reboot','shutdown','exit','firmware','mok_tool']
if not tool_ids or len(set(tool_ids))!=len(tool_ids) or any(t not in allowed_tools for t in tool_ids): p.error('Invalid tools')
if any(e['glyph'] not in ('windows','terminal') for e in entries): p.error('Invalid glyph')
if len(set(e['title'] for e in entries)) != len(entries): p.error('Entry titles must be unique')
if not isinstance(cfg['timeout'],int) or not 0 <= cfg['timeout'] <= 300: p.error('Invalid timeout')
# Values enter an example rEFInd config; reject quote/control injection.
def safe(value):
 return isinstance(value,str) and not any(c in value for c in '\r\n"{}')
if not all(safe(e.get(k,'')) for e in entries for k in ('title','loader','volume','ostype')): p.error('Unsafe config value')
if any(not e['loader'].startswith('/') or not e['loader'].lower().endswith('.efi') for e in entries): p.error('Use absolute EFI loader paths')
refind_dir=cfg['refind_dir'].rstrip('/')
if not safe(refind_dir) or not refind_dir.startswith('/EFI/') or ' ' in refind_dir or '..' in refind_dir: p.error('Invalid refind_dir')
OUT=a.output.resolve()
if OUT.exists() and any(OUT.iterdir()): p.error('Output must be a new or empty directory')
(OUT/'theme/icons').mkdir(parents=True,exist_ok=True);(OUT/'theme/fonts').mkdir(exist_ok=True)
THEME=OUT/'theme'
W,H=1920*S,1080*S;INK=(218,228,235);MUTED=(137,153,168);DIM=(110,139,158);LIT=(180,232,248)
big=192*S;small=48*S;bt=216*S;st=64*S
centers=[int(W/2+(i-(len(entries)-1)/2)*(bt+8)) for i in range(len(entries))]
tools=[int(W/2+(i-(len(tool_ids)-1)/2)*(st+8)) for i in range(len(tool_ids))]
main_top=H//2-big//2;tool_top=H//2+bt//2+16+(st-small)//2
def font(n,bold=False,light=False):
 f=ImageFont.truetype(str(HERE/'fonts/Inter.ttf'),n*S)
 f.set_variation_by_axes([14,600 if bold else 300 if light else 400])
 return f
def text(d,x,y,t,n,c=INK,center=False,bold=False,light=False):
 f=font(n,bold,light)
 if center:x-=d.textlength(t,font=f)/2
 d.text((x,y),t,font=f,fill=c)
canvas=Image.new('RGB',(W,H))
ambient=Image.new('L',(W,H));ad=ImageDraw.Draw(ambient)
ad.ellipse(tuple(v*S for v in (650,330,1270,740)),fill=130)
ambient=ambient.filter(ImageFilter.GaussianBlur(160*S))
canvas=Image.composite(Image.new('RGB',(W,H),(8,14,21)),canvas,ambient)
d=ImageDraw.Draw(canvas)
text(d,96*S,76*S,cfg['brand'],18,(169,195,211),bold=True)
text(d,1750*S,78*S,labels['home'],13,(112,133,148))
text(d,W//2,288*S,labels['choose'],40,center=True,light=True)
for x,title,sub in zip(centers,[e['title'] for e in entries],[e['subtitle'] for e in entries]):
 text(d,x,373*S,title,21,center=True);text(d,x,404*S,sub,14,MUTED,True)
for x,t in zip(tools,[labels[t] for t in tool_ids]):
 text(d,x,tool_top+small+18*S,t,12,MUTED,True)
# Optional static information, supplied by the person using the theme.
info=cfg.get('info',[])
if info:
 text(d,W//2,820*S,labels['info'],12,(112,133,148),True)
 if len(info)>4: p.error('Use at most four information fields')
 for i,field in enumerate(info):
  x=int(W*(i+1)/(len(info)+1))
  text(d,x,855*S,field['label'],12,(112,133,148),True)
  text(d,x,875*S,field['value'],18,(158,176,190),True)
text(d,W//2,940*S,labels['keys'],15,MUTED,True)
footer=labels['wait'] if cfg['timeout']==0 else labels['countdown'].format(name=entries[0]['title'],seconds=cfg['timeout'])
text(d,W//2,976*S,footer,13,(112,133,148),True)
layer=Image.new('RGBA',canvas.size);ld=ImageDraw.Draw(layer)
for y in range(0,H,3*S):ld.rectangle((0,y,W,y+S-1),fill=(0,0,0,19))
canvas=Image.alpha_composite(canvas.convert('RGBA'),layer).convert('RGB');base=canvas.copy()
class Draw:
 def __init__(self,mask):self.d=ImageDraw.Draw(mask)
 def __getattr__(self,name):
  def draw(coords,**kw):
   for k in ('width','radius'):
    if k in kw:kw[k]*=S
   return getattr(self.d,name)(tuple(v*S for v in coords),**kw)
  return draw
def glyph(kind,size):
 m=Image.new('L',(size,size));g=Draw(m);c=255
 if kind=='windows':
  for x in (24,100):
   for y in (24,100):g.rectangle((x,y,x+68,y+68),fill=c)
 elif kind=='terminal':
  g.rounded_rectangle((34,44,158,144),radius=7,outline=c,width=2);g.line((35,65,157,65),fill=c,width=1)
  for x in (45,54,63):g.rectangle((x,53,x+2,55),fill=c)
  g.line((54,84,68,97,54,110),fill=c,width=3);g.line((84,115,116,115),fill=c,width=3)
 elif kind=='about':
  g.ellipse((11,11,37,37),outline=c,width=2);g.line((24,22,24,31),fill=c,width=2);g.ellipse((23,17,25,19),fill=c)
 elif kind=='reset':
  g.arc((11,11,37,37),start=25,end=320,fill=c,width=2);g.line((35,11,35,19,28,19),fill=c,width=2)
 elif kind=='shutdown':
  g.arc((12,12,36,36),start=-55,end=235,fill=c,width=2);g.line((24,10,24,24),fill=c,width=2)
 elif kind=='exit':
  g.line((23,12,13,12,13,36,23,36),fill=c,width=2);g.line((23,24,37,24,32,19),fill=c,width=2);g.line((37,24,32,29),fill=c,width=2)
 elif kind=='firmware':
  g.rectangle((16,16,32,32),outline=c,width=2);g.rectangle((21,21,27,27),outline=c,width=1)
  for v in (19,24,29):
   for line in [(v,10,v,15),(v,33,v,38),(10,v,15,v),(33,v,38,v)]:g.line(line,fill=c,width=2)
 elif kind=='key':
  g.ellipse((10,11,24,25),outline=c,width=2);g.line((22,23,36,37,39,34),fill=c,width=2);g.line((30,31,34,27),fill=c,width=2)
 return m
layout=[]
items=[(e['glyph'],f'entry-{i}.png',centers[i],main_top,big,.4) for i,e in enumerate(entries)]
tool_assets={'about':('about','func_about.png'),'reboot':('reset','func_reset.png'),'shutdown':('shutdown','func_shutdown.png'),'exit':('exit','func_exit.png'),'firmware':('firmware','func_firmware.png'),'mok_tool':('key','tool_mok_tool.png')}
items += [(tool_assets[t][0],tool_assets[t][1],x,tool_top,small,.9) for t,x in zip(tool_ids,tools)]
for kind,name,cx,y,size,scan in items:
 x=cx-size//2;box=(x,y,x+size,y+size);shape=glyph(kind,size);patch=base.crop(box)
 canvas.paste(Image.composite(Image.new('RGB',(size,size),DIM),patch,shape),box)
 coverage=shape.copy();px=coverage.load()
 for sy in range(0,size,3*S):
  for yy in range(sy,min(sy+S,size)):
   for xx in range(size):px[xx,yy]=round(px[xx,yy]*scan)
 stencil=patch.convert('RGBA');stencil.putalpha(ImageOps.invert(coverage));stencil.save(THEME/'icons'/name)
 layout.append({'name':name,'box':box})
canvas.save(THEME/'background.png')
for size,tile,name in [(big,bt,'selection_big.png'),(small,st,'selection_small.png')]:
 im=Image.new('RGBA',(tile,tile));pad=(tile-size)//2;ImageDraw.Draw(im).rectangle((pad,pad,pad+size-1,pad+size-1),fill=(*LIT,255));im.save(THEME/name)
n=18*S;f=ImageFont.truetype(str(HERE/'fonts/JetBrainsMono-Regular.ttf'),n);cell=round(f.getlength('M'));h=24*S
im=Image.new('RGBA',(cell*96,h));fd=ImageDraw.Draw(im);asc,desc=f.getmetrics()
for i in range(96):
 ch=chr(i+32) if i<95 else '?';fd.text((i*cell+(cell-f.getlength(ch))/2,(h-asc-desc)//2),ch,font=f,fill=(106,112,91,255))
im.save(THEME/'fonts/mono.png')
(THEME/'theme.conf').write_text(f"""# ICE / native {W}x{H}; fixed geometry, regenerate for changed entry/tool counts.
timeout {cfg['timeout']}
hideui hints,label,badges
icons_dir themes/ice/icons
banner themes/ice/background.png
banner_scale noscale
selection_big themes/ice/selection_big.png
selection_small themes/ice/selection_small.png
font themes/ice/fonts/mono.png
big_icon_size {big}
small_icon_size {small}
resolution {W} {H}
""",encoding='utf-8')
(OUT/'layout.json').write_text(json.dumps(layout,indent=2),encoding='utf-8')
example=['# EXAMPLE ONLY: verify every loader and volume before using.',
         '# Icons/loaders: absolute paths on the selected EFI volume. Theme paths: rEFInd-relative.',
         'scanfor manual','showtools '+','.join(tool_ids),'use_nvram false',
         'use_graphics_for windows','default_selection "'+entries[0]['title']+'"',
         'include themes/ice/theme.conf','']
for i,e in enumerate(entries):
 example+=['menuentry "'+e['title']+'" {',f'    icon {refind_dir}/themes/ice/icons/entry-{i}.png']
 if e.get('volume'): example+=['    volume "'+e['volume']+'"']
 example+=['    loader '+e['loader']]
 if e.get('ostype'): example+=['    ostype '+e['ostype']]
 example+=['}','']
(OUT/'refind.conf.example').write_text('\n'.join(example),encoding='utf-8')
# Local design preview. Not a firmware screenshot and not an OS launch test.
for i,entry in enumerate(layout):
 state=canvas.convert('RGBA');x,y,x2,y2=entry['box']
 state.paste(Image.new('RGBA',(x2-x,y2-y),(*LIT,255)),(x,y))
 state.alpha_composite(Image.open(THEME/'icons'/entry['name']),(x,y))
 state.convert('RGB').save(OUT/f'preview-{i}.png')
files=[f for f in THEME.rglob('*') if f.is_file()]
(OUT/'sha256.json').write_text(json.dumps({f.relative_to(THEME).as_posix():hashlib.sha256(f.read_bytes()).hexdigest() for f in files},indent=2))
print(f'Rendered {W}x{H}: {len(entries)} entries, {len(tools)} tools. Nothing installed.')
