# 口播视频流水线

多镜头短长片现已使用 v2 流程，见 [多镜头口播视频 v2](video-v2.md)。本页的具体清单和静态布局说明保留为 v1 试片记录。

本项目可以完成「选题与口播稿 → 分镜和柯基配图 → 小米 MiMo 配音 → 字幕和数据层 → MP4」。两个 Skill 负责内容与画面决策；Python 和 FFmpeg 负责可重复的语音调用、时间轴与合成。当前实现是本地制作工具，尚不是托管的一键批量服务。

## 项目检查与修正

已同步远端提交 `dfc7e2a`。新增的 `economics-of-owning` 是本仓库原创口播 Skill，3 个文本文件经静态扫描和人工阅读，无可执行入口、安装钩子或凭据读取行为。扫描器将成本项「软件订阅」误报为推广，人工确认属于财务内容。本轮未修改全局 skills 或 Codex 配置。

| 发现 | 处理 |
|---|---|
| 口播 Skill 指向不存在的 `economics-of-owning-visuals` | 改为现有 `ian-xiaohei-illustrations` |
| 把单位净利润再次扣固定成本 | 改为单位贡献毛利，再扣年度固定成本、折旧和利息 |
| 没有来源时允许写「行业常见区间」 | 改为明确标注假设；正式数字需核实地区、年份与分母 |
| 长片格式不适合几十秒试片 | 用户指定时长优先，试片只取必要环节 |
| Skill 只有文字流程，没有音视频程序 | 新增 TTS 客户端、显式镜头清单与合成器 |

配图 Skill 的默认主角是柯基。它的「独有图数量」与「换画面次数」是两种指标：同一原图可以对应多个逐项揭示的数据画面，长片仍需按规则补充场景与景别，不能用三张试片图撑满十几分钟。

## 已实现的接口

`scripts/mimo_tts.py` 使用用户指定的中转站 `https://api.hotday.uk/v1`，模型 `mimo-v2.5-tts`。经真实请求确认，该 Key 可列出三个 MiMo TTS 模型，也能合成 WAV。默认试片音色为「白桦」。小米官方示例使用 `chat/completions`，风格放 `user`，正文放 `assistant`，读取 `choices[0].message.audio.data`。[小米官方文档](https://mimo.mi.com/docs/zh-CN/quick-start/usage-guide/audio/speech-synthesis-v2.5)

中转站和小米官方是不同服务地址，模型可用性、计费与限制由中转站实际响应决定。客户端允许修改 `--base-url` 或 `MIMO_BASE_URL`，不记录密钥、不输出完整失败响应、不自动跟随重定向或重试计费请求。

```bash
python3 scripts/mimo_tts.py --list-models
python3 scripts/mimo_tts.py --text narration.txt --output outputs/narration.wav
```

没有 `MIMO_API_KEY` 时会出现隐藏输入提示。实际 Key 不放进 Git；`.env`、音频缓存及合成输出已被忽略。

## 运行视频示例

运行环境：Python 3.10+、Pillow 10–12、带 `libx264` 的 FFmpeg / FFprobe、中文字体。安装 Python 依赖可使用本地虚拟环境：

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-video.txt
.venv/bin/python scripts/narrated_video.py examples/minimal-video/manifest.json --output outputs/laundromat-pilot
```

Codex 桌面版的 bundled Python 已包含 Pillow，本次制作使用了它，无需另装依赖。macOS 自动寻找 STHeiti，Linux 自动寻找 Noto Sans CJK；其他位置可通过 `VIDEO_FONT` 指定。

只修改图片或版式、不重新付费生成语音：

```bash
python3 scripts/narrated_video.py examples/minimal-video/manifest.json --output outputs/laundromat-pilot --offline
```

缓存指纹包含正文、音色、模型、风格和服务地址。任何一个发生变化都会需要新音频；`--offline` 在缓存缺失时停止，不会偷偷调用接口。

## 清单与交付

[示例清单](../examples/minimal-video/manifest.json) 按字幕/数据揭示节点组织 `segments`，每段明确对应图片，图片路径相对清单所在目录。

| 字段 | 用途 |
|---|---|
| `text` | 发往 TTS 的纯口播；不含分镜标签 |
| `subtitle` | 屏幕字幕，可将口语数字格式化；省略时使用正文 |
| `image` | 已生成的独立原图或明确复用原图 |
| `heading` / `eyebrow` | 镜头标题与数据口径 |
| `metric` / `detail` | 单个重点数字或结论 |
| `rows` | 数据明细，最多 7 行，含 label/value/可选 accent |
| `note` | 金额口径、来源或假设说明 |

程序每段生成一份音频，从 WAV 样本数得到真实时长，并在视频帧边界补不足一帧的静音。它不会按字数估算时间，也不提供逐字高亮。旁白重采样为 48kHz mono PCM16 后连续拼接；最终只编码一次 AAC，并做响度归一化。

本机 FFmpeg 未包含字幕绘制滤镜，因此使用 Pillow 生成透明文字层，再由 FFmpeg 叠加到视频。原始插图单独保留。当前版式为 16:9、左图右账本，字幕位于底部；竖版需要重新设计画面与文字位置。

输出目录包含：

- `video.mp4`：H.264 / AAC 成片，含可读中文字幕。
- `narration.wav`：完整配音，响度归一化前。
- `subtitles.srt`：可独立编辑的段级字幕。
- `timeline.json`：每段音频实测时长、起止时间和所用图片。
- `media-info.json`：最终视频与音轨信息。
- `audio-cache/`、`render/`、`picture.mp4`：可复用音频与渲染中间件。

## 洗衣店试片的数字

主题：「一家洗衣店一年到底能赚多少」。本片采用人民币、自助洗烘门店的假设账本，没有声称是真实门店或行业均值；也不代表 `economics-of-owning` 默认的美国市场数据。

单价 20 元 × 每天 50 单 × 每年 360 天 = 营收 360,000 元。

水电耗材 120,000 元，房租 72,000 元，人工 96,000 元，维修杂费 18,000 元，折旧 12,000 元，共 318,000 元。税前利润 42,000 元。人工已经含店主劳动，不能再额外扣一次店主工资；模型不设融资，未计算所得税。税前利润不等于现金流、回本金额或全部店主收入。

客流减少至每天 40 单：营收 288,000 元，水电耗材按订单同比减少到 96,000 元，固定成本及折旧仍是 198,000 元，税前亏损 6,000 元。没有把所有成本都误设为固定成本。

## 正式长片还需要什么

用户确认中国自助洗烘店，并提出更频繁的配图变化及短片加长片形式。接口测试、来源核验和下一版制作建议见 素材档案中的 `laundromat-next-version.md`（保存位置见 [素材管理](material-storage.md)）。该文档中的新版功能仍是待实施方案。

确定地区、门店类型和时长后，补充可核验的价格、房租、人工、设备投资、维修和税费口径，区分自助洗烘、代洗和干洗。先验证年账，再写完整口播和分镜。图像由当前会话中的内置生图工具逐张生成并目检；Python 不会自动调用两个 Skill 来独立写稿或生图。

当前试片采用静态图卡、逐项数据揭示和段级字幕；没有配乐、角色动作动画、逐字对齐或无人值守调度。图像与配音生成的成本以工具及中转站实际计费为准，本次未估算报价。

## 验证

```bash
python3 -m unittest discover -s tests -v
python3 scripts/quick_validate.py .
```

覆盖 MiMo 消息角色、音频解码与真实时长、无效响应保护、缺失图片拦截、SRT 进位和试片账本。实际成片另检查画面、字幕安全区、音视频时长及解码。
