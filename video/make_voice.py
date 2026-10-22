"""为各镜头生成普通话旁白，缓存已有文件以便重复渲染。"""
import sys, asyncio, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'.video-deps'))
import edge_tts
HERE=Path(__file__).parent
OUT=ROOT/'tmp/video/audio';OUT.mkdir(parents=True,exist_ok=True)
async def main():
 scenes=json.loads((HERE/'scenes.json').read_text(encoding='utf-8'))
 for i,s in enumerate(scenes):
  path=OUT/f'{i:02d}.mp3'
  if path.exists() and path.stat().st_size>2000:continue
  await edge_tts.Communicate(s['speech'],'zh-CN-YunxiNeural',rate='+3%',pitch='-1Hz').save(str(path))
  print(f'voice {i+1}/{len(scenes)}',flush=True)
asyncio.run(main())
