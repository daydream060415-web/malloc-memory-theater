"""暖色纸感分镜：把申请、拆分、释放与碎片串成一场入住故事。"""
import bisect
import functools
import math
import sys

from PIL import Image, ImageDraw

v = sys.modules.get('__main__')
if not hasattr(v, 'SCENES'):
    import render_video as v

C = {
    'bg': '#F8F1E5', 'panel': '#FFFCF5', 'panel2': '#F0E4D2',
    'ink': '#3D3028', 'muted': '#796B5D', 'teal': '#587960',
    'orange': '#B66337', 'red': '#AF5044', 'line': '#D9CBB7',
    'free': '#E9DDC7', 'blue': '#6C8794', 'head': '#A99A82',
    'A': '#E8B18D', 'B': '#B8C6A4', 'C': '#E8CE8A',
}
v.C.update(C)
text, rect, line, circle, arrow = v.text, v.rect, v.line, v.circle, v.arrow
ease, lerp, p = v.ease, v.lerp, v.p

TITLES = [
    ('有空房，也住不进？', '先猜一猜：96 B 空闲，能接待 72 B 的请求吗？'),
    ('需要多大，运行时才知道', '把空间准备得恰到好处'),
    ('一个接口，半个世纪的演进', '接口规定行为，实现选择算法'),
    ('从一张申请单开始', '应用程序 → 分配器 → 操作系统'),
    ('先看这家旅馆的规则', '可手算的教学模型，不代表所有 malloc 实现'),
    ('带上钥匙，依次入住', '申请 24 B，模型中的块占 32 B'),
    ('A、C 退房，B 留下', '空闲块相邻，才可以直接合并'),
    ('轮到 D：这次能入住吗？', '把“空闲总量”和“连续空间”分开看'),
    ('退掉中间一间，再试一次', '同样的请求，不同的空闲布局'),
    ('放大一个 13 B 的请求', '分清管理开销、内部碎片与外部碎片'),
    ('真正写 C，还要管好钥匙', '检查 → 初始化 → 使用 → 释放'),
    ('下次看 malloc，看这四件事', '从“要多少”到“何时归还”'),
]


def label(im, x, y, title, color=None, size=16):
    col = color or C['orange']
    w = v.glyph(title, size, col).width / v.S + 26
    rect(im, (x, y, x+w, y+31), C['panel2'], 15)
    text(im, x+13, y+6, title, size, col, True)
    return w


def card(im, box, fill=None, radius=17, outline=None):
    x, y, xx, yy = box
    rect(im, (x+2, y+5, xx+2, yy+5), '#E8DFCF', radius)
    rect(im, box, fill or C['panel'], radius, outline or C['line'])


@functools.lru_cache(12)
def base(i):
    im = Image.new('RGB', (v.W, v.H), C['bg'])
    # 大面积留白配合纸页边缘的浅橙圆弧，避免背景抢走叙事焦点。
    circle(im, 1252, 100, 184, '#F1DDC5')
    circle(im, 1260, 100, 146, C['bg'])
    circle(im, 28, 600, 130, '#F2E7D4')
    text(im, 49, 26, 'M / 内存旅馆', 17, C['orange'], True)
    text(im, 1230, 29, f'{i+1:02d} / 12', 15, C['muted'], mono=True, anchor='rt')
    line(im, [(50, 63), (1230, 63)], C['line'], 1)
    text(im, 50, 84, v.SCENES[i]['chapter'], 15, C['orange'])
    text(im, 50, 120, TITLES[i][0], 38, C['ink'], True)
    text(im, 52, 177, TITLES[i][1], 19, C['muted'])
    return im


