"""生成 1080p 动态讲解视频、内嵌字幕、独立字幕与原创合成背景音乐。"""
import sys,math,json,re,subprocess,wave,functools,bisect
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'.video-deps'))
import numpy as np
from PIL import Image,ImageDraw,ImageFont
import imageio_ffmpeg
HERE=Path(__file__).parent;TMP=ROOT/'tmp/video';OUT=ROOT/'output/video';OUT.mkdir(parents=True,exist_ok=True)
FF=imageio_ffmpeg.get_ffmpeg_exe()
SCENES=json.loads((HERE/'scenes.json').read_text(encoding='utf-8'))
W,H=1920,1080;S=1.5;FPS=24
C={'bg':'#0A1423','panel':'#12243A','panel2':'#192F47','ink':'#F1F5F8','muted':'#9FB0C4','teal':'#42DBC2','orange':'#FFB15B','red':'#FF787F','line':'#2A4058','free':'#243B50','blue':'#7BA5FF'}
def p(x):return round(x*S)
def rgb(c):return tuple(bytes.fromhex(c.lstrip('#')))
@functools.lru_cache(256)
def font(size,bold=False,mono=False):
 return ImageFont.truetype('C:/Windows/Fonts/'+('consolab.ttf' if mono and bold else 'consola.ttf' if mono else 'msyhbd.ttc' if bold else 'msyh.ttc'),p(size))
@functools.lru_cache(3000)
def glyph(text,size,color,bold=False,mono=False):
 f=font(size,bold,mono);box=f.getbbox(text);im=Image.new('RGBA',(max(2,box[2]-box[0]+6),max(2,box[3]-box[1]+6)))
 ImageDraw.Draw(im).text((3-box[0],3-box[1]),text,font=f,fill=color)
 return im
