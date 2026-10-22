# malloc 讲解视频

成片 `malloc-explained.mp4` 约 **3 分 32 秒**，1920×1080、24 fps，包含普通话合成旁白、画面内中文字幕、原创合成背景音乐。独立 SRT 文件可用于字幕修改。

视频依次讲解运行时需求、历史脉络、调用层次、模型参数、分配与拆分、释放与合并、外部碎片、内部碎片，以及 C API 的正确使用。

## 播放

下载本目录的 MP4 后，用浏览器或常见视频播放器打开。字幕已经合成在视频画面里，不依赖播放器加载外挂字幕。

## 制作内容

- `scenes.json`：逐镜头旁白与字幕脚本。
- `make_voice.py`：使用普通话合成语音生成旁白。
- `render_video.py`：绘制动态画面、生成背景音乐、混音并编码。
- `requirements.txt`：所需 Python 依赖。

背景音乐由合成和弦与拨弦音直接生成，未引用现成歌曲。旁白是合成语音。知识出处见仓库 `docs/references.md`。

## 重建

Windows 环境，需安装微软雅黑和 Consolas 字体。先安装依赖，再运行：

```sh
python -m pip install -r video/requirements.txt
python video/make_voice.py
python video/render_video.py
```

脚本把中间文件写入仓库父目录的 `tmp/video`，把成片写入父目录的 `output/video`。配音生成需要网络，已生成音频会缓存；画面绘制与编码在本地完成。
