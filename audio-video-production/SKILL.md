---
name: audio-video-production
description: Use when audio plus matching SRT must become a storyboarded, packaged, rendered, or verified short video, especially when visual style, template matching, subtitle-safe layout, HyperFrames, Remotion, source assets, or final delivery checks matter.
---

# 语音视频制作

以音频为唯一时间基准，SRT 只作语义定位，不烧录完整字幕。成片不仅要技术合格，还必须通过模板匹配、素材预算、运行时预检和可追溯视觉复核。

## 强制前置

1. 确认音频/SRT；默认 `standard`、16:9、1280×720、30fps、H.264/AAC。运行 `scripts/analyze_inputs.py`。
2. 建立独立任务目录与 `job-manifest.json`，记录哈希、规格、版本、渲染器、素材、动态区间和阶段。
3. 写 `DESIGN.md`、`template-match.md` 和 `shot-plan.json`。模板匹配必须写明视觉身份、选用模板、禁用元素、素材预算和拒绝理由；执行：

```bash
python3 scripts/validate_production_plan.py --plan <project>/shot-plan.json --profile standard
```

4. 选择一个最终渲染器并记录理由：用户指定或已有工程时沿用；否则优先 HyperFrames。用户指定 Remotion 时使用 Remotion。HyperFrames 可用时必须阅读 `hyperframes:hyperframes` 和 `hyperframes:hyperframes-cli`；使用 Remotion 时必须阅读相应 Remotion Skill。模板参考或部分试验不算作该渲染器已交付。
5. 素材搜索需要外部素材时，使用 `browser:control-in-app-browser`；下载本地、验证可解码并记录来源、直接地址、日期、许可和 SHA-256。先满足素材预算再进入渲染。
6. 运行本地预检，不等待浏览器自动下载：

```bash
python3 scripts/preflight_runtime.py --renderer <hyperframes|remotion> --report <project>/analysis/runtime-preflight.json
```

本机 Chrome 可通过 `PRODUCER_HEADLESS_SHELL_PATH` 指定。先渲染短 smoke clip，再按可用内存确定全片并发；smoke 失败时不得启动全片。

## 生产与验收

- 按 `references/visual-contract.md` 设计宏观章节与微观镜头；按 `references/production-workflow.md` 建工程、素材和版本。
- 每段计时视频必须在 `shot-plan.json` 声明时间线与源素材的入/出点；不得自动循环、冻结或超出源窗口。
- 仅将已核验事实做成强化数据卡。合理推断与个人观点不得伪装为数据事实。
- 最终渲染到新的 `final-vNN.mp4`，保留旧合格版本。
- 技术验收后，生成并填写 `review.json`；未完成全部人工项不可批准：

```bash
python3 scripts/verify_delivery.py --video <video> --source-audio <audio> --manifest <manifest> --review <project>/delivery/review.json --report <report>
```

只有上述命令通过，且关键帧联系表已逐张看过，才生成不可变 `approved-vNN.mp4`；如需要 `approved.mp4`，它只作为指向当前批准版的别名。

## 质量档位

- `fast`：减少镜头，但不降低同步、安全区、事实和验收标准。
- `standard`：至少 3 个独立实景来源、实景时长目标 40% 以上；无法满足时在计划中写明许可或解码例外。
- `premium`：至少 5 个独立实景来源、实景时长目标 60% 以上；逐场景复核。

无烧录字幕、底部安全区、无可见网格、无模板名/时间码是硬约束。具体字段、命令和复核样例见 [runtime-and-review.md](references/runtime-and-review.md)。
