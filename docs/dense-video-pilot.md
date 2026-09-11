# 密集插画视觉试片

本次试验沿用洗烘店短版的原稿、账本、旁白和字幕，仅改变图片、版式和切镜。60.07 秒、23 镜，使用 12 张内置 image_gen 新插画与 7 张程序绘制的数据图解；其中 6 镜有人物，17 镜无人物。主角与顾客合并计入人物镜头。一个盈亏平衡图分为两次信息揭示，其余有意复用均在镜头表中记录。

第一版已收到用户反馈：衔接不错，但中途突出的柯基很突兀，而且人物与其他画面的风格不一致。整体仍未验收。原来的 `corgi-narrated-static-v1` 和 `approved-baseline.json` 保持不变。

## 画风统一修订

修订源文件在 `examples/video/laundromat-dense-pilot-v2/`，输出在 `outputs/laundromat-dense-pilot-v2/`。沿用第一版的 23 个切点、原配音、字幕和账本。12 张插画使用同一店内画风参考，统一设备造型、暖白/灰绿/橙色、简化轮廓与阴影；7 张程序图解沿用原有准确比例，背景调整到本片暖白色。

开场与假设边界改为衣篮、笔记本，利润与结尾改为账目静物，去掉四个大幅主持人式人物镜头。只在使用机器和清洁场景保留人物，共 2 镜、4.7 秒。这个比例是本次内容的结果，不作为后续视频配额。原始生成图和针对人物大小的修正记录保存在 `generation-record.json`。

复现修订版：

```bash
.venv/bin/python examples/video/laundromat-dense-pilot-v2/author.py
.venv/bin/python scripts/episode_video.py render --editions short --output outputs/laundromat-dense-pilot-v2
```

成片 `short/video.mp4` 和与上一试片的 `comparison.mp4` 另存。修订版仍待用户判断效果，不能因技术检查通过就替代旧确认版。

## 查看和复现

- 新试片：`outputs/laundromat-dense-pilot/short/video.mp4`。
- 同步对比：`outputs/laundromat-dense-pilot/comparison.mp4`，左为确认版，右为试片，共用一条配音。
- 镜头、稿件、账本、生成提示词和配音来源保存在 `examples/video/laundromat-dense-pilot/`。
- `generation-record.json` 区分独立生成图和程序图解；`audio-reuse.json` 绑定已确认旁白哈希。

在完整素材与旧版 `outputs/laundromat-v2/short/` 仍在时执行：

```bash
.venv/bin/python examples/video/laundromat-dense-pilot/author.py
.venv/bin/python scripts/episode_video.py render --editions short --output outputs/laundromat-dense-pilot
```

`author.py` 重建数据图、镜头清单和视觉试片运行目录，核对旧旁白哈希再复制已确认音频；不调用 TTS。新一期不得沿用这个例子的数字或语音切点。

## 新版布局接口

`layout: "full"` 将图片等比铺满 1920×1080，必要时从中央裁去极少量比例差异。没有固定页眉、章节、脚注带或进度条；假设提示与原稿字幕独立叠加。`labels` 按图片的可读区域放置：

```json
{
  "layout": "full",
  "image": "images/washer.png",
  "at_seconds": 0,
  "heading": "洗衣成交价",
  "labels": [
    {"text": "12 元", "x": 0.22, "y": 0.43, "size": 94, "color": "#CF7135"}
  ]
}
```

`x/y` 为 0—1 的归一化坐标；`anchor` 可为 `mm/lm/rm`，默认中心；`background` 可按需要设为颜色以维持对比度。文字越界会在渲染时失败。`heading` 在该布局中只是镜头描述，不自动显示。

`at_seconds` 是本段实际音频的相对切点。同一段镜头要么全部明确指定，要么全部保留自动分配；明确切点必须从零开始，量化到 30 fps 后严格递增且不超过段落长度。明确切点不再被字幕边界吸附移动。旧布局和默认切镜逻辑保持兼容。

图解与后期文字均可由代码修改，生成插图的原始文件另存。完整成片及音频仍在 Git 忽略的 `outputs/` 中；Git 提交保存规则、程序和内容源文件，恢复成片需要这些输出材料或原旁白。
