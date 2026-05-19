# 视频产线

## 定位

视频产线是独立于热点锐评的第二条内容产线，主要服务低成本 AI 生成视频的创意和提示词资产包。

它不应复用“热搜候选池”的产品逻辑。

核心不是自动生成视频，而是生成可供人工筛选和投喂视频工具的创意、脚本、分镜和提示词。

## 推荐工作流

```text
选择账号 / 栏目 / 题材方向 / 表达风格
-> AI 生成 10 个视频创意
-> 人工选择 1-3 个
-> 生成脚本文案 + 分镜稿 + 视频提示词包
-> 人工修改
-> 标记为可制作 / 已制作 / 废弃
```

## 推荐模型

- `CreativeIdeaPool`
- `CreativeIdea`
- `VideoScriptDraft`
- `VideoPromptPack`

## 推荐状态

- `idea`
- `selected`
- `scripted`
- `prompted`
- `produced`
- `discarded`

## 推荐输出字段

- `video_concept`
- `target_platform`
- `duration_seconds`
- `style`
- `script_copy`
- `shot_list`
- `image_prompts`
- `video_prompts`
- `negative_prompts`
- `caption`
- `title_options`
- `cover_text`
- `risk_notes`
- `production_notes`

## 边界

- 不自动发布视频。
- 不自动批量搬运素材。
- 不生成仿冒真人、侵犯肖像或误导性真实事件视频。
- 对新闻、公共事件、真人相关内容必须保留事实核验和人工审核。

## 优先级

当前建议优先级 P6。先完成热点候选池、综合池分发、知识库和多平台 Provider，再进入实现。
