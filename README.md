# 内存旅馆：malloc 的前世今生

一个可离线运行的 C 语言课堂创意案例，以交互动画解释动态内存分配、释放、拆分、合并与外部碎片。

## 开始演示

点击 GitHub 的 **Code → Download ZIP**，解压后双击 `index.html`。不需要安装依赖或联网。GitHub 文件预览不会直接运行网页。

- **故事放映**：10 幕情节，支持播放、暂停、前后切换和速度调整。
- **自由实验**：自定义 1 至 120 B 请求、释放对象、一键加载碎片案例。
- **前世今生**：简明历史、API 使用原则、原始参考资料。
- 支持窄屏、键盘操作和系统减少动态效果偏好。

## 教学案例

128 B 固定池，A/B/C 分别申请 24 B，各占 32 B。释放 A 和 C 后，空闲总量 96 B，最大连续空闲块 64 B。此时申请 72 B 载荷需要 80 B 连续空间，因外部碎片失败。释放 B、合并空闲块后，同一请求成功。

**模型边界**：首次适配、8 B 头部、8 B 对齐、立即合并；小于 16 B 的尾部不再拆分。地址是模拟偏移。该模型不是 libc 的真实 malloc，也不复现操作系统虚拟内存；真实分配器可能继续申请系统空间，且未必立刻合并。

## 文件

- `index.html`、`style.css`、`app.js`：动画和课堂页面。
- `allocator.js`：独立教学分配模型。
- `examples/dynamic_scores.c`：实际调用 malloc/realloc/free 的安全示例。
- `docs/presentation.md`：约 8 分钟课堂讲稿及问答。
- `docs/references.md`：资料出处与适用范围。
- `tests/allocator.test.cjs`：确定性案例及 5000 次状态不变量检查。

## 验证

```sh
node tests/allocator.test.cjs
cc -std=c11 -Wall -Wextra -Werror -pedantic examples/dynamic_scores.c -o dynamic_scores
./dynamic_scores
```

预期 C 示例输出：`count=5, sum=445, average=89.0`。支持 GCC/Clang 的环境可以增加 `-fsanitize=address,undefined -g` 检查内存错误。

报告单独交付；仓库不保存个人姓名、学号或带个人编号的 PDF。
