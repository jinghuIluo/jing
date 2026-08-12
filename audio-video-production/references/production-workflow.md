# 生产流程与防错规则

## 1. 任务清单

每次创建全新任务目录，不复用上个选题的素材或事实。最小 `job-manifest.json`：

```json
{
  "inputs": {"audio_path": "", "audio_sha256": "", "srt_path": "", "srt_sha256": ""},
  "output_spec": {"platform": "视频号", "width": 1280, "height": 720, "fps": 30, "video_codec": "h264", "audio_codec": "aac"},
  "quality_profile": "standard",
  "safe_area_ratio": 0.16,
  "renderer": null,
  "runtime_preflight": null,
  "font_strategy": null,
  "template_match": null,
  "shot_plan": null,
  "stages": {"input_checked": false, "storyboard_ready": false, "assets_ready": false, "project_validated": false, "rendered": false, "visually_reviewed": false, "approved": false},
  "assets": [],
  "motion_windows": [],
  "render_versions": [],
  "approved_output": null,
  "manual_review": null,
  "preview_confirmation_required": false
}
```

每完成一个阶段即更新清单。恢复任务时先核对输入哈希；哈希变化时重新分析时间轴。批准版使用不可变 `approved-vNN.mp4`；`approved.mp4` 只在明确需要时更新为别名。

## 2. 输入、模板与镜头计划

运行 `scripts/analyze_inputs.py`。暂停或修复：音频无法解码、SRT 为空/倒序/重叠、说话人格式异常、SRT 明显超出音频。

先写 `DESIGN.md`、`template-match.md` 和 `shot-plan.json`，再建立分镜表：

| 时间 | 语义功能 | 观众问题 | 视觉目的 | 素材类型 | 搜索词 | 来源 | 状态 |
|---|---|---|---|---|---|---|---|

模板匹配必须写出选用模板、禁用元素与拒绝的视觉方向。`shot-plan.json` 的视频镜头必须声明时间线与源素材入/出点；运行 `scripts/validate_production_plan.py` 后才能将 `assets_ready` 标为 true。字段见 [runtime-and-review.md](runtime-and-review.md)。

## 3. 事实与素材

把准备上屏的数字和具体声明分类为：已核验事实、合理推断、个人观点。只有已核验事实可以成为强化数据卡；找不到依据时保留口播原观点，但不额外伪装成权威数字。

素材优先：官方/机构、许可清晰图库、必要新闻引用。仅在语义需要时使用照片；不要为了满足形式塞入无关图片。下载后验证文件类型、尺寸、时长和可解码性，记录来源页、直接地址、访问日期、用途、许可和 SHA-256。

视频优先 1080P、最低 720P。进入最终渲染器前统一固定帧率、关键帧最大间隔约 1 秒：

```bash
ffmpeg -i input.mp4 -c:v libx264 -r 30 -g 30 -keyint_min 30 -sc_threshold 0 -pix_fmt yuv420p -movflags +faststart -an output.mp4
```

禁止让时间线视频长于源窗口。需要冻结、循环或替换时，写成新的镜头决策，不得静默延长。

## 4. 渲染器与预检

用户指定或已有工程决定最终渲染器；没有约束时优先 HyperFrames。模板参考、局部试验与最终渲染器要明确区分。运行：

```bash
python3 scripts/preflight_runtime.py --renderer <hyperframes|remotion> --report <project>/analysis/runtime-preflight.json
```

使用本机浏览器路径或 `PRODUCER_HEADLESS_SHELL_PATH`，不要依赖渲染时自动下载 Chrome。先完成短 smoke render，再根据可用内存设置全片并发。

### HyperFrames

读取当前 HyperFrames 主 Skill 和 CLI Skill。对话音频为独立全片轨；SRT 不作为可见字幕节点；计时视频是主画布直接子元素、唯一稳定 ID、静音且不被静态背景遮住。运行 `lint`、`validate`、`inspect`，零错误后再渲染。

### Remotion

读取当前 Remotion 创建、渲染、媒体与字幕 Skill。音频为独立全片轨；公开素材只从 `public/` 读取；先执行 composition/build 与 smoke render。不要以编译通过代替正式渲染验证。

## 5. 预览、版本与验收

用户要求预览确认时，先渲染预览、等待确认；未要求则直接正式渲染。渲染失败时保留上个合格版本，不删除输入、来源、工程、SRT 或旧成片。

渲染为新的 `final-vNN.mp4` 后先运行技术验收。`motion_windows` 必须以源素材与成片同一区域的不同帧验证真实运动，不能用文字动画冒充视频运动。

技术工具无法可靠确认无烧录字幕、安全区、背景文字、语义、转场、首尾完整性。制作关键帧联系表并实际查看，然后填写 `delivery/review.json`：

```bash
python3 scripts/verify_delivery.py --video <video> --source-audio <audio> --manifest <manifest> --review <project>/delivery/review.json --report <report>
```

这条命令通过前不得批准。通过后创建 `approved-vNN.mp4`，更新清单路径、哈希和技术报告；需要时再更新 `approved.mp4` 别名。

## 6. 暂停确认

仅在收费服务、用户明确要求预览、音频与 SRT 疑似不同版本、输出规格会造成明显返工、或缺失关键素材会改变表达方向时暂停。缺少视觉风格不构成暂停条件；选择视觉身份后写入 `DESIGN.md` 并继续。
