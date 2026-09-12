# 复刻已确认的口播视频

本项目默认方案为 `corgi-narrated-static-v1`。用户于 2026-09-11 认可洗烘店的字体与静态画面修正版。今后“沿用上一期”指这一版，不指最初 41 秒试片或带推近效果的版本。

## 固定什么，每期换什么

固定制作方法：16:9、1080p、30 fps、已选柯基、静态镜头、三种画面布局、独立简体字幕、MiMo 配音及本地语音对齐。完整参数与检查规则放在 [视频制作参考](../ian-xiaohei-illustrations/references/video-production.md)，两个 Skill 负责路由，不重复维护多套参数。

每期替换题材、地区与经营对象、来源、账本、纯口播、分镜和配图。不要继承洗烘店的数值、固定语速、局部音频裁剪、音频指纹或字幕时间。约 10 分钟长片通常安排 60–80 镜、25–35 张独立图；按内容调整，不机械凑数。

## 下次如何调用

在这个项目中可以直接说：

> 沿用已确认的洗烘店修正版，做一期「中国社区咖啡店一年能赚多少」。先核查资料，短片约 1 分钟，详细片约 10 分钟；继续用柯基、静态多镜头和独立简体字幕。没有可靠经营数据的部分明确标为假设，保存可修改的完整源文件。

新任务若未自动加载仓库 Skill，可明确指定本仓库 `economics-of-owning/SKILL.md` 和 `ian-xiaohei-illustrations/SKILL.md`。复制单独的配图 Skill 不会同时安装仓库根目录的视频程序；跨项目使用时保留完整仓库或明确提供其位置。

## 内容清单与命令

每期建立独立目录，例如仓库外的 `../ian-xiaohei-video-projects/examples/video/coffee-shop/`，保存 `short.json`、`long.json`、来源、账本、脚本、分镜、提示词和 `images/`。可参考 [v2 最小清单](../examples/minimal-video/short.json)，长版使用相同结构扩展 blocks。

清单顶层填写 `schema_version: 2`、`edition`、`title`、`tts` 和 `blocks`；`asr_hint` 只填本期少量领域词。正式片默认省略 `series_label`、`disclosure` 和镜头 `note`、`source`；这些可选字段仅在明确需要上屏时填写。`tts` 可指定 voice、style、model、base_url，但不包含 key。每个 block 的 text 是纯口播，shots 记录配图和后期文字。新稿默认省略 `tempo` 和 `audio_edit`，实测后确有需要再设置。

下面命令在本期清单和图片准备好后执行，`coffee-shop` 只是新一期目录示例，不表示已经生成该期内容。依赖安装见 [运行说明](video-v2.md)。

```bash
uv run --locked --env-file .env python scripts/episode_video.py prepare \
  ../ian-xiaohei-video-projects/examples/video/coffee-shop/short.json ../ian-xiaohei-video-projects/examples/video/coffee-shop/long.json \
  --output outputs/coffee-shop
uv run --locked --env-file .env python scripts/episode_video.py align --output outputs/coffee-shop
uv run --locked --env-file .env python scripts/episode_video.py render --output outputs/coffee-shop
```

已经有旁白和字幕时，只改字体、图片、标题或布局，直接运行最后一条。正文或配音变化才重新执行三步。整个制作并非一个命令自动完成事实核查和生图；Skill 组织这些工作，程序负责稳定的音频、字幕和合成。

## 怎样保存，才能以后改得动

| 保存内容 | 当前位置 | 用途 |
|---|---|---|
| 制作规则 | 两个 Skill 及视频制作参考 | 新任务知道要遵循的方式 |
| 合成程序与依赖 | `scripts/`、`requirements-video.txt`、`tests/` | 复用字体选择、静态合成、TTS 与字幕处理 |
| 每期可编辑内容 | 仓库外素材目录的 `examples/video/题材/` | 替换数据、稿件、图片和分镜 |
| 确认版记录 | 本期 `approved-baseline.json` | 用户确认点、文件位置与 SHA-256 指纹 |
| 完整制作材料 | 本期 `outputs/题材/` | 原始 TTS 缓存、旁白、字幕、时间轴、检查记录及成片 |

Git 只保存规则、程序、必要角色参考、校准图与最小示例；每期稿件、图片和确认记录存放于仓库外。详见 [素材管理](material-storage.md)。当前 `outputs/` 被 Git 忽略，提交仓库不会备份成片与配音。完整恢复需要另行备份本期 outputs，至少保留 `audio-cache/`、各版 `audio/`、`narration.wav`、`audio-timeline.json`、`captions.json`、SRT、镜头时间轴、检查记录和已确认 MP4。模型下载与中间渲染缓存可以重建；只备份 MP4 无法重做干净字幕和版式。

新生成的时间轴使用相对于版本目录的 manifest/audio 路径，方便连同完整项目一起移动。旧的绝对路径时间轴也兼容；迁移旧项目时先用本期清单执行 `prepare --offline --output ...` 重建路径，不必重新付费合成。若语音、分段或语速改变，再重新对齐字幕。

当前确认成片为 `outputs/laundromat-v2/short/video-fixed.mp4` 和 `outputs/laundromat-v2/long/video-fixed.mp4`。它们作为确认版保留；后续修改用新的版本文件名。`approved-baseline.json` 只记录该版本的用户认可和文件指纹，不能代替素材备份或保证外部模型重生成完全相同。
