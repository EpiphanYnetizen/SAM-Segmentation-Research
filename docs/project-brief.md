# 原题要求（PDF 原文摘录）

> 本文件只记录课程 PDF 原文，便于和 AI 生成的选题说明区分。以课程 PDF 为准。

## 报名与提交

- 组队：两个班自由组队，建议 2-4 人，不超过 4 人；组队在中期报告后不可更改。
- 截止：10 月 11 日前，项目负责人发组队信息 + 选题信息给对应邮箱。
- 开题：10 月 25 日前，项目负责人发录制视频 + PPT。
- 邮件主题：`深度学习_[姓名1]_[姓名2]_[姓名3]_选题_[No.]`
- 附件名：`开题报告.mp4`、`开题报告.ppt`

## 开题三页

1. 项目题目和组队成员。
2. 数据来源和收集方案。
3. Research Track：拟使用的模型和改进；Demo Track：实时性、工具、UI、完成指标。

## Research Track 硬性要求

- 禁止直接调用 off-the-shelf API（如 DeepSeek-V3、Qwen-VL），除非作为 distillation 教师模型。
- 至少用 SFT / RLHF / OPD / OPSD 之一 fine-tune 模型，通常用 LoRA。
- 自采日常数据用于评估加 5-10 分。

## No.2 Large Visual Model

- 原文问题：`Does Segmentation Anything work on all cases? Read paper.`
- 要求：`Collect your own datasets and identify your own object categories.`
- 示例：食堂打饭时能否把每块肉、每块鱼分隔开。
- Reference：SAM、DINO。

## 待与老师确认

- 视觉模型是否等同于论文里说的 `SFT/RLHF`，LoRA 微调 SAM 的 image encoder / mask decoder 是否满足“至少一种后训练”。
