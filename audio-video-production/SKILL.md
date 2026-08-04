---
name: audio-video-production
description: Use when the user provides an audio file and matching SRT and asks to create, storyboard, package, render, or verify an audio-led short video, especially for 视频号, HyperFrames, online image/video sourcing, no burned captions, or a reserved subtitle-safe area.
---

# 语音视频制作

## 核心原则

以音频为唯一总时间基准，以 SRT 作为语义定位，不把字幕烧录进画面。先建立可追溯分镜和本地素材，再制作、渲染和逐项验收；技术检查与视觉检查全部通过后才交付。

**REQUIRED SUB-SKILLS:** Use `hyperframes:hyperframes`, `hyperframes:hyperframes-cli`, and `browser:control-in-app-browser` when available. Do not ask whether to use them. If a required capability is unavailable, state the concrete limitation instead of pretending the work is complete.

## 开始前

确认音频与 SRT 路径。默认采用 `standard` 质量档位、16:9、1280×720、30fps、H.264/AAC；用户明确指定的平台、比例、分辨率、风格或预览门槛优先。

用户未指定视觉风格，或明确让你整体规划时，根据内容类型自动选择视觉身份并继续，不得仅因缺少主色、参考图、Logo或风格名称而暂停询问。

仅在收费服务、明确的预览确认、音频与 SRT 不匹配、或会造成明显返工的规格变化时暂停询问。

## 工作流

1. 创建独立任务目录和 `job-manifest.json`，保存输入路径、哈希、规格、阶段、素材、动态区间和版本。
2. 运行输入分析：

```bash
python3 scripts/analyze_inputs.py --audio <audio> --srt <srt> --output-dir <project>/analysis
```

3. 阅读 `analysis/input-report.json` 和候选分镜，结合完整 SRT 建立宏观章节与微观镜头。遵循 [visual-contract.md](references/visual-contract.md)。
4. 使用浏览器搜索来源明确的官方、图库或公共素材。必须同时规划图片和视频；下载本地并记录来源页、直接地址、访问日期、用途、授权状态和 SHA-256。
5. 将数字信息标记为“已核验事实 / 合理推断 / 个人观点”。只有已核验事实才能制作强化数据卡。
6. 按 [production-workflow.md](references/production-workflow.md) 创建 HyperFrames 工程。计时视频必须是主画布直接子元素、带唯一 ID、静音、固定帧率且不能被静态层遮挡。
7. 运行 HyperFrames `lint`、`validate` 和覆盖章节中点、转场边界的 `inspect`；制作关键帧联系表并逐张查看。
8. 渲染到新的 `final-vNN.mp4`，不得覆盖旧合格版本。运行：

```bash
python3 scripts/verify_delivery.py --video <video> --source-audio <audio> --manifest <manifest> --report <report>
```

9. 技术报告通过后，人工确认：无烧录字幕、底部安全区无关键信息、背景文字不干扰、视频确实运动、无闪帧/空白/异常裁切、开头和结尾完整。通过后再更新 `approved.mp4`。

## 质量档位

- `fast`：减少素材数量和视觉变化，不降低事实、同步、编码与安全区门槛。
- `standard`：默认；实景为主，信息卡为辅，检查全部章节和转场。
- `premium`：更多高分辨率动态素材、更密微观分镜、逐场景视觉复核。

## 完成交付

交付 MP4、独立 SRT、HyperFrames 工程、分镜、`job-manifest.json`、素材来源清单、技术报告和关键帧联系表。任何硬性检查失败、动态素材被遮挡、或视觉检查未完成时，继续修正，不得宣告完成。