def text(im,x,y,t,size=24,color=None,bold=False,mono=False,anchor='lt',alpha=255):
 if mono and any('\u4e00'<=ch<='\u9fff' for ch in str(t)):mono=False
 g=glyph(str(t),size,color or C['ink'],bold,mono)
 if alpha!=255:g=g.copy();g.putalpha(g.getchannel('A').point(lambda v:round(v*alpha/255)))
 xx=p(x)-(g.width//2 if anchor.startswith('m') else g.width if anchor.startswith('r') else 0)
 im.paste(g,(xx,p(y)),g)
def rect(im,box,fill,r=0,outline=None,width=1):
 ImageDraw.Draw(im).rounded_rectangle(tuple(p(v) for v in box),radius=p(r),fill=fill,outline=outline,width=p(width))
def line(im,points,fill,width=2):ImageDraw.Draw(im).line([(p(x),p(y)) for x,y in points],fill=fill,width=p(width))
def circle(im,x,y,r,fill,outline=None,width=1):ImageDraw.Draw(im).ellipse((p(x-r),p(y-r),p(x+r),p(y+r)),fill=fill,outline=outline,width=p(width))
def ease(v):v=max(0,min(1,v));return v*v*(3-2*v)
def lerp(a,b,v):return a+(b-a)*v
def pill(im,x,y,t,color=None):
 width=(glyph(t,14,C['ink']).width/S)+26;rect(im,(x,y,x+width,y+30),C['panel2'],15);text(im,x+13,y+6,t,14,color or C['muted'])
def arrow(im,x1,y1,x2,y2,col=None,width=2):
 col=col or C['muted'];line(im,[(x1,y1),(x2,y2)],col,width)
 ang=math.atan2(y2-y1,x2-x1);a=10
 pts=[(x2,y2),(x2-a*math.cos(ang-.5),y2-a*math.sin(ang-.5)),(x2-a*math.cos(ang+.5),y2-a*math.sin(ang+.5))]
 ImageDraw.Draw(im).polygon([(p(x),p(y)) for x,y in pts],fill=col)
def token(im,x,y,name,col=None,scale=1):
 col=col or C['teal'];circle(im,x,y-14*scale,12*scale,col)
 rect(im,(x-18*scale,y+2*scale,x+18*scale,y+37*scale),col,10*scale)
 text(im,x,y+45*scale,name,15,C['muted'],anchor='mt')
def heading_card(im,x,y,w,title,sub,color=None):
 rect(im,(x,y,x+w,y+124),C['panel'],14,outline=C['line'])
 text(im,x+22,y+22,title,28,color or C['ink'],True);text(im,x+22,y+75,sub,17,C['muted'])

def base(i):
 a=np.zeros((H,W,3),dtype=np.uint8)
 # 安静的深蓝渐变，保留字幕和视觉标记的对比度。
 for y in range(H):
  f=y/H;a[y,:,0]=round(10+4*f);a[y,:,1]=round(20+7*f);a[y,:,2]=round(35+10*f)
 im=Image.fromarray(a);d=ImageDraw.Draw(im)
 for x in range(50,W,75):
  for y in range(42,H-130,75):d.ellipse((x,y,x+1,y+1),fill='#243349')
 text(im,50,27,'M / MEMORY THEATER',15,C['teal'],True,True)
 text(im,1230,29,f'{i+1:02d} / {len(SCENES):02d}',14,C['muted'],mono=True,anchor='rt')
 line(im,[(50,63),(1230,63)],C['line'],1)
 text(im,50,85,SCENES[i]['chapter'],15,C['teal'])
 text(im,50,121,SCENES[i]['title'],38,C['ink'],True)
 text(im,52,177,SCENES[i]['subtitle'],19,C['muted'])
 return im
BASES=[base(i) for i in range(len(SCENES))]
def block(im,x,y,w,label,col,head=False,small=False):
 rect(im,(x,y,x+w,y+88),col,8)
 if head:rect(im,(x,y,x+w/4,y+88),'#1E565D',8)
 if w>50:text(im,x+w/2,y+28,label,22 if not small else 17,C['ink'],True,anchor='mt')
def memory(im,parts,y=355,head=False):
 x=80;totalw=1120
 for off in [0,32,64,96,128]:text(im,x+totalw*off/128,y-31,str(off),13,C['muted'],mono=True,anchor='mt')
 start=x
 for size,label,col in parts:
  ww=totalw*size/128;block(im,start,y,ww-3,label,col,head and not ('空闲' in label));start+=ww
def modelnote(im):text(im,80,554,'教学模型：128 B 固定池 / 8 B 头部 / 8 B 对齐 / 首次适配 / 相邻空闲块立即合并',15,C['muted'])

def draw_scene(i,t,duration):
 im=BASES[i].copy();u=t/duration;sid=SCENES[i]['id']
 # 所有镜头都有缓慢的环境运动和连续播放进度。
 for j in range(9):
  x=(50+j*149+t*(3+j*.3))%1280;y=240+((j*71)%320)
  circle(im,x,y,1.4,C['line'])
 if sid=='hook':
  text(im,75,262,'96',110,C['teal'],True,True);text(im,250,323,'B 空闲',30,C['muted'])
  text(im,78,416,'malloc(72)',43,C['ink'],True,True)
  text(im,78,480,'为什么是 NULL？',32,C['orange'],True)
  # 房间由远至近展开，形成旅馆外形。
  ox,oy=688,280
  for row in range(4):
   for col in range(4):
    shift=18*math.sin(t*.35+row*.7)
    x=ox+col*103-row*16;y=oy+row*65+shift
    used=(row==1)
    rect(im,(x,y,x+91,y+54),C['teal'] if used else C['panel2'],7,outline=C['line'])
    text(im,x+45,y+16,'B' if used else '空闲',16,C['bg'] if used else C['muted'],True,anchor='mt')
  pill(im,716,226,'MEMORY HOTEL · 内存旅馆',C['teal'])
 elif sid=='need':
  for idx,(title,items,col) in enumerate([('输入文本',['H','e','l','l','o','!'],C['teal']),('学生名单',['01','02','03','04','05','06'],C['blue'])]):
   x=75+idx*600;rect(im,(x,250,x+535,500),C['panel'],16,outline=C['line']);text(im,x+25,275,title,24,C['ink'],True)
   count=min(6,1+int(t*1.4)%8)
   for j in range(count):
    rect(im,(x+25+j*78,346,x+93+j*78,414),C['panel2'],7)
    text(im,x+59+j*78,363,items[j],24,col,True,True,anchor='mt')
   text(im,x+25,452,'运行时输入 → 决定所需容量',19,C['muted'])
  text(im,640,540,'按需申请，也要明确何时归还',29,C['teal'],True,anchor='mt')
 elif sid=='history':
  line(im,[(135,380),(1145,380)],C['line'],4)
  data=[(150,'1970s','C 与 Unix','运行时数据结构'),(475,'1987','dlmalloc','时间与空间的取舍'),(800,'1989','ANSI C','库接口标准化'),(1120,'现代','多线程分配器','缓存与并发优化')]
  for j,(x,a,b,c) in enumerate(data):
   v=ease((t-j*1.5)/2);circle(im,x,380,12,C['teal'] if v>.8 else C['line'])
   text(im,x,275+(1-v)*18,a,31,C['teal'],True,True,anchor='mt',alpha=round(v*255))
   text(im,x,421,b,25,C['ink'],True,anchor='mt',alpha=round(v*255))
   text(im,x,468,c,17,C['muted'],anchor='mt',alpha=round(v*255))
  text(im,640,550,'历史资料：Ritchie / Doug Lea / GNU libc / TCMalloc',14,C['muted'],anchor='mt')
 elif sid=='layers':
  xs=[80,480,880];titles=['应用程序','C 库分配器','操作系统'];codes=['malloc(72)','查找 / 复用 / 拆分','虚拟内存与页映射']
  for j in range(3):
   heading_card(im,xs[j],303,320,titles[j],codes[j],C['teal'] if j==1 else None)
   if j<2:arrow(im,xs[j]+333,365,xs[j]+385,365)
  phase=(t%4)/4
  px=lerp(385,484,ease(min(phase*2,1))) if phase<.5 else lerp(785,884,ease((phase-.5)*2))
  circle(im,px,365,8,C['orange'])
  text(im,640,486,'优先复用已有空间；必要时再向系统申请',28,C['teal'],True,anchor='mt')
  pill(im,491,545,'库函数 ≠ 每次都调用内核')
 elif sid=='rules':
  labels=[('128 B','固定池容量'),('8 B','模型头部'),('8 B','对齐粒度')]
  for j,(a,b) in enumerate(labels):
   x=80+j*400;rect(im,(x,265,x+320,410),C['panel'],14);text(im,x+160,290,a,52,C['teal'],True,True,anchor='mt');text(im,x+160,366,b,21,C['muted'],anchor='mt')
  memory(im,[(128,'空闲 128 B',C['free'])],y=475)
  scan=80+(t%5)/5*1120;line(im,[(scan,462),(scan,568)],C['orange'],3)
  text(im,640,590,'从左往右，寻找第一块足够大的空闲空间',21,C['orange'],anchor='mt')
 elif sid=='allocate':
  phase=min(3,int(t/4));n=max(1,phase)
  if phase==0:
   v=ease(t/2.5);start=80;block(im,start,365,lerp(1120,280,v)-3,'A' if v>.5 else '空闲',C['teal'],True)
   if v>.05:block(im,start+lerp(1120,280,v),365,1120-lerp(1120,280,v),'空闲',C['free'])
  else:
   parts=[(32,chr(65+j),C['teal'] if j==0 else C['blue'] if j==1 else '#B898F8') for j in range(min(3,phase))]
   parts.append((128-32*min(3,phase),'空闲',C['free']));memory(im,parts,y=365,head=True)
  for j in range(min(3,phase+1)):
   tx=210+j*280;token(im,tx,270,chr(65+j),[C['teal'],C['blue'],'#B898F8'][j]);arrow(im,tx,337,tx,357,C['muted'])
  text(im,80,495,'24 B 载荷',28,C['teal'],True);text(im,315,495,'+',28,C['muted']);text(im,380,495,'8 B 头部',28,C['blue'],True);text(im,607,495,'=',28,C['muted']);text(im,675,495,'32 B 块',28,C['orange'],True)
  modelnote(im)
 elif sid in ['free','fail','coalesce']:
  if sid=='free':
   if t<4:parts=[(32,'A',C['teal']),(32,'B',C['blue']),(32,'C','#B898F8'),(32,'空闲',C['free'])]
   elif t<8:parts=[(32,'空闲',C['free']),(32,'B',C['blue']),(32,'C','#B898F8'),(32,'空闲',C['free'])]
   else:parts=[(32,'空闲 32 B',C['free']),(32,'B',C['blue']),(64,'空闲 64 B',C['free'])]
   memory(im,parts);text(im,80,475,'free(A);',27,C['teal'],mono=True);text(im,430,475,'free(C);',27,'#B898F8',mono=True)
   text(im,975,475,'B 仍存活',27,C['blue'],True);modelnote(im)
  elif sid=='fail':
   memory(im,[(32,'32 B 空闲',C['free']),(32,'B',C['blue']),(64,'64 B 空闲',C['free'])])
   rect(im,(80,249,460,309),C['panel'],9);text(im,100,265,'D 请求：72 + 8 = 80 B',24,C['orange'],True)
   rect(im,(810,249,1200,309),'#412B37',9);text(im,1005,266,'NULL / 无连续 80 B',24,C['red'],True,anchor='mt')
   arrow(im,480,279,790,279,C['red'],3)
   text(im,80,485,'空闲总量',20,C['muted']);text(im,265,475,'96 B',45,C['teal'],True,True)
   text(im,695,485,'最大空闲块',20,C['muted']);text(im,920,475,'64 B',45,C['red'],True,True)
   text(im,80,558,'仅针对固定池：真实分配器还可能向系统申请更多空间',18,C['muted'])
   if int(t*2)%2==0:line(im,[(640,345),(640,453)],C['red'],4)
  else:
   if t<3:memory(im,[(32,'空闲',C['free']),(32,'B',C['blue']),(64,'空闲',C['free'])]);text(im,640,480,'free(B);',33,C['blue'],mono=True,anchor='mt')
   elif t<8:
    v=ease((t-3)/2);memory(im,[(128,'连续空闲 128 B',C['free'])]);text(im,640,480,'32 + 32 + 64 = 128 B',35,C['teal'],True,True,anchor='mt')
    for xx in [360,640]:line(im,[(xx,355),(xx,443)],'#243B50' if v>0.8 else C['muted'],2)
   else:memory(im,[(80,'D / 80 B',C['teal']),(48,'空闲 48 B',C['free'])]);text(im,640,480,'malloc(72) → 成功',34,C['teal'],True,True,anchor='mt')
   modelnote(im)
 elif sid=='padding':
  x=80;ww=1120;parts=[(8,'头部 8 B',C['blue']),(13,'有效载荷 13 B',C['teal']),(3,'',C['orange'])]
  start=x
  for size,label,col in parts:
   width=ww*size/24;rect(im,(start,315,start+width-3,425),col,7)
   if label:text(im,start+width/2,354,label,25,C['bg'],True,anchor='mt')
   start+=width
  arrow(im,1130,455,1130,432,C['orange']);text(im,1130,474,'填充 3 B',25,C['orange'],True,anchor='mt')
  text(im,80,490,'8 + 13 + 3 = 24 B',31,C['ink'],True,True)
  text(im,80,549,'头部属于管理开销；对齐填充属于内部碎片',23,C['muted'])
 elif sid=='safe':
  code=[('int *p = NULL;', '先建立指针变量'),('if (n > SIZE_MAX / sizeof *p) { /* handle */ }', '先防止乘法溢出'),('p = malloc(n * sizeof *p);','按所需字节申请'),('if (p == NULL) { /* handle */ }','失败要处理'),('p[0] = 80;','先初始化，再读取'),('free(p); p = NULL;','释放后停止访问')]
  active=min(5,int(t/(duration/6)))
  for j,(a,b) in enumerate(code):
   yy=235+j*55;rect(im,(70,yy,1210,yy+49),C['panel2'] if j==active else C['panel'],6)
   text(im,90,yy+13,f'{j+1:02d}',16,C['muted'],mono=True);text(im,145,yy+12,a,19,C['teal'] if j==active else C['ink'],mono=True)
   text(im,1178,yy+13,b,17,C['orange'] if j==active else C['muted'],anchor='rt')
  text(im,640,588,'扩容时，用临时指针接收 realloc 的结果；成功后再更新 p',18,C['muted'],anchor='mt')
 elif sid=='end':
  terms=[('01','请求大小','≠ 实际占用'),('02','空闲总量','≠ 最大空闲块'),('03','释放对象','≠ 立即归还系统'),('04','接口规则','≠ 实现细节')]
  for j,(a,b,cc) in enumerate(terms):
   x=75+(j%2)*600;y=251+(j//2)*129;rect(im,(x,y,x+530,y+110),C['panel'],12,outline=C['line']);text(im,x+22,y+24,a,30,C['teal'],True,True);text(im,x+89,y+19,b,25,C['ink'],True);text(im,x+89,y+61,cc,20,C['muted'])
  text(im,640,542,'github.com/daydream060415-web/malloc-memory-theater',19,C['teal'],mono=True,anchor='mt')
  text(im,640,577,'资料：WG14 N1570 / Ritchie / Doug Lea / GNU libc / TCMalloc',13,C['muted'],anchor='mt')
 # 内嵌字幕：独立于主画面，始终维持相同安全边距。
 captions=SCENES[i]['captions'];weights=[max(1,len(x)) for x in captions];cum=np.cumsum(weights)/sum(weights)
 ci=min(len(captions)-1,bisect.bisect_right(cum,min(.9999,max(0,(t-.2)/(duration-.7)))))
 rect(im,(35,627,1245,702),'#07101D',12)
 text(im,640,647,captions[ci],27,C['ink'],False,anchor='mt')
 # 场景编号进度与时间进度。
 for j in range(12):
  x=50+j*99;rect(im,(x,716,x+89,719),C['teal'] if j<i else C['line'],1)
  if j==i:rect(im,(x,716,x+89*u,719),C['teal'],1)
 # 镜头之间短淡入淡出，保留节奏而不遮挡长时间内容。
 fade=min(1,t/.35,(duration-t)/.35)
 if fade<1:im=Image.blend(Image.new('RGB',(W,H),C['bg']),im,max(0,fade))
 return im

def secstr(t):
 ms=round(t*1000);return f'{ms//3600000:02d}:{ms//60000%60:02d}:{ms//1000%60:02d},{ms%1000:03d}'
def audio_and_subs():
 sr=44100;offset=0;tracks=[];timeline=[];srt=[];idx=1
 for i,s in enumerate(SCENES):
  wav=TMP/'audio'/f'{i:02d}.wav'
  subprocess.run([FF,'-y','-v','error','-i',str(TMP/'audio'/f'{i:02d}.mp3'),'-ar',str(sr),'-ac','1',str(wav)],check=True)
  with wave.open(str(wav),'rb') as f:voice=np.frombuffer(f.readframes(f.getnframes()),dtype='<i2').astype(np.float32)/32768
  duration=math.ceil((len(voice)/sr+.75)*FPS)/FPS
  voice=np.pad(voice,(round(.15*sr),max(0,round(duration*sr)-len(voice)-round(.15*sr))))
  tracks.append(voice);timeline.append({'start':offset,'duration':duration,'id':s['id']})
  weights=np.array([len(x) for x in s['captions']],float);edges=np.r_[0,np.cumsum(weights)/weights.sum()]*(duration-.7)+.2
  for j,cap in enumerate(s['captions']):
   srt.append(f'{idx}\n{secstr(offset+edges[j])} --> {secstr(offset+edges[j+1])}\n{cap}\n');idx+=1
  offset+=duration
 total=np.concatenate(tracks);n=len(total);music=np.zeros(n,np.float32)
 # 原创低音量氛围配乐，使用和弦音与轻柔拨弦，避免引用现成曲目。
 bpm=78;beat=60/bpm;progressions=[[130.81,164.81,196.0,246.94],[110.,130.81,164.81,220.],[87.31,110.,130.81,174.61],[98.,123.47,146.83,196.]]
 for k,start in enumerate(np.arange(0,n/sr,beat*4)):
  chord=progressions[k%4];length=min(round(beat*4.8*sr),n-round(start*sr));tt=np.arange(length)/sr
  env=(1-np.exp(-tt*1.8))*np.exp(-tt/.9/4)
  for hz in chord:music[round(start*sr):round(start*sr)+length]+=.007*np.sin(2*np.pi*hz*tt)*env
 for k,start in enumerate(np.arange(0,n/sr,beat/2)):
  chord=progressions[int(start/(beat*4))%4];hz=chord[(k*3)%4]*4;length=min(round(.9*sr),n-round(start*sr));tt=np.arange(length)/sr
  music[round(start*sr):round(start*sr)+length]+=.014*(np.sin(2*np.pi*hz*tt)+.25*np.sin(4*np.pi*hz*tt))*np.exp(-tt*5)*np.minimum(1,tt*100)
 fade=np.minimum(1,np.arange(n)/(sr*2))*np.minimum(1,(n-np.arange(n))/(sr*3));music*=fade
 # 背景音乐随旁白轻微闪避，旁白始终清楚。
 total=np.clip(total*.93+music,-.98,.98)
 stereo=np.column_stack((total,total)).ravel()
 with wave.open(str(TMP/'mix.wav'),'wb') as f:f.setnchannels(2);f.setsampwidth(2);f.setframerate(sr);f.writeframes((stereo*32767).astype('<i2').tobytes())
 (OUT/'malloc-explained.zh-CN.srt').write_text('\n'.join(srt),encoding='utf-8')
 (TMP/'timeline.json').write_text(json.dumps(timeline,indent=2),encoding='utf-8')
 return timeline

def main():
 global draw_scene
 from visuals_warm import draw_scene as warm_scene
 draw_scene=warm_scene
 timeline=audio_and_subs();duration=sum(x['duration'] for x in timeline)
 print(f'Total duration: {duration:.2f}s / {duration/60:.2f}min',flush=True)
 # 保存各镜头样张以做内容、字幕与安全边距检查。
 for i,entry in enumerate(timeline):draw_scene(i,entry['duration']*.57,entry['duration']).save(TMP/f'scene-{i:02d}.jpg',quality=92)
 draw_scene(0,4,timeline[0]['duration']).save(OUT/'malloc-explained-cover.jpg',quality=95)
 if '--preview-only' in sys.argv:return
 cmd=[FF,'-y','-v','warning','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-', '-i',str(TMP/'mix.wav'),'-c:v','libx264','-preset','fast','-crf','23','-maxrate','750k','-bufsize','1500k','-pix_fmt','yuv420p','-c:a','aac','-b:a','112k','-movflags','+faststart','-shortest',str(OUT/'malloc-explained.mp4')]
 log=open(TMP/'encode.log','wb');proc=subprocess.Popen(cmd,stdin=subprocess.PIPE,stderr=log)
 try:
  for i,e in enumerate(timeline):
   for frame in range(round(e['duration']*FPS)):
    im=draw_scene(i,frame/FPS,e['duration']);proc.stdin.write(im.tobytes())
   print(f'rendered {i+1}/{len(timeline)}',flush=True)
  proc.stdin.close();ret=proc.wait()
  if ret:raise RuntimeError((TMP/'encode.log').read_text(errors='replace'))
 finally:
  log.close()
 print(OUT/'malloc-explained.mp4',flush=True)
if __name__=='__main__':main()