def traveller(im, x, y, name, col, scale=1, walk=0, face=True):
    """y 为脚底，角色与行李同步移动，形成可读的入场和退场。"""
    s=scale; bob=math.sin(walk*9)*2 if walk else 0
    def rr(a,b,c,d,fill,r=0): rect(im,(x+a*s,y+(b+bob)*s,x+c*s,y+(d+bob)*s),fill,r*s)
    circle(im,x,y-75*s+bob,15*s,'#E7B999')
    rr(-17,-97,17,-86,C['ink'],5);rr(-25,-89,25,-83,C['ink'],3)
    rr(-21,-55,21,-15,col,9)
    line(im,[(x-9*s,y-15*s),(x-(9+math.sin(walk*9)*7)*s,y)],C['ink'],5*s)
    line(im,[(x+9*s,y-15*s),(x+(9+math.sin(walk*9)*7)*s,y)],C['ink'],5*s)
    line(im,[(x+21*s,y-45*s),(x+39*s,y-29*s)],C['ink'],3*s)
    rr(31,-29,59,-1,col,5);rr(38,-37,51,-29,C['head'],2)
    circle(im,x+37*s,y+1*s,3*s,C['ink']);circle(im,x+53*s,y+1*s,3*s,C['ink'])
    if face:
        circle(im,x+5*s,y-76*s+bob,1.6*s,C['ink'])
        line(im,[(x+4*s,y-69*s+bob),(x+9*s,y-69*s+bob)],C['orange'],1.4*s)
    text(im,x,y-48*s+bob,name,20*s,C['ink'],True,anchor='mt')


def key(im,x,y,color=None,scale=1):
    col=color or C['orange'];circle(im,x,y,8*scale,None,col,3*scale)
    line(im,[(x+8*scale,y),(x+31*scale,y)],col,4*scale)
    line(im,[(x+24*scale,y),(x+24*scale,y+7*scale)],col,3*scale)
    line(im,[(x+31*scale,y),(x+31*scale,y+7*scale)],col,3*scale)


def ticks(im,y=340,x=80,w=1120):
    for off in range(0,129,8):
        xx=x+w*off/128
        line(im,[(xx,y-7),(xx,y-1)],C['head'],1)
        if off%32==0:text(im,xx,y-30,str(off),14,C['muted'],mono=True,anchor='mt')


def memblock(im,x,y,w,title,col,allocated=False,alpha=1):
    if w<6:return
    rect(im,(x,y,x+w-3,y+86),col,8,C['line'])
    if allocated:
        # 头部严格按 8 B 与块宽比例画，不把所有块都误画成四等分。
        hw=1120*8/128
        rect(im,(x,y,x+min(hw,w-4),y+86),C['head'],7)
        text(im,x+hw/2,y+31,'H',16,C['panel'],True,mono=True,anchor='mt')
    if w>120:
        xx=x+(w+(1120*8/128 if allocated else 0))/2
        text(im,xx,y+29,title,23,C['ink'],True,anchor='mt')


def memory(im,parts,y=355):
    ticks(im,y);x=80
    for size,title,col,used in parts:
        memblock(im,x,y,1120*size/128,title,col,used);x+=1120*size/128
    text(im,1200,y+99,'模拟地址 / B',13,C['muted'],anchor='rt')


def note(im,content='教学模型：128 B 固定池 · 8 B 头部 · 8 B 对齐 · 首次适配'):
    text(im,80,588,content,15,C['muted'])


def counter(im,x,y,num,unit,caption,col=None):
    text(im,x,y,str(num),49,col or C['orange'],True,mono=True)
    text(im,x+v.glyph(str(num),49,C['ink'],True,True).width/v.S+8,y+20,unit,22,C['muted'])
    text(im,x,y+63,caption,18,C['muted'])


def stamp(im,x,y,title,col):
    w=v.glyph(title,25,col,True).width/v.S+34
    rect(im,(x,y,x+w,y+52),C['panel'],10,col,2)
    text(im,x+17,y+12,title,25,col,True)


