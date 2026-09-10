# 单镜提示词与编辑

提示词中的空位应按当前分镜填写；不要把所有可选规则机械拼入每张图。

## 内容配图模板

```text
Generate one standalone illustration for a Chinese narrated explainer.

Reference roles:
{Identify each supplied image as character reference, style reference, composition reference or edit target.}
Preserve the selected character's identity and the selected linework.
The reference's props, text, pose and scene are not part of its identity.
{If no character appears in this shot, omit the character reference and identity instructions.}

Visual style and framing:
{Current style, palette, aspect ratio and shot size.}
{Subtitle-safe area if this is a video frame.}

Narration and one core idea:
{The corresponding spoken line and the one idea this image explains.}

Scene and action:
{Current character if present, main objects, pose, gaze and relationships.}

Explanatory callouts:
{For each necessary callout: exact Chinese label, target object and part, leader endpoint, placement and color.}
Keep each label connected to one clear target.
Keep leader lines short and separate from directional flow arrows.
Do not cross the face, key action or other labels.

Flow arrows:
{Only if required: source, destination and what actually flows.}

Text to render verbatim:
{Exact short labels or user-approved figures; otherwise no text.}

Post-production text:
{Text or numerical claims to leave out of the generated image, with the space to reserve.}

Keep the main action readable at video scale. No unrequested titles, watermarks or decorative arrows.
```

柯基的身份与参考图从 [角色档案](characters/corgi-minimal.md) 读取，不在通用模板里硬编码身体或道具。标注的颜色与类别见 [annotations.md](annotations.md)。

## 引线编辑示例

```text
Edit the provided image. Change only the leader line belonging to “{label}”.
Its endpoint must touch the edge of {target object and part}, not the character's sleeve or an adjacent object.
Preserve the exact label, character identity, facial expression, clothing, props, composition, line style and other annotations.
```

## 替换主角

明确原图是编辑目标，新图是角色参考。保留核心动作、道具关系、文字与构图，只替换指定角色，并按其身体结构调整持握动作。换主角不自动换整幅画风，除非用户同时要求。

## 去掉多余标题

仅删除用户指定的文字和对应下划线，以相同白底补齐区域；保留角色、必要标注、引线、画幅和主体位置。
