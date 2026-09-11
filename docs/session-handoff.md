# 视频改版交接摘要

更新：2026-09-11。上下文已发生一次系统压缩，当前最新修订为画风统一试片 v2 的精简标注版。

## 最新目标与反馈

用户要求比较我们的洗烘店视频与 `/Volumes/MachineU1/chrome_downloads/The Economics of Owning a Cafe.mp4`，随后同意增加配图、减少柯基出镜、优化 Skill，并先做试片看效果。

用户认可第一版密集试片的衔接，但指出中途凸显柯基突兀，进一步明确“主要是风格也不相同，反正需要调整一下感觉”。已制作画风统一修订版。用户最新要求删除约 54 秒“客流 · 成交价 · 房租”和全片左上角“社区店 · 演示假设”；本轮只删除这两处叠加文字，不能把这条反馈当成整片验收。

## 当前修订

- 最新成片：`outputs/laundromat-dense-pilot-v2-clean/short/video.mp4`。
- 上一带标注版本与左右对比保留在 `outputs/laundromat-dense-pilot-v2/`；该对比片右侧仍是删除文字之前的版本。
- 源文件：`examples/video/laundromat-dense-pilot-v2/`，含 `author.py`、`short.json`、`storyboard.md`、`generation-record.json`、`audio-reuse.json`、`trial-status.json`、账本与来源。
- 12 张最终插画统一使用新 `images/empty.png` 作为画风参考，暖白/灰绿/橙色、简化轮廓与阴影、同一设备造型。7 张程序数据图解保留比例，背景改暖白。
- 原四个大半身人物镜头改成衣篮/笔记本和账本/计算器静物。保留使用机器与清洁的两个人物镜头，共 4.7 秒。23 镜、19 个最终素材文件；12 个最终生成素材，内置 image_gen 共 13 次调用（其中清洁图缩小人物修正一次），初稿另存 `revisions/cleaning-initial.png`。
- 保留上一版全部切点、同一原配音、字幕与账本。60.0667 秒、1802 帧、30 fps、1080p。没有重写口播或再次调用 TTS。
- 已核对原 WAV、字幕、来源与账本相同；两版 MP4 解码音频相同；全片解码、画面覆盖、切点逐帧对应、单镜静止抽样通过。逐镜中点目检后，把清洁镜头的人工说明移离长椅；修正最终帧已放大检查。结构检查与配图 Skill 验证通过。未做新的主观音频试听。
- 各版成片 SHA256 在对应输出目录的 `short/verification.json`；最新源目录的 `trial-status.json` 对应精简标注版。
- 配图 Skill 已补充共同画风参考、角色身份与本片画风的分工、人物在场景中行动、连看前后镜头检查突兀。资料见 `docs/dense-video-pilot.md` 与 `ian-xiaohei-illustrations/references/dense-illustrated-video.md`。

## 历史版本与提交

- 当前分支：`codex/illustrated-video-pilot`。
- `5f02835`：此前洗烘店确认版规则、程序和源素材。
- `660e5e7`：第一版密集插画 Skill、全屏布局、明确切点及 60 秒试片。
- 以上均为本地提交，未 push；本次修订的提交以 `git log` 为准。
- 原确认短/长片：`outputs/laundromat-v2/short/video-fixed.mp4`、`outputs/laundromat-v2/long/video-fixed.mp4`。
- 第一版密集试片：`outputs/laundromat-dense-pilot/short/video.mp4`。其 `trial-status.json` 已记录用户的衔接认可与画风修订要求。
- 原默认参考仍是 `examples/video/laundromat-v2/approved-baseline.json` 的 `corgi-narrated-static-v1`；新方案 `dense-illustrated-static-v1` 仍是试验方案。
- 参考片分析：`outputs/cafe-reference-analysis/analysis.md`。参考片约 24:20、约 501 个自动检测画面段落、平均 2.9 秒；旧长片约 9:57、72 镜、30 张独立图、平均 8.3 秒。自动画面段落数不是独立图片数。

## 复现与约束

运行 `.venv/bin/python examples/video/laundromat-dense-pilot-v2/author.py`，再运行 `.venv/bin/python scripts/episode_video.py render --editions short --output outputs/laundromat-dense-pilot-v2-clean`。原确认版音频必须保留。合成器已有关闭角标的能力，无须改合成程序：源清单 `disclosure` 为空字符串，S09-2 的 `labels` 为空数组。旧输出目录中的 `verify_revision.py` 绑定旧版路径，不能直接用来声称检查了最新版本。

`scripts/episode_video.py` 的 `full` 布局按整屏静态插图叠加可编辑文字；`at_seconds` 是本段音频的实测切点。当前修订没有修改合成器或对齐程序，此前合成器的 22 项测试已通过，本轮运行的是素材/清单/音视频实物检查。

保留柯基身份、简体字幕、可复算账本与来源。经营金额为演示假设；新一期不可继承旧金额、固定语速或旧音频裁剪点。人物比例由叙事决定，不机械套三分之一或本次两镜比例。

所有生成图使用内置 image_gen，项目素材复制进本期目录。生成结果只输出 output_hint 并用 generatedImage 展示，禁止把含 image_url 的完整结果经 text 输出，避免巨量 base64 消耗上下文。

维护 Skill 后运行 `scripts/quick_validate.py`；修改合成或对齐程序后运行相关测试。测试或模型目检通过不能代替用户验收。`outputs/` 被 Git 忽略，Git 保存源图和内容文件，完整恢复仍需本地音频与成片。