def draw_scene(i,t,duration):
    im=base(i).copy();u=t/duration;sid=v.SCENES[i]['id']
    if sid=='hook':
        card(im,(670,235,1205,584))
        rect(im,(723,248,1152,292),C['A'],8)
        text(im,938,259,'MEMORY HOTEL',23,C['ink'],True,mono=True,anchor='mt')
        for j,(title,col) in enumerate([('空闲 32 B',C['free']),('B 正在入住',C['B']),('空闲 64 B',C['free'])]):
            yy=311+j*74;rect(im,(713,yy,1165,yy+58),col,7)
            text(im,939,yy+17,title,23,C['ink'],True,anchor='mt')
        text(im,80,246,'空闲总量',20,C['muted'])
        text(im,75,278,'96 B',80,C['orange'],True,mono=True)
        text(im,80,393,'malloc(72)',35,C['ink'],True,mono=True)
        text(im,80,448,'够不够？',34,C['orange'],True)
        x=lerp(470,603,ease(t/3));traveller(im,x,558,'D',C['A'],1.04,t if t<3 else 0)
        if t>3:
            text(im,585,365,'?',54,C['orange'],True,mono=True,anchor='mt')
        label(im,80,535,'带着这个问题，开始入住实验')
    elif sid=='need':
        stage=0 if t<5.6 else 1 if t<10.4 else 2
        card(im,(80,250,1200,538))
        headings=['预留 8 格，只来 3 人','预留 3 格，却来了 6 人','知道人数后，申请 6 格']
        text(im,110,275,headings[stage],28,C['ink'],True)
        cap=[8,3,6][stage];count=[3,6,6][stage]
        for j in range(8):
            xx=115+j*133;present=j<cap
            rect(im,(xx,356,xx+112,449),C['panel2'] if present else C['panel'],11,C['line'])
            if j<count:
                delay=[0,5.6,10.4][stage]+j*.18
                yy=lerp(342,428,ease((t-delay)/.6))
                if stage==1 and j>=cap:
                    rect(im,(xx,356,xx+112,449),'#F3D8CE',11,C['red'],2)
                traveller(im,xx+45,yy,str(j+1),C['A'] if stage!=2 else C['B'],.58)
            elif present:text(im,xx+56,385,'空置',19,C['muted'],anchor='mt')
        phrases=[('太大：空置 5 格',C['orange']),('太小：还差 3 格',C['red']),('按需申请，容量正好',C['teal'])]
        text(im,640,482,phrases[stage][0],25,phrases[stage][1],True,anchor='mt')
        for j,title in enumerate(['浪费','装不下','按需分配']):
            col=C['orange'] if j==stage else C['muted'];circle(im,380+j*250,578,12,col if j==stage else C['line'])
            text(im,401+j*250,566,title,21,col,True)
    elif sid=='history':
        times=[('1970s','C × Unix','运行时数据结构'),('1987','dlmalloc','速度与空间的取舍'),('1989','ANSI C','统一接口规范'),('现代','并发分配器','缓存与多区域管理')]
        line(im,[(145,380),(1135,380)],C['line'],5)
        progress=ease(t/(duration*.88));line(im,[(145,380),(145+990*progress,380)],C['orange'],5)
        active=0 if t<6 else 2 if t<10 else 1 if t<13 else 3
        for j,(year,title,sub) in enumerate(times):
            x=145+j*330;col=C['orange'] if j==active else C['muted']
            circle(im,x,380,14,C['orange'] if progress>=j/3 else C['panel'],C['line'],2)
            text(im,x,274,year,34,col,True,mono=True,anchor='mt')
            text(im,x,419,title,24,C['ink'],True,anchor='mt')
            text(im,x,461,sub,17,C['muted'],anchor='mt')
            if j==active:line(im,[(x-54,321),(x+54,321)],C['orange'],3)
        card(im,(230,527,1050,589));text(im,640,547,'相同的 malloc，内部可以有不同算法',24,C['orange'],True,anchor='mt')
    elif sid=='layers':
        names=[('应用程序','我需要 72 B'),('C 库分配器','查找 · 复用 · 拆分'),('操作系统','虚拟内存与页映射')]
        for j,(title,sub) in enumerate(names):
            yy=236+j*117;card(im,(90,yy,573,yy+94),C['panel'] if j!=1 else '#F4DFC8')
            text(im,118,yy+18,title,26,C['ink'],True);text(im,118,yy+58,sub,18,C['muted'])
            if j<2:arrow(im,335,yy+96,335,yy+113,C['orange'],2)
        if t<6:
            q=ease(t/4);yy=lerp(270,389,q);label(im,474,yy,'72 B 申请单')
        elif t<11.5:
            card(im,(691,269,1191,482));text(im,723,294,'先在已有内存里找',26,C['teal'],True)
            for j in range(5):rect(im,(725+j*83,360,795+j*83,416),C['free'] if j!=2 else C['B'],7)
            scan=725+(t-6)/5.5*330;line(im,[(scan,348),(scan,429)],C['orange'],3)
            text(im,723,449,'找到合适空闲块 → 直接复用',19,C['muted'])
            arrow(im,685,389,600,389,C['teal'],3)
        else:
            card(im,(691,269,1191,482));text(im,723,294,'必要时，再申请更多',26,C['orange'],True)
            arrow(im,880,344,880,408,C['orange'],4)
            text(im,880,440,'不要求每次都进入内核',21,C['muted'],anchor='mt')
            arrow(im,600,506,685,506,C['orange'],3)
        text(im,943,552,'malloc 是库函数',25,C['orange'],True,anchor='mt')
    elif sid=='rules':
        label(im,80,235,'本片演示参数 · 非 C 标准固定规定')
        data=[('128 B','固定内存池'),('8 B','每块管理头部'),('8 B','载荷对齐粒度')]
        for j,(num,title) in enumerate(data):
            yy=lerp(324,284,ease((t-j*1.2)/.8));card(im,(80+j*385,yy,420+j*385,yy+130))
            text(im,250+j*385,yy+20,num,43,C['orange'],True,mono=True,anchor='mt')
            text(im,250+j*385,yy+84,title,21,C['muted'],anchor='mt')
        memory(im,[(128,'空闲 128 B',C['free'],False)],y=465)
        scan=80+1120*min(1,max(0,(t-7)/(duration-7)))
        line(im,[(scan,453),(scan,557)],C['orange'],3)
        text(im,640,587,'首次适配：从左向右，找到第一块足够大的空闲空间',21,C['orange'],True,anchor='mt')
    elif sid=='allocate':
        starts=[.8,9.4,11.8];done=sum(t>=s+.9 for s in starts)
        parts=[]
        for j in range(done):parts.append((32,f'{chr(65+j)} / 32 B',C[chr(65+j)],True))
        # 新分配块逐渐从空闲块中拆出，地址顺序始终保持不变。
        partial=0
        if done<3 and t>=starts[done]:
            partial=32*ease((t-starts[done])/.9)
            if partial>.3:parts.append((partial,f'{chr(65+done)} / 32 B',C[chr(65+done)],True))
        rem=128-32*done-partial
        if rem:parts.append((rem,'正在拆分' if partial else f'空闲 {int(rem)} B',C['free'],False))
        memory(im,parts)
        for j,s in enumerate(starts):
            if t<s:continue
            q=ease((t-s)/1);target=80+j*280+163
            x=lerp(1165,target,q);traveller(im,x,305,chr(65+j),C[chr(65+j)],.72,t if q<1 else 0)
            if q==1:
                payload=80+j*280+70
                key(im,payload,468,C['orange'],.8)
                text(im,payload+36,458,f'p{chr(65+j)} = +{8+j*32}',18,C['muted'],mono=True)
                arrow(im,payload,450,payload,443,C['orange'],2)
            else:
                boundary=80+j*280+280*q
                line(im,[(boundary,346),(boundary,446)],C['orange'],3)
        text(im,80,526,'24 B 载荷  +  8 B 头部  =  32 B 块',29,C['orange'],True)
        if t>14:label(im,856,527,'3 位旅客：72 B 数据 / 96 B 块')
        note(im,'H = 模型管理头部；钥匙指向载荷起点，不指向头部')
    elif sid=='free':
        a=t>1.6;c=t>4.8;merged=t>7
        parts=[(32,'空闲 32 B' if a else 'A / 32 B',C['free'] if a else C['A'],not a),(32,'B / 32 B',C['B'],True)]
        if merged:parts.append((64,'连续空闲 64 B',C['free'],False))
        else:parts.extend([(32,'空闲 32 B' if c else 'C / 32 B',C['free'] if c else C['C'],not c),(32,'空闲 32 B',C['free'],False)])
        memory(im,parts)
        traveller(im,523,304,'B',C['B'],.72)
        for j,start in [(0,1.6),(2,4.8)]:
            q=ease((t-start)/1.5)
            if q<1:traveller(im,lerp(243+j*280,1265,q),304,chr(65+j),C[chr(65+j)],.72,t if q>0 else 0)
        if c and not merged:
            q=ease((t-4.8)/2.2);line(im,[(920,355),(920,441)],C['panel'] if q>.7 else C['orange'],3)
            arrow(im,899,495,937,495,C['orange'],3)
        label(im,80,245,'free(A)   +   free(C)',C['orange'])
        if merged:
            counter(im,80,494,96,'B','空闲总量',C['teal']);counter(im,741,494,64,'B','最大连续空闲块',C['orange'])
        else:text(im,640,525,'相邻的两块空闲空间，正在合并',25,C['orange'],True,anchor='mt')
        note(im,'B 的对象仍然存活：不能跨过 B 拼接两侧空闲空间')
    elif sid=='fail':
        memory(im,[(32,'空闲 32 B',C['free'],False),(32,'B / 32 B',C['B'],True),(64,'空闲 64 B',C['free'],False)],y=388)
        q=ease(t/3.5);requestx=lerp(80,500,q)
        rect(im,(requestx,277,requestx+700,327),'#F4D4BB',7,C['orange'],2)
        text(im,requestx+350,289,'D：72 B 载荷 + 8 B 头部 = 80 B',23,C['ink'],True,anchor='mt')
        if t<3.5:label(im,80,236,'先猜答案：能放在哪一段？')
        if t>3.5:
            line(im,[(640,344),(1200,344)],C['orange'],3)
            text(im,920,352,'最大只有 64 B',18,C['orange'],True,anchor='mt')
            line(im,[(500,334),(500,367)],C['red'],2)
            text(im,505,240,'多出来的 16 B，无法跨过 B',22,C['red'],True)
        if t>6:stamp(im,80,519,'NULL · 外部碎片',C['red'])
        text(im,1200,530,'96 B 总量  /  64 B 最大块  /  80 B 需求',23,C['ink'],True,anchor='rt')
        note(im,'仅针对固定池：真实分配器还可能向操作系统申请更多空间')
    elif sid=='coalesce':
        if t<2.9:
            memory(im,[(32,'空闲 32 B',C['free'],False),(32,'B / 32 B',C['B'],True),(64,'空闲 64 B',C['free'],False)])
            q=ease((t-.8)/1.5)
            if q<1:traveller(im,lerp(523,1256,q),304,'B',C['B'],.72,t)
            label(im,80,245,'free(B)：最后一位住客退房')
        elif t<7.2:
            memory(im,[(128,'连续空闲 128 B',C['free'],False)])
            q=ease((t-2.9)/1.7)
            for x in [360,640]:
                h=86*(1-q)
                if h>1:line(im,[(x,355+(86-h)/2),(x,355+(86+h)/2)],C['orange'],3)
            text(im,640,501,'32 + 32 + 64 = 128 B',35,C['teal'],True,mono=True,anchor='mt')
            label(im,80,245,'相邻边界消失，重新连成一整块')
        else:
            q=ease((t-7.2)/1.5);sz=max(.1,80*q)
            memory(im,[(sz,'D / 80 B',C['A'],True),(128-sz,'空闲 48 B' if q==1 else '空闲',C['free'],False)])
            traveller(im,lerp(1170,465,q),304,'D',C['A'],.72,t if q<1 else 0)
            stamp(im,80,503,'malloc(72) · 成功',C['teal'])
            text(im,1200,513,'128 − 80 = 48 B 剩余',29,C['orange'],True,anchor='rt')
            label(im,80,245,'同一个请求，这次住得下')
        note(im,'合并空闲块不等于移动存活对象：本例先释放 B，才消除中间阻隔')
    elif sid=='padding':
        label(im,80,238,'放大镜：一个块中的每一个字节')
        x0=80;ww=1120/24;yy=340
        for j in range(24):
            xx=x0+j*ww;col=C['head'] if j<8 else C['A'] if j<21 else C['C']
            rect(im,(xx,yy,xx+ww-2,yy+87),col,4)
            if j>=21:
                for k in range(3):line(im,[(xx+5,yy+14+k*23),(xx+ww-8,yy+33+k*23)],'#B5A061',1)
            if t>2:text(im,xx+ww/2,yy+109,str(j),12,C['muted'],mono=True,anchor='mt')
        vals=[(8,'管理头部 8 B',C['muted']),(13,'有效载荷 13 B',C['orange']),(3,'填充 3 B',C['orange'])];xx=x0
        for size,title,col in vals:
            w=size*ww;line(im,[(xx+3,314),(xx+w-4,314)],col,2);text(im,xx+w/2,278,title,22,col,True,anchor='mt');xx+=w
        card(im,(80,503,1200,563));text(im,640,520,'8 B 管理开销  +  13 B 数据  +  3 B 内部碎片  =  24 B',25,C['ink'],True,anchor='mt')
        if t>6:arrow(im,1130,478,1130,430,C['orange'],3)
        note(im,'内部碎片：块内的对齐填充；外部碎片：空闲空间被分散成多段')
    elif sid=='safe':
        rows=[('if (n == 0 || n > SIZE_MAX / sizeof *p)', '验证长度与乘法'),('    return EXIT_FAILURE;', '失败分支及时退出'),('p = malloc(n * sizeof *p);', '申请字节数'),('if (p == NULL) return EXIT_FAILURE;', '检查空指针'),('p[0] = 80; /* ... */', '先初始化，再读取'),('free(p); p = NULL;', '释放后停止访问')]
        active=0 if t<3 else 2 if t<4.5 else 3 if t<6.4 else 4 if t<13 else 5
        card(im,(78,237,910,562));text(im,103,253,'●  ●  ●      lifecycle.c',16,C['muted'],mono=True)
        for j,(code,hint) in enumerate(rows):
            yy=299+j*40
            if j==active:rect(im,(90,yy-5,895,yy+29),'#F4DFC8',5)
            text(im,109,yy,f'{j+1:02d}',15,C['head'],mono=True)
            text(im,150,yy,code,20,C['ink'],mono=True)
        key(im,1030,305,C['orange'],1.7)
        text(im,1048,359,rows[active][1],21,C['orange'],True,anchor='mt')
        text(im,1048,407,'释放之后' if t>13 else '申请成功',19,C['teal'],anchor='mt')
        text(im,1048,441,'停止访问原对象' if t>13 else '才可使用对象',19,C['muted'],anchor='mt')
        if 9<t<13:
            card(im,(105,477,888,552),'#F0E8D8')
            text(im,130,491,'int *next = realloc(p, new_bytes);',20,C['ink'],mono=True)
            text(im,130,525,'用临时指针接收；失败时，原分配仍可处理',18,C['orange'])
        note(im,'片段假设 p 已声明且初始为 NULL，n 为 size_t；扩容前同样要检查字节数')
    elif sid=='end':
        items=[('大小','24 B 申请 → 32 B 块','请求大小与实际占用'),('连续性','96 B 空闲 → 最大 64 B','总量与最大块'),('生命周期','free → 停止访问原对象','释放未必立即归还系统')]
        for j,(title,example,sub) in enumerate(items):
            x=80+j*385;yy=lerp(287,251,ease((t-j*.8)/.8));card(im,(x,yy,x+350,yy+207))
            text(im,x+25,yy+22,f'0{j+1}',18,C['orange'],True,mono=True)
            text(im,x+25,yy+58,title,32,C['ink'],True)
            text(im,x+25,yy+116,example,20,C['orange'],True)
            text(im,x+25,yy+163,sub,17,C['muted'])
        text(im,640,483,'第四件事：区分接口规则与具体实现',23,C['orange'],True,anchor='mt')
        card(im,(80,528,1200,600),'#F2DFC8')
        text(im,105,542,'继续探索 · 代码 / 交互 / 资料',16,C['muted'],True)
        text(im,105,570,'github.com/daydream060415-web/malloc-memory-theater',23,C['ink'],mono=True)

    # 字幕独立于主画面，深棕色字置于暖白底，保持一致的阅读区。
    captions=v.SCENES[i]['captions'];weights=[len(x) for x in captions]
    total=sum(weights);cum=[];acc=0
    for w in weights:acc+=w;cum.append(acc/total)
    ci=min(len(captions)-1,bisect.bisect_right(cum,min(.9999,max(0,(t-.2)/(duration-.7)))))
    rect(im,(35,627,1245,702),C['panel'],13,C['line'])
    rect(im,(35,641,40,687),C['orange'],2)
    text(im,640,648,captions[ci],27,C['ink'],anchor='mt')
    for j in range(12):
        x=50+j*99;rect(im,(x,716,x+89,719),C['orange'] if j<i else C['line'],1)
        if j==i:rect(im,(x,716,x+89*u,719),C['orange'],1)
    fade=min(1,t/.3,(duration-t)/.3)
    if fade<1:im=Image.blend(Image.new('RGB',(v.W,v.H),C['bg']),im,max(0,fade))
    return im
