/* 教学模型：128 B 固定池、8 B 模型头部、8 B 对齐；不是 libc 实现。 */
(function (root) {
  'use strict';
  class Allocator {
    constructor() { this.blocks = [{start:0,size:128,id:null,requested:0}]; this.serial=0; }
    allocate(bytes, label) {
      if (!Number.isSafeInteger(bytes) || bytes < 1 || bytes > 120) return {ok:false, reason:'请输入 1 至 120 的整数。'};
      const need = Math.ceil(bytes / 8) * 8 + 8;
      const i = this.blocks.findIndex(b => b.id === null && b.size >= need);
      if (i < 0) return {ok:false, reason:`需要连续 ${need} B（含模型头部与对齐），最大空闲块只有 ${this.stats().largest} B。`};
      const b = this.blocks[i];
      const id = label || `P${++this.serial}`;
      if (this.blocks.some(b => b.id === id)) return {ok:false,reason:'分配标识已存在。'};
      // 不留下无法容纳头部及最小有效载荷的碎片。
      const used = b.size - need >= 16 ? need : b.size;
      const allocated = {start:b.start,size:used,id,requested:bytes};
      const pieces = [allocated];
      if (used < b.size) pieces.push({start:b.start+used,size:b.size-used,id:null,requested:0});
      this.blocks.splice(i,1,...pieces);
      return {ok:true,id,ptr:b.start+8,size:used};
    }
    release(id) {
      const block = this.blocks.find(b => b.id === id && id !== null);
      if (!block) return {ok:false,reason:'该标识没有存活的分配；模拟器拒绝无效释放。'};
      block.id=null; block.requested=0;
      for (let i=0;i<this.blocks.length-1;) {
        const a=this.blocks[i], b=this.blocks[i+1];
        if(a.id===null && b.id===null) { a.size+=b.size; this.blocks.splice(i+1,1); } else i++;
      }
      return {ok:true};
    }
    stats() {
      const free=this.blocks.filter(b=>b.id===null), live=this.blocks.filter(b=>b.id!==null);
      return {free:free.reduce((s,b)=>s+b.size,0),largest:Math.max(0,...free.map(b=>b.size)),payload:live.reduce((s,b)=>s+b.requested,0),overhead:live.reduce((s,b)=>s+b.size-b.requested,0)};
    }
  }
  if(typeof module !== 'undefined' && module.exports) module.exports=Allocator;
  else root.Allocator=Allocator;
})(typeof globalThis !== 'undefined' ? globalThis : this);
