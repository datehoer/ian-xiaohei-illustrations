# 多镜头口播视频 v2

本轮已制作中国社区自助洗烘店的短片和长片。内容仍是明确的情景测算；政策及高校资料来自原始发布页面，经营参数没有包装成真实门店数据。

## 内容文件

- [随片资料与来源](../examples/video/laundromat-v2/sources.md)：事实、假设、计算口径和封面备选。
- [可复算账本](../examples/video/laundromat-v2/ledger.json)：基准与客流、价格、烘干比例情景。
- [完整分镜](../examples/video/laundromat-v2/storyboard.md)：短片 13 镜、长片 72 镜。
- [短片口播](../examples/video/laundromat-v2/short-script.md)与[长片口播](../examples/video/laundromat-v2/long-script.md)。
- [内容源文件](../examples/video/laundromat-v2/author.py)：修改后运行，生成 JSON 清单、脚本和分镜。
- [原始配图提示词](../examples/video/laundromat-v2/prompts.json)与[生成及修正记录](../examples/video/laundromat-v2/generation-record.json)。全部使用内置 image_gen；最终选用 30 张独立插图，另保留 3 张被修正版本的原图。

生成图中的设备数量、肢体和技术示意均需要目检。本次修正了设备数量、额外手臂，以及不适合作为经营示意的烘干机剖面。精确数字、中文标题、字幕、来源均由程序后期绘制。

## 与试片程序的区别

新入口为 `scripts/episode_video.py`。`scripts/narrated_video.py` 保留用于 v1 试片。

v2 的旁白以自然段合成，镜头与字幕单独记录。一段话可以切多张插图或数据画面；字幕根据本地识别的词时间戳与已校对稿件匹配，文字始终采用稿件。存在识别差异的字词在邻近时间锚点之间插值，不属于逐字精确强制对齐。

支持场景、左图右数字、全屏账表三种布局。插图在单个镜头内保持静止，按分镜切换；账表对应项目在旁白提到时可突出显示。源码采用明确的缓存指纹，改变视觉后可离线重渲染。

### 字形与画面移动修正

用户指出长片约 02:38 的「口径」字形异常。稿件字符是正确的 U+5F84，但此前加载 `STHeiti Medium.ttc` 时使用了默认索引 0（Heiti TC），导致部分汉字采用繁体地区字形。现在按字体族名选择 SC/CN 字体面（本机 Heiti SC 索引 1），所有标题、数据和字幕共用该选择，缓存指纹也包含字体索引。其他字体集合可通过清单的 `font_index` 显式选择；无法识别简体字体面时停止，避免悄悄使用默认字体面。

原来的轻微推近已移除，保留正常换镜。字幕始终由程序独立绘制后叠加，并非图像模型生成。修正版复用原配音和字幕时间轴，输出另存 `video-fixed.mp4`，旧成片保存在各版本目录的 `before-font-fix/`。

## 运行

需要 Python、FFmpeg/FFprobe、中文字体。首次本地识别还需要下载 Whisper 模型；音频不发送到识别服务。

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-video.txt
python3 examples/video/laundromat-v2/author.py
.venv/bin/python scripts/episode_video.py prepare examples/video/laundromat-v2/short.json examples/video/laundromat-v2/long.json
.venv/bin/python scripts/episode_video.py align --model small
.venv/bin/python scripts/episode_video.py render
```

配音缺少缓存时读取 `MIMO_API_KEY`，否则隐藏输入；密钥不写入项目。`prepare --offline` 在缺少缓存时停止。当前一轮最多 2 个并发 TTS 请求，不自动重试付费请求。

`align` 的 `base` 模型适合试探，但本片最终采用 `small`。不要把整段正确稿件作为识别提示：本轮发现这种方式可能让模型漏掉开头或中间内容。提示仅提供少量中文领域词，正文用于识别后的对齐和审核。

```bash
# 只更新图片、标题或版式
python3 examples/video/laundromat-v2/author.py
.venv/bin/python scripts/episode_video.py render --editions short
```

若改动口播、语速或音频剪辑，依次重新运行 prepare、align、render。配音正文改变会产生新的缓存项；已有音频可复用。语速来自实际时长测量，本片长片参数已锁定，避免局部纠错后整片时间轴无意漂移。

## 配音与核查

本次 TTS 曾在短片 S09 重复读完一遍正文，在长片 L28 完成正文后生成额外语音。根据本地 ASR 时间戳保留完整第一遍和短尾音，剪辑点及对应缓存指纹记录在清单中；原始 WAV 仍保留。音频剪辑指纹不匹配时会停止，避免新音频被套用旧剪辑点。

识别出的阿拉伯数字可能被拆成多个词，或将「筒」识别为同音字。程序合并相邻数字词再对齐，主要金额另作第二次识别核对。识别比对用于定位问题，不能证明每个音节、音色和听感都完美，也不能代替后续人工试听。本轮不声称完成了人工听觉验收。

最终输出位于 `outputs/laundromat-v2/short/` 和 `outputs/laundromat-v2/long/`，分别包含视频、完整旁白、SRT、镜头及字幕时间轴、章节表、媒体信息与识别审核记录。中间渲染文件、模型和音频缓存均在被 Git 忽略的 outputs 下。

验证覆盖单位经济与敏感性、字幕完整性、词时间戳利用、异常语音拦截、镜头覆盖、图片存在性；成片另做解码、媒体参数、时间轴和画面检查。具体结果见输出目录内的 `verification.json`。
