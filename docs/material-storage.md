# 仓库与素材保存边界

Git 保存两个 Skill、程序、依赖、测试、制作规范、必要角色参考和上游校准图。`examples/minimal-video/` 只演示清单结构，复用内置角色图，不代表最终分镜或确认成片。README 与 Skill 共用校准图，不再复制一套展示图片。

每期脚本、账本、来源、分镜、生成图、确认记录、音频、字幕和成片保存在独立目录，不提交到 Git。原 macOS 制作机的位置为：

```text
/Volumes/MachineU1/github_work/ian-xiaohei-video-projects/
  examples/video/laundromat/
  examples/video/laundromat-v2/
  examples/video/laundromat-dense-pilot/
  examples/video/laundromat-dense-pilot-v2/
  examples/video/song-pawnshop/
  outputs/
  branch-archives/
```

原仓库的 `examples/video` 和 `outputs` 是指向素材目录的本地软链接，已被忽略；它们不随 clone 分发。这样旧作者脚本与绝对路径时间轴仍能使用。换电脑时恢复完整素材目录，再按需建立这两个链接，或在命令中显式传入外部清单及输出目录。保留 examples/video 与 outputs 的相对层级，避免旧清单和时间轴失效。

新一期继续放在素材目录的 examples/video 下，输出放在同一素材根目录的 outputs 下。不要把每期材料放进最小示例目录。

合并 `codex/illustrated-video-pilot` 时，两套密集试片的源文件已补存到上述目录，并逐文件与分支核对。原分支的历史交接说明与素材哈希清单保存在 `branch-archives/illustrated-video-pilot-11e9667/`；其中关于分支、推送和存储位置的描述只代表当时状态。当前制作规则以仓库文档为准。

Linux 工作区使用 `/srv/projects/ian-xiaohei-video-projects/` 作为独立素材根目录，保留相同的 `examples/video/` 与 `outputs/` 层级；`models/` 保存共享识别模型，`checks/` 保存环境验证材料。旧 Mac 上的确认成片、配音和时间轴尚未迁入此目录。新一期可以直接使用该目录，精确复刻旧版需要先恢复原始素材。

素材目录需要单独备份到其他设备或存储服务；移出仓库本身不是备份。至少保存源稿、图片、原始 TTS 缓存、旁白、字幕、时间轴、确认记录和已确认 MP4。模型与中间渲染缓存可以重建。
