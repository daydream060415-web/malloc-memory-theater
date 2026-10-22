const assert=require('node:assert/strict');
const Allocator=require('../allocator.js');
function invariant(a){let end=0;for(let i=0;i<a.blocks.length;i++){const b=a.blocks[i];assert.equal(b.start,end);assert.equal(b.size%8,0);assert.ok(b.size>=16);if(b.id){assert.ok(b.requested<=b.size-8);assert.equal((b.start+8)%8,0);}else if(i)assert.notEqual(a.blocks[i-1].id,null);end+=b.size;}assert.equal(end,128);const s=a.stats();assert.equal(s.free+s.payload+s.overhead,128);}
const a=new Allocator();
for(const id of ['A','B','C'])assert.ok(a.allocate(24,id).ok);
a.release('A');a.release('C');assert.equal(a.stats().free,96);assert.equal(a.stats().largest,64);
const before=JSON.stringify(a.blocks);assert.equal(a.allocate(72,'D').ok,false);assert.equal(JSON.stringify(a.blocks),before);
a.release('B');assert.equal(a.stats().largest,128);assert.ok(a.allocate(72,'D').ok);assert.equal(a.stats().free,48);a.release('D');assert.equal(a.stats().free,128);
assert.equal(a.release('D').ok,false);
for(const n of [0,-1,1.5,121,NaN,Infinity])assert.equal(a.allocate(n).ok,false);
assert.equal(a.allocate(13,'X').size,24);assert.equal(a.stats().overhead,11);assert.equal(a.allocate(13,'X').ok,false);invariant(a);
const exact=new Allocator();assert.equal(exact.allocate(120).size,128);assert.equal(exact.stats().free,0);invariant(exact);
const tail=new Allocator();assert.equal(tail.allocate(112).size,128);invariant(tail);
// 固定种子的压力序列验证地址连续、容量守恒和相邻空闲块合并。
let seed=123456;const random=()=>{seed=(Math.imul(seed,1664525)+1013904223)>>>0;return seed/4294967296;};
const fuzz=new Allocator();for(let i=0;i<5000;i++){const live=fuzz.blocks.filter(b=>b.id);if(live.length&&random()<.5)fuzz.release(live[Math.floor(random()*live.length)].id);else fuzz.allocate(1+Math.floor(random()*120));invariant(fuzz);}
console.log('PASS: fragmentation, alignment, invalid input, coalescing, 5000 invariant operations');
