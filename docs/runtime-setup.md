# uv 视频环境与资料检索

完整项目提供资料检索、MiMo 配音、Whisper 字幕对齐和 FFmpeg 合成。两个 Skill 提供写稿与配图流程；内置图像工具由当前 Codex 会话提供，不需要在本项目配置 OpenAI API 密钥。

## 安装环境

在仓库根目录执行：

```bash
uv sync --locked
```

Python 默认使用 `.python-version` 中的 3.12。`pyproject.toml` 是依赖声明，`uv.lock` 固定解析结果，`.venv` 不入 Git。即使外层已激活 Telegram 网关环境，uv 仍使用本项目环境；不要加 `--active`。见 [uv 项目说明](https://docs.astral.sh/uv/guides/projects/)。

Ubuntu/Debian 的系统依赖：

```bash
sudo apt-get install --no-install-recommends ffmpeg fonts-noto-cjk
```

合成器自动查找 Noto Sans CJK 并选择 SC 字体面。其他字体位置可设置 `VIDEO_FONT`，或在清单中指定 `font` 和 `font_index`。需要目检真实字幕，不根据文件名推断字体面。字体来源为 [Noto CJK](https://github.com/notofonts/noto-cjk)，许可证随发行包提供。

兼容 pip 的 `requirements-video.txt` 从锁文件导出，不手工维护第二套依赖：

```bash
uv export --format requirements-txt --no-hashes --no-dev --output-file requirements-video.txt
```

## 配置两个现有令牌

首次安装时复制 `.env.example` 为 `.env`，通过本地编辑器填入令牌并执行 `chmod 600 .env`；不要覆盖已有配置。`.env` 已被 Git 忽略，不随素材归档。

| 环境变量 | 用途 |
|---|---|
| `MIMO_API_KEY` | New API 中用于配音的既有令牌，本机选择名为 `free` 的令牌 |
| `MIMO_BASE_URL` | 兼容 MiMo chat completions 的网关地址，包含 `/v1` |
| `MIMO_MODEL` | 默认 `mimo-v2.5-tts` |
| `XAI_API_KEY` | New API 中用于资料检索的既有 `xai` 令牌 |
| `XAI_BASE_URL` | 支持 Responses 与网页搜索的网关地址，包含 `/v1` |
| `XAI_MODEL` | 用户指定的 `grok-chat-fast`，不自动替换模型 |
| `WHISPER_MODEL` | 可选的本地模型目录；未设置时使用 `small` 并按输出目录缓存 |

`free` 是现有令牌的名字，不代表对所有模型和上游计费作出免费保证。模型可见性与实际调用能力分别验证；不从旧制作记录推断当前接口状态。

uv 不自动读取 `.env`，调用时显式传入 `--env-file`。参见 [uv 环境变量文件](https://docs.astral.sh/uv/configuration/files/#environment-variable-files)。MiMo 的 `tts.base_url`、`tts.model` 清单字段优先于环境变量，环境变量优先于程序默认值；有效地址和模型也参与音频缓存指纹。

```bash
uv run --locked --env-file .env python scripts/mimo_tts.py --list-models
```

上面的命令只列模型。真正配音由 `prepare` 发起；非交互进程缺少密钥会明确退出，不等待隐藏输入。接口失败不自动重试。

## 共享 Whisper 模型

每期素材根目录由本机维护，不入代码仓库。可预下载 small 模型，避免首次正式制作时才下载：

```bash
uv run --locked python -c 'from faster_whisper.utils import download_model; download_model("small", output_dir="../ian-xiaohei-video-projects/models/faster-whisper-small")'
```

确保目标父目录由当前用户拥有。然后在 `.env` 中将 `WHISPER_MODEL` 设为模型目录的绝对路径。程序使用 CPU、int8 和四个识别线程，无需 CUDA。`--model` 可覆盖该环境变量。

## 用 Grok 搜资料

```bash
uv run --locked --env-file .env python scripts/grok_research.py \
  '查找中国社区咖啡店设备价格的原始报价来源，注明日期、含税情况和配置，不给无来源均值。' \
  --output ../ian-xiaohei-video-projects/examples/video/coffee-shop/research-leads.json
```

脚本调用 `/responses`，明确启用 `web_search`，只使用配置中的模型。输出包含回答、来源链接、联网搜索记录和用量。没有完成的搜索记录时不会报告联网成功；已有输出不会被覆盖。协议依据 [xAI Web Search](https://docs.x.ai/developers/tools/web-search)，`grok-chat-fast` 是本机网关实际提供的模型名。

资料文件是线索：继续打开原始链接，记录核验日期、口径和用于口播的具体说法。经营数字仍按 `economics-of-owning` 的规则核查。`max-output-tokens` 限制回答长度，不等于限制搜索次数。

## 制作与验证

```bash
uv run --locked --env-file .env python scripts/episode_video.py prepare ../ian-xiaohei-video-projects/examples/video/coffee-shop/short.json --output ../ian-xiaohei-video-projects/outputs/coffee-shop
uv run --locked --env-file .env python scripts/episode_video.py align --editions short --output ../ian-xiaohei-video-projects/outputs/coffee-shop
uv run --locked --env-file .env python scripts/episode_video.py render --editions short --output ../ian-xiaohei-video-projects/outputs/coffee-shop
uv run --locked python -m unittest discover -s tests -v
uv run --locked python scripts/quick_validate.py .
```

清单需要先写好并配齐图片，上面的题材路径只是使用示例。只改画面时直接离线 `render`；修改口播后重新配音和对齐。将验证结果、音频缓存和本期素材保存在外部素材根目录。旧版确认成片及其原始素材需要从原设备单独恢复，安装环境不会恢复这些文件。
