# Changelog

## Unreleased

- 将每期视频材料与输出移出代码仓库；保留最小清单示例，合并重复展示图片，明确独立备份边界。

- Captured the user-approved static narrated-video workflow in the existing skills, including shared short/long research, independent Simplified Chinese typography, narration checks, and episode source preservation.
- Made video page labels and ASR vocabulary configurable per episode, and new audio timelines portable across project locations; retained compatibility with existing absolute paths.

- Added a minimal-line anthropomorphic corgi as the default character, with an independent identity profile and reference image; preserved Xiaohei as an explicit optional preset.
- Added character-design and content-illustration modes under the existing skill name, with reusable project character assets and narration-based shot planning.
- Added explanatory callouts with explicit target parts, separate flow arrows, source-note guidance, and image QA for annotation endpoints and character consistency.
- Updated agent metadata, prompt examples, installation instructions, and source notices for this fork; bundled license notices with the installable skill.
- Extended structural validation to cover the new references, character PNG, and local Markdown links, including graceful reporting of missing or malformed assets.

- Added video illustration density rules (≈ minutes × 1.5–2 unique images, per-segment minimum quotas, card-type labels, digit-dense sections get one card per row, reuse rules, and a dangling-`[画面]` guard) to `ian-xiaohei-illustrations/SKILL.md`.
- Bundled `economics-of-owning/` as a second installable skill in this repository: an original script-writing companion (Economics of Owning a X format) whose `[画面]` beats render through `ian-xiaohei-illustrations` under the density rules.

- Added `scripts/quick_validate.py` to check skill structure, required references, README image links, example image aspect ratios, changelog presence, and obvious draft markers.
- Added task routing to `ian-xiaohei-illustrations/SKILL.md` so planning, generation, single-image, editing, and example-driven tasks read only the needed references.
- Clarified the README example-image split between the public GitHub gallery and the installed skill calibration assets.

## v1.0.0 - 2026-05-28

- Initial release of Ian Xiaohei Illustrations as a Codex Skill.
- Included the skill entrypoint, OpenAI agent metadata, style references, prompt template, QA checklist, and calibration example images.
