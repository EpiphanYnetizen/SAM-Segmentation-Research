# SAM-Segmentation-Research

> 深度学习课程项目 · Research Track No.2 · Large Visual Model
> 核心研究问题：Does Segment Anything work on all cases?

> 第一次看这个仓库的人，先读 [`START_HERE.md`](./START_HERE.md)，用大白话分好“三个人先干什么”。

## 一句话目标

先验证 SAM 在**自采食堂菜品 / 日常物品数据**上的零样本能力与失败边界，再用 LoRA 后训练 SAM（image encoder / mask decoder），并用 mIoU、Dice、边界 F1 对比 `zero-shot vs fine-tuned`，最终产出一个可上传图片的分割演示 UI。

## 目录与角色对应
1

| 目录 | 角色 | 负责内容 |
|---|---|---|
| [`data/`](./data) | 组员 A | 自采原始图、类别定义、Label Studio 标注、COCO/mask 导出、数据集划分 |
| [`evaluation/`](./evaluation) | 组员 A | mIoU / Dice / 边界 F1、零样本 vs 微调对比、失败案例图鉴 |
| [`model/`](./model) | 组员 B + 组长 | B：SAM 加载/推理、image encoder LoRA；组长：mask decoder 微调与消融 |
| [`app/`](./app) | 组长(PM) | Gradio 上传图片 + 点/框提示 + 实时分割展示 |
| [`scripts/`](./scripts) | 组长(PM) | 数据切分、一键评测、报告图表生成 |
| [`docker/`](./docker) | 组长(PM) | 可选：Dockerfile + Compose 起 UI/评测服务 |
| [`docs/`](./docs) | 全员 | 原题解读、数据协议、实验方案、报告草稿、视频脚本 |

## 当前状态

- [x] 目录骨架与分工计划
- [ ] 报名邮件发送（10 月 11 日前）
- [ ] 跑通 SAM zero-shot
- [ ] 自采数据 200 张以上并标注
- [ ] LoRA 微调 + 对比评测
- [ ] 开题 3 页 PPT + 3 分钟视频（10 月 25 日前）

## 关键节点

- `10/11`：发送报名邮件（今天，主题 `深度学习_[姓名1]_[姓名2]_[姓名3]_选题_2`）
- `10/24`：`开题报告.ppt` + `开题报告.mp4` 完成，组长检查附件命名
- `10/25`：发送开题材料（硬截止）
- `10/25` 后：继续 zero-shot、双分支微调、消融与最终报告

## 技术栈

| 层 | 技术 |
|---|---|
| 分割模型 | `segment-anything` / `SAM2`（HuggingFace `transformers` 可选） |
| 辅助特征 | `DINOv2`（对照特征，可选） |
| 微调 | PyTorch + `peft`（LoRA） |
| 标注 | Label Studio / CVAT |
| 评测 | NumPy + `scikit-image`（IoU、Dice、边界 F1 均本仓库实现，减少黑盒） |
| UI | Gradio |
| 部署 | 本地 Python / 可选 Docker Compose |
| GPU | SAM-ViT-B / MobileSAM 优先，单卡 8G 以上 |

## 快速开始

### 1. 环境

```bash
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pip install -r model/requirements.txt -r app/requirements.txt
```

### 2. 数据

原始图放 `data/raw/`，标注导出放 `data/exports/`。类别清单在 `data/categories.yaml`，由组员 A 维护。

```bash
python scripts/split_dataset.py --data-dir data/exports --out data/splits
```

### 3. 零样本评测

```bash
python model/zero_shot_inference.py --checkpoint checkpoints/sam_vit_b_01ec64.pth --data-dir data/splits/val --out outputs/zero_shot
python evaluation/evaluate.py --gt data/splits/val --pred outputs/zero_shot --out outputs/zero_shot_metrics.json
```

### 4. LoRA 微调

```bash
python model/train_lora.py --config model/config/default.yaml
```

### 5. 演示

```bash
gradio app/main.py
```

## 仓库规则

1. 禁止 force push `main`。
2. feature 分支：`feature/<role>-<short-desc>`，例如 `feature/a-label-export`、`feature/b-lora-train`。
3. 每个角色只改自己目录；`docs/` 和根目录由组长统一汇总。
4. 大文件（模型权重、原始图、视频、PDF）不进 git，走 `.gitignore` 或 release。
5. 交付物命名严格按课程要求：`开题报告.mp4`、`开题报告.ppt`。

## 课程要求备份

见 [`docs/project-brief.md`](./docs/project-brief.md)（PDF 原文逐条摘录，不依赖 AI 生成文档）。

## 贡献与分工

详细分工、贡献值（合计 100）、周计划和风险预案见 [`team-plan.md`](./team-plan.md)。
