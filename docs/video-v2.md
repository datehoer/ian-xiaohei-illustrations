# 多镜头口播视频 v2

入口为 `scripts/episode_video.py`。旁白以自然段合成，镜头与字幕单独记录；支持静态场景、左图右数字、全屏账表。字幕使用校对稿件和本地识别时间戳对齐，仍需试听核查。

## 最小运行示例

需要 Python、FFmpeg/FFprobe、中文字体，以及 `requirements-video.txt` 中的依赖。首次识别需要下载 Whisper 模型。

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-video.txt
.venv/bin/python scripts/episode_video.py prepare examples/minimal-video/short.json --output outputs/minimal-video
.venv/bin/python scripts/episode_video.py align --model small --output outputs/minimal-video --editions short
.venv/bin/python scripts/episode_video.py render --output outputs/minimal-video --editions short
```

配音缺少缓存时读取 `MIMO_API_KEY`，否则隐藏输入；密钥不写入项目。配音会调用外部服务。`prepare --offline` 可复用已有缓存，缓存缺失时停止。

只修改图片或版式时重新 render；正文、语速或剪辑变化后重新 prepare、align、render。不要继承旧一期的音频剪辑点或固定语速。字体集合按 SC/CN 字体面选择，可用 `font_index` 显式指定。

每期源材料与成片保存方式见 [素材管理](material-storage.md)，新一期制作流程见 [复刻说明](video-replication.md)。洗烘店的详细制作记录随本地素材档案保存。
