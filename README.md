# Jinghu 的可复用 Skills

这个仓库存放可分享、可安装的 Agent Skills。每个 Skill 都是独立目录，可以按需复制到 Codex、Claude Code 或其他兼容 Agents Skills 的运行环境。

## Skills

### Ian 本人怪诞正文配图

为中文文章生成 16:9 纯白手绘正文配图。默认使用已确认的 Ian 本人卡通 IP：短黑发、黑色圆领、冷静认真，人物必须参与画面的核心动作。包含固定人物设定稿、14 张示例图、构图规则、生图提示词和质检清单。

- 入口：[`ian-xiaohei-illustrations/SKILL.md`](ian-xiaohei-illustrations/SKILL.md)
- 人物规范：[`ian-xiaohei-illustrations/references/ian-persona-ip.md`](ian-xiaohei-illustrations/references/ian-persona-ip.md)
- 依赖：支持参考图片输入的图像生成工具；在 Codex 中默认使用内置 `image_gen`
- 隐私：仓库包含已确认的卡通人物设定稿，不包含真人原始照片

调用示例：

```text
使用 $ian-xiaohei-illustrations，为这篇中文文章设计并生成 4 张怪诞手绘正文配图。
```

### 音频视频制作

接收匹配的音频文件和 SRT 字幕，完成短视频分镜、素材规划、制作与交付验收。

- 入口：[`audio-video-production/SKILL.md`](audio-video-production/SKILL.md)
- 默认规格：16:9、720P、30fps、H.264/AAC
- 音频作为时长基准，SRT 用于语义定位，默认不烧录字幕

调用示例：

```text
使用 $audio-video-production，根据这份音频和 SRT 制作视频。
```

## 安装

先克隆仓库：

```bash
git clone https://github.com/jinghuIluo/jing.git
cd jing
```

安装单个 Skill 到 Codex：

```bash
cp -R ian-xiaohei-illustrations ~/.codex/skills/
```

安装到 Claude Code：

```bash
cp -R ian-xiaohei-illustrations ~/.claude/skills/
```

安装到支持通用 Agents Skills 目录的运行环境：

```bash
cp -R ian-xiaohei-illustrations ~/.agents/skills/
```

安装完成后，在新对话中使用 `$ian-xiaohei-illustrations` 调用。不同平台的图像工具接口可能不同；如果没有兼容的参考图生成功能，可直接复用 Skill 中的提示词模板和人物设定稿。
