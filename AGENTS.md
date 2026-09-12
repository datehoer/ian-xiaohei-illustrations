# 项目任务约定

## 口播视频

用户要求制作经营经济学口播视频时，先读取 `economics-of-owning/SKILL.md` 和 `ian-xiaohei-illustrations/SKILL.md`，再按其任务路由读取需要的参考。只改代码、分析项目或只做单图时，不启动完整视频制作。

用户说“沿用上一期”“同款复刻”而未指定其他版本时，本项目的默认参考是 2026-09-11 用户认可的洗烘店修正版，方案为 `corgi-narrated-static-v1`。详细制作规则在 `ian-xiaohei-illustrations/references/video-production.md`，新一期操作与保存范围在 `docs/video-replication.md`。

每期使用独立内容及输出目录。每期材料保存在仓库外的独立素材目录，见 `docs/material-storage.md`。确认版的记录在素材目录的 `examples/video/laundromat-v2/approved-baseline.json`；它的经营数字是演示假设。继承风格与制作方法时，重新核查本期数据，不继承旧音频的裁剪点、固定语速或时间轴。

维护 Skill 后运行仓库结构检查；修改合成或对齐程序时运行相关测试。成片验收与用户反馈另行记录，测试通过不等于用户已认可新视频。

正式视频按用户偏好省略测试页眉、运行验证角标和固定的“经营金额为演示假设”等说明；默认只显示内容标题、图示、必要数据和口播字幕。具体上屏字段遵循配图 Skill 的视频制作参考。

## 本地运行与检索

使用 `uv sync --locked` 和 `uv run --locked` 管理本仓库独立的 `.venv`，不使用 Telegram 网关的 Python 环境。配音和检索命令通过 `uv run --locked --env-file .env` 加载本地配置；不打印 `.env` 或令牌。

资料检索默认调用 `scripts/grok_research.py`，使用本地 `XAI_API_KEY` 和用户指定的 `grok-chat-fast`。保存联网搜索记录与来源线索，再打开原始发布页面核验；不把模型返回直接当成最终数据。MiMo 配音使用本地 `MIMO_API_KEY`。配置优先级、字体与共享 Whisper 模型见 `docs/runtime-setup.md`。
