# 语音视频制作

这是一个 Codex Skill：接收匹配的音频文件和 SRT 字幕，自动完成短视频分镜、素材规划、视频制作与交付验收。

## 主要能力

- 检查音频、SRT 时长、时间轴重叠和空字幕等异常
- 根据字幕语义自动拆分视觉节拍与分镜
- 默认制作 16:9、720P、30fps、H.264/AAC 视频
- 默认不烧录字幕，保留原始 SRT
- 避免可见网格、时间线、倒计时和进度条等模板化画面
- 验证分辨率、编码、音轨、字幕轨、时长与动态画面
- 输出制作工程、分镜、来源记录、任务清单和验收报告

## 安装

```bash
git clone https://github.com/jinghuIluo/jing.git
cp -R jing/audio-video-production ~/.codex/skills/
```

## 调用

向 Codex 提供匹配的音频和 SRT，然后输入：

```text
使用 $audio-video-production，根据这份音频和 SRT 制作视频。
```

Skill 入口位于 [`audio-video-production/SKILL.md`](audio-video-production/SKILL.md)。
