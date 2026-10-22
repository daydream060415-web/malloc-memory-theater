# 参考资料与适用范围

查阅日期：2026-10-22。内容采用自主归纳，不将教学模型当作标准规定。

1. Dennis M. Ritchie. *The Development of the C Language*, 1993. https://cm-bell-labs.github.io/who/dmr/chist.html 。用于 C/Unix 背景与 ANSI C 标准化脉络；不据此断言 malloc 的首次出现年份。
2. ISO/IEC JTC1/SC22/WG14. *N1570 Committee Draft*, 2011，§7.22.3、§7.22.3.3-5。https://www.open-std.org/jtc1/sc22/wg14/www/docs/n1570.pdf 。这是公开的 C11 委员会草案，并非最新标准全文；用于基本 API 合约。本作品不依赖零大小 realloc 的跨版本差异。
3. Doug Lea. *A Memory Allocator*. https://gee.cs.oswego.edu/dl/html/malloc.html 。用于 1987 年起的 dlmalloc 背景、时间与空间折中及相邻空闲块合并思想；原文说明内容属于历史设计，不能代表当前完整实现。
4. GNU C Library 2.35 Manual. *The GNU Allocator*. https://www.gnu.org/software/libc/manual/2.35/html_node/The-GNU-Allocator.html 。用于 dlmalloc/ptmalloc 衍生关系、arena、mmap 等 GNU 实现特征，不能推广为 C 标准要求。
5. Google. *TCMalloc Design*. https://google.github.io/tcmalloc/design.html 。用于按线程/CPU 缓存、大小类别和分层设计的现代实例；具体模式随构建与平台变化。

## 必须区分的三个层次

- C 接口：字节数、返回指针、失败处理、生命周期。
- 分配器实现：缓存、空闲块组织、元数据、合并策略。
- 操作系统：虚拟地址、页映射和系统内存供给。

动画只模拟第二层的一个固定池模型。对齐/头部大小均为教学参数；本模型中的固定容量失败不能用于预测真实 malloc 失败。
