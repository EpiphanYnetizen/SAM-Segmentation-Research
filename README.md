# SAM-Segmentation-Research

> 深度学习课程项目 · Research Track No.2 · Large Visual Model
> 核心研究问题：Does Segment Anything work on all cases?

## 你该先看哪个文件

| 你是谁 | 第一步 | 你负责的目录 | 你要交的东西 |
|---|---|---|---|
| 组长（黄闻喆） | [`team-plan.md`](./team-plan.md) | `app/` `docker/` `scripts/`，以及 `model/train_mask_decoder.py` | mask decoder 微调、消融实验、演示 UI、开题 PPT/视频、报告串稿 |
| 组员 B | [`model/README.md`](./model/README.md) | `model/`（`train_mask_decoder.py` 除外） | SAM 加载与 zero-shot 推理、image encoder LoRA、checkpoint |
| 组员 A | [`data/README.md`](./data/README.md) → [`evaluation/README.md`](./evaluation/README.md) | `data/`、`evaluation/` | 自采图片与标注、数据集划分、指标计算、失败案例 |

三个人之间只通过**接口**交接，接口定义见 [`docs/data-protocol.md`](./docs/data-protocol.md)。谁产出、谁消费都写在那里，不要口头约定。

## 项目要做什么

一句话：先测 SAM 在自采食堂菜品上的零样本能力与失败边界，再用 LoRA 后训练 SAM 的 image encoder 和 mask decoder，用 mIoU / Dice / 边界 F1 对比 `zero-shot vs fine-tuned`，最后做一个能上传图片的分割演示 UI。

```text
自采照片 → 标注 → 数据集划分 ─┬→ zero-shot 推理 → 评测 ─┐
                              └→ LoRA 微调 → 再推理 → 评测 ─┴→ 对比表 → 报告 / PPT / 视频
```

## 现在能真跑，还是骨架

**装好依赖后能真跑：**

- `scripts/split_dataset.py`：`data/exports` -> `data/splits/{train,val,test}`
- `model/zero_shot_inference.py`：SAM 零样本推理，代码已接好，只差权重和依赖
- `evaluation/evaluate.py` + `metrics.py`：GT 和预测 mask 对齐，算 mIoU / Dice / 边界 F1
- `scripts/run_ablation.py`：多份 metric JSON -> Markdown 对比表

**还是骨架，别当已跑通：**

- `model/train_lora.py`：组员 B 的 image encoder LoRA，目前只加载配置，训练循环待写
- `model/train_mask_decoder.py`：组长的 mask decoder 微调，同上
- `app/main.py`：Gradio 界面能打开，但 `render_mask()` 还返回全零，没接 SAM

## 按这个顺序做

1. **组员 A**：照片 -> `data/exports` -> `scripts/split_dataset.py`，交出一份 train/val/test
2. **组员 B**：装 `model/requirements.txt` -> 下载权重 -> 在 `val` 跑通 `zero_shot_inference.py`
3. **组员 A**：跑 `evaluation/evaluate.py`，得到第一份 `zero_shot_metrics.json`（零样本基线）
4. **组员 B**：补 `train_lora.py` 的训练循环
5. **组长**：补 `train_mask_decoder.py`，并把 `app/main.py` 的 `render_mask()` 接上真实推理

## 硬节点

| 日期 | 事项 | 状态 |
|---|---|---|
| 10/11 | 报名邮件，主题 `深度学习_[姓名1]_[姓名2]_[姓名3]_选题_2` | 已过期，需确认是否已发 |
| **10/25** | **交 `开题报告.ppt`（恰好 3 页）+ `开题报告.mp4`（3 分钟）** | 硬截止，进行中 |
| 10/25 后 | zero-shot 跑通 → 双分支 LoRA → 消融 → 最终报告 | 未开始 |

开题材料 10/24 前做成成品，10/25 当天发邮件。

## 进度看板

- [x] 仓库骨架、分工、接口契约
- [ ] 报名邮件确认是否已发
- [ ] 组员 A：自采 80-120 张并标注（目标 400-600 个实例）
- [ ] 组员 B：跑通 SAM zero-shot
- [ ] 组长：mask decoder 微调 + 消融
- [ ] 三人：`zero-shot vs fine-tuned` 对比表
- [ ] 开题 PPT（3 页）+ 视频（3 分钟）

## 装环境

**只有组员 B 需要完整装一遍**，因为只有他的脚本要 PyTorch 和 SAM。A 和组长按需装。

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows；Linux/macOS 用 source .venv/bin/activate
pip install -r requirements.txt
```

| 角色 | 额外安装 |
|---|---|
| 组员 A | 无，`requirements.txt` 够用 |
| 组员 B | `pip install -r model/requirements.txt` |
| 组长（要跑 UI） | `pip install -r app/requirements.txt` |

## 仓库规则

1. 禁止 force push `main`。
2. 分支命名 `feature/<角色>-<简短描述>`，例如 `feature/a-label-export`、`feature/b-lora-train`。
3. **只改自己的目录**；`docs/` 和根目录由组长统一汇总，避免三个人同时改同一个文件。
4. 大文件一律不进 git：模型权重、原始照片、视频、PPT、checkpoints 都已写进 `.gitignore`。
5. 交付物命名严格按课程要求：`开题报告.ppt`、`开题报告.mp4`。

## 文档地图

| 文件 | 内容 | 谁维护 |
|---|---|---|
| [`team-plan.md`](./team-plan.md) | 分工、贡献值、周计划、风险预案 | 组长 |
| [`docs/project-brief.md`](./docs/project-brief.md) | 课程 PDF 原文逐条摘录 | 组长 |
| [`docs/data-protocol.md`](./docs/data-protocol.md) | 目录、命名、类别契约（唯一真源） | 组长 |
| [`docs/architecture.md`](./docs/architecture.md) | 端到端流程与模块边界 | 组长 |
| [`docs/experiment-plan.md`](./docs/experiment-plan.md) | 三个实验怎么设计 | 组长 |
| [`docs/report/`](./docs/report) | 最终报告分章草稿 | 全员写，组长串稿 |

## 技术栈

| 层 | 技术 |
|---|---|
| 分割模型 | `segment-anything`（SAM ViT-B）或 SAM2 |
| 微调 | PyTorch + `peft`（LoRA） |
| 标注 | Label Studio |
| 评测 | NumPy + SciPy，指标在 `evaluation/metrics.py` 自己实现，不用黑盒 |
| UI | Gradio |
| 部署 | 本地 Python；Docker Compose 可选 |
| 硬件 | 单卡 8G 以上，不够就退到 MobileSAM |
