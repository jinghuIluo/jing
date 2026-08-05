# 运行时、镜头计划与人工复核

## 渲染器路由

| 条件 | 最终渲染器 |
|---|---|
| 用户点名 HyperFrames，或已有 HyperFrames 工程 | HyperFrames |
| 用户点名 Remotion，或已有可运行 Remotion 工程 | Remotion |
| 二者都可用、没有项目约束 | HyperFrames |
| 首选引擎 smoke render 失败 | 记录错误后切换另一引擎并重新预检 |

不要把“读取模板参考”写成“使用了该引擎”。最终引擎必须留下 lint/validate 或 composition/build、smoke render 和全片渲染证据。

## `shot-plan.json`

`validate_production_plan.py` 读取以下最小结构。所有 `kind: video` 镜头必须把时间线区间完整映射到源素材区间。

```json
{
  "template_match": {
    "style": "雾瓷绿",
    "selected_templates": ["纪录片式素材穿插", "数据对比卡"],
    "banned_elements": ["可见网格", "完整烧录字幕"]
  },
  "timeline_duration": 202.884,
  "visual_budget": {
    "unique_real_sources": 3,
    "real_footage_seconds": 90
  },
  "scenes": [
    {
      "id": "washer-habit",
      "kind": "video",
      "timeline_start": 120.667,
      "timeline_end": 136,
      "source_path": "assets/washer.mp4",
      "source_start": 4.167,
      "source_end": 19.5
    }
  ]
}
```

当授权、题材或下载错误使预算无法达标时，添加简短 `visual_budget.exception`；不得把没有素材预算的图形卡堆叠称作 `standard`。

## `review.json`

技术工具不能可靠判断下列视觉条件。人工逐张查看联系表后，填写所有值为 `true`：

```json
{
  "approved": true,
  "checks": {
    "no_burned_captions": true,
    "subtitle_safe_area": true,
    "background_text": true,
    "scene_midpoints": true,
    "transition_boundaries": true,
    "opening_and_ending": true,
    "video_motion": true
  }
}
```

联系表至少包括：0.5 秒、3 秒、每章中点、每次转场前后 0.1 秒、大字稳定帧、每段视频两个不同时点、CTA 稳定帧和最后 0.3 秒。把联系表路径和实际抽检时间写入视觉复核说明。

## 运行时

`preflight_runtime.py` 只验证本地二进制可用性。预检通过后，仍要执行所选引擎的 smoke render；并发数由 smoke 的内存表现决定，不以机器核心数推断。显式传入的二进制路径若无效必须失败，不得悄悄回退。
