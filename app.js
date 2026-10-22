'use strict';
const $ = id => document.getElementById(id);
const scenes = [
  {title:'数据有多大？运行时才知道。',chapter:'第一幕 / 从需求到接口',code:'size_t n = read_count();\nint *p = malloc(n * sizeof *p);',text:'旅客数量到达时才确定。动态分配允许程序在运行时申请空间，并明确控制它何时释放。',tip:'上方是动机伪代码：真实代码还要检查长度乘法溢出和返回值。',action:null},
  {title:'A 入住：24 B 请求，占用 32 B。',chapter:'第二幕 / 请求与实际占用',code:'A = malloc(24);',text:'模型先找第一个够大的空闲块，保留 8 B 管理头部，再交出 24 B 可用空间。剩余部分拆成空闲块。',tip:'A 指向有效载荷的起点 +8。管理头部不是用户可以读写的区域。',action:['alloc',24,'A']},
  {title:'B 入住：继续拆分空闲块。',chapter:'第二幕 / 首次适配与拆分',code:'B = malloc(24);',text:'首次适配跳过 A，从下一个足够大的空闲块切出 32 B。B 的模拟有效载荷起点是 +40。',tip:'这里的分配顺序由教学算法决定，C 标准不保证连续分配的地址顺序。',action:['alloc',24,'B']},
  {title:'C 入住：只剩最后 32 B。',chapter:'第二幕 / 读懂一张内存地图',code:'C = malloc(24);',text:'三个对象各需要 24 B 载荷与 8 B 模型头部。72 B 有效数据，实际占用 96 B。',tip:'返回非空指针后先初始化再读取；malloc 不会自动把数据清零。',action:['alloc',24,'C']},
  {title:'A 退房：留下第一个空洞。',chapter:'第三幕 / 释放与生命周期',code:'free(A);\nA = NULL;',text:'A 所占的 32 B 可以再次分配。原对象的生命周期结束，之后不能通过旧指针访问它。',tip:'给 A 置 NULL 是编程习惯；free 自身不会修改 A，也不会自动修复其他别名。',action:['free','A']},
  {title:'C 退房：相邻空闲块合并。',chapter:'第三幕 / 外部碎片出现',code:'free(C);\nC = NULL;',text:'C 与右侧空闲块相邻，立即合并成 64 B。空闲总量已经是 96 B，但被 B 分隔成两段。',tip:'合并只发生在相邻空闲块之间。不能跨过仍在使用的 B，也没有移动 B。',action:['free','C']},
  {title:'96 B 空闲，为什么还会失败？',chapter:'第四幕 / 碎片的反直觉时刻',code:'D = malloc(72);\n/* 模型结果：NULL */',text:'72 B 载荷加 8 B 头部，需要连续 80 B。当前最大空闲块只有 64 B，因此固定池中的请求失败。',tip:'这是外部碎片案例。真实分配器还可能向系统申请更多空间，不一定在此处失败。',action:['alloc',72,'D']},
  {title:'B 退房：三段重新连成一片。',chapter:'第五幕 / 合并恢复大块',code:'free(B);\nB = NULL;',text:'中间的阻隔消失。模型把左、中、右三个相邻空闲块合并，恢复完整的 128 B。',tip:'“合并”只更新空闲块的管理信息；本案例不搬迁任何存活对象。',action:['free','B']},
  {title:'同样的请求，这次入住成功。',chapter:'第五幕 / 再次分配',code:'D = malloc(72);\nif (D == NULL) { /* 处理失败 */ }',text:'现在有连续 128 B。分配 80 B 后，还剩 48 B。请求没有变化，变化的是可用空间的形状。',tip:'调用方始终要检查 NULL；不要把一次成功当成以后都会成功的保证。',action:['alloc',72,'D']},
  {title:'退房完成，故事回到起点。',chapter:'终幕 / 把所有权交代清楚',code:'free(D);\nD = NULL;',text:'所有分配都已归还。申请、检查、初始化、使用、释放，是一段完整的动态内存生命周期。',tip:'free 使空间可供分配器复用，不等于物理内存立即归还操作系统。',action:['free','D']}
];
let allocator = new Allocator(), step=0, timer=null, mode='story';
function perform(a, action) { if(!action) return; return action[0]==='alloc' ? a.allocate(action[1],action[2]) : a.release(action[1]); }
function paint() {
  const keep = new Set();
  allocator.blocks.forEach(b=>{
    const key=b.id || `free-${b.start}`; keep.add(key);
    let el=Array.from($('memory').children).find(e=>e.dataset.key===key);
    if(!el){el=document.createElement('div');el.dataset.key=key;el.className='block';$('memory').append(el);}
    el.className=`block ${b.id?'used':'free'}`; el.style.left=`${b.start/128*100}%`;el.style.width=`${b.size/128*100}%`;
    const padding=b.size-b.requested-8;
    el.innerHTML=b.id ? `<span class="header-part" style="width:${8/b.size*100}%"></span><span class="payload-part">${b.id}</span>${padding?`<span class="padding-part" style="width:${padding/b.size*100}%"></span>`:''}` : '<span class="payload-part">空闲</span>';
  });
  Array.from($('memory').children).forEach(el=>{if(!keep.has(el.dataset.key))el.remove();});
  const labels=allocator.blocks.map(b=>b.id ? `${b.id} · +${b.start+8} · 载荷 ${b.requested} B / 块 ${b.size} B` : `空闲 · [${b.start}, ${b.start+b.size}) · ${b.size} B`);
  $('memory').setAttribute('aria-label',labels.join('；'));
  $('block-list').replaceChildren(...labels.map(t=>{const d=document.createElement('span');d.className='block-label';d.textContent=t;return d;}));
  const s=allocator.stats(); for(const [id,key] of [['free','free'],['largest','largest'],['payload','payload']]) $(id+'-value').innerHTML=`${s[key]} <small>B</small>`;
  const previous=$('allocation').value;
  $('allocation').replaceChildren(...allocator.blocks.filter(b=>b.id).map(b=>{const o=document.createElement('option');o.value=b.id;o.textContent=`${b.id} (${b.requested} B)`;return o;}));
  if(Array.from($('allocation').options).some(o=>o.value===previous))$('allocation').value=previous;
  $('release').disabled=!$('allocation').options.length;
}
function renderStory() {
  allocator=new Allocator(); for(let i=0;i<=step;i++)perform(allocator,scenes[i].action);
  const s=scenes[step];$('scene-title').textContent=s.title;$('chapter').textContent=s.chapter;$('operation').textContent=s.code;$('narration').textContent=s.text;$('takeaway').textContent=s.tip;$('counter').textContent=`${String(step+1).padStart(2,'0')} / ${scenes.length}`;
  $('prev').disabled=step===0;$('next').disabled=step===scenes.length-1;paint();
}
function stop(){clearTimeout(timer);timer=null;$('play').textContent='播放动画';}
function schedule(){timer=setTimeout(()=>{if(step<scenes.length-1){step++;renderStory();if(step===scenes.length-1)stop();else schedule();}else stop();},Number($('speed').value));}
function switchMode(next){stop();mode=next;const story=mode==='story';$('story-controls').hidden=!story;$('lab-controls').hidden=story;for(const id of ['story','lab']){$(id+'-tab').classList.toggle('active',id===mode);$(id+'-tab').setAttribute('aria-pressed',String(id===mode));}if(story)renderStory();else{allocator=new Allocator();$('chapter').textContent='实验室 / 改变请求，观察空间';$('scene-title').textContent='亲手安排一次入住。';$('counter').textContent='LIVE';$('operation').textContent='等待 malloc / free';$('narration').textContent='输入请求大小后分配空间，再选择一个存活分配进行释放。';$('takeaway').textContent='例如申请 13 B：模型头部 8 B、载荷 13 B、对齐填充 3 B，共占 24 B。';paint();}}
$('prev').onclick=()=>{stop();if(step>0){step--;renderStory();}};
$('next').onclick=()=>{stop();if(step<scenes.length-1){step++;renderStory();}};
$('reset').onclick=()=>{stop();step=0;renderStory();};
$('play').onclick=()=>{if(timer){stop();return;}if(step===scenes.length-1){step=0;renderStory();}$('play').textContent='暂停动画';schedule();};
$('speed').onchange=()=>{if(timer){clearTimeout(timer);schedule();}};
$('story-tab').onclick=()=>switchMode('story');$('lab-tab').onclick=()=>switchMode('lab');
$('allocate').onclick=()=>{const n=Number($('bytes').value),r=allocator.allocate(n);$('operation').textContent=`malloc(${n});`;$('narration').textContent=r.ok?`${r.id} 入住成功，模拟指针偏移 +${r.ptr}，占用 ${r.size} B。`:r.reason;$('takeaway').textContent=r.ok?'请只使用请求范围内的有效载荷；对齐填充不属于可用容量。':'模拟器保留原布局；真实 C 程序应在 NULL 分支处理失败。';paint();};
$('release').onclick=()=>{const id=$('allocation').value;if(!id)return;allocator.release(id);$('operation').textContent=`free(${id});\n${id} = NULL;`;$('narration').textContent=`${id} 已释放，相邻的空闲块已合并。`;$('takeaway').textContent='不能再通过旧指针访问这个对象。';paint();};
$('fragment').onclick=()=>{allocator=new Allocator();for(let i=1;i<=5;i++)perform(allocator,scenes[i].action);$('bytes').value=72;$('operation').textContent='下一步：malloc(72);';$('narration').textContent='空闲总量 96 B，最大空闲块 64 B。点击 malloc 观察失败，再释放 B 后重试。';$('takeaway').textContent='需要 80 B 连续块；96 B 的空闲总量无法跨过存活的 B 拼接。';paint();};
$('clear').onclick=()=>switchMode('lab');
document.addEventListener('visibilitychange',()=>{if(document.hidden)stop();});
renderStory();
