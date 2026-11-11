# SAM-Segmentation-Research

> 深度学习课程项目 · Research Track No.2 · Large Visual Model
> 核心研究问题：Does Segment Anything work on all cases?

## 阅读入口

| 你是谁 | 第一步 | 你负责的目录 | 你要交的东西 |
|---|---|---|---|
| 组长（黄闻喆） | [`team-plan.md`](./team-plan.md) | `app/` `docker/` `scripts/`，以及 `model/train_mask_decoder.py` | mask decoder 微调、消融实验、演示 UI、开题 PPT/视频、报告串稿 |
| 组员 B（葛瀚然） | [`model/README.md`](./model/README.md) | `model/`（`train_mask_decoder.py` 除外） | SAM 加载与 zero-shot 推理、image encoder LoRA、checkpoint |
| 组员 A（曹庆科） | [`data/README.md`](./data/README.md) → [`evaluation/README.md`](./evaluation/README.md) | `data/`、`evaluation/` | 自采图片与标注、数据集划分、指标计算、失败案例 |

成员之间通过接口交接，接口定义见 [`docs/data-protocol.md`](./docs/data-protocol.md)，谁产出、谁消费均需在文档中记录，避免口头约定造成偏差。

## 项目要做什么

一句话：先测 SAM 在自采食堂菜品上的零样本能力与失败边界，再用 LoRA 后训练 SAM 的 image encoder 和 mask decoder，用 mIoU / Dice / 边界 F1 对比 `zero-shot vs fine-tuned`，最后做一个能上传图片的分割演示 UI。

```text
自采照片 → 标注 → 数据集划分 ─┬→ zero-shot 推理 → 评测 ─┐
                              └→ LoRA 微调 → 再推理 → 评测 ─┴→ 对比表 → 报告 / PPT / 视频
```

## 当前实现状态

### 已实现（安装依赖后可直接运行）

| 模块 | 用途 |
|---|---|
| `scripts/labelstudio_to_masks.py` | 将 Label Studio 导出的 JSON 转成 `data/exports/{images,masks}` |
| `scripts/validate_dataset.py` | 校验图片与 mask 配套、尺寸一致、类别合法、重复图片 |
| `scripts/split_dataset.py` | 将 `data/exports` 划分为 `data/splits/{train,val,test}` |
| `scripts/convert_masks.py` | 将其他工具导出的 PNG mask 规整为 0..5 类别（Label Studio 流程不需要） |
| `model/zero_shot_inference.py` | 加载 SAM 按 GT 单点提示推理（oracle-point，不是自动实例分割）；`--lora-dir` / `--decoder-ckpt` 可评测两条微调分支 |
| `evaluation/evaluate.py` | 对齐 GT 与预测 mask，输出 mIoU / Dice / 边界 F1 |
| `scripts/run_ablation.py` | 汇总多份评测结果，生成 Markdown 对比表 |
| `model/quick_demo.py` | 不依赖标注，单图验证权重与显卡（点提示或自动模式） |

### 待实现（脚手架已就位，训练循环和 UI 推理未接）

| 模块 | 已有 | 待办 | 负责人 |
|---|---|---|---|
| `model/train_lora.py` | 配置加载、LoRA 注入、`--check` 自检 | 训练循环、checkpoint 保存 | 组员 B |
| `model/train_mask_decoder.py` | 配置加载、冻结策略、`--check` 自检 | 训练循环、checkpoint 保存 | 组长 |
| `app/main.py` | Gradio 界面与启动参数 | 把点击坐标接到 `sam_runtime.predict_with_prompt` | 组长 |

未实现的部分会明确报错退出，不会静默输出全零结果。训练前先跑自检：

```powershell
python model\train_lora.py --check
python model\train_mask_decoder.py --check
```

## 推进顺序

1. 组员 A：按 [`data/README.md`](./data/README.md) 用 Label Studio 标注，导出 JSON 后用 `scripts/labelstudio_to_masks.py` 转成 PNG mask，再划分 `data/splits/{train,val,test}`。
2. 组员 B：安装 `model/requirements.txt`，下载权重，在 `val` 上运行 `model/zero_shot_inference.py`。
3. 组员 A：运行 `evaluation/evaluate.py`，产出第一份 `outputs/zero_shot_metrics.json` 基线。
4. 组员 B：`python model\train_lora.py --check` 通过后，补训练循环，产出 `checkpoints/lora/encoder/<run_id>/`。
5. 组长：`python model\train_mask_decoder.py --check` 通过后，补训练循环，产出 `checkpoints/lora/mask_decoder/<run_id>/mask_decoder.pth`。
6. 组长：把 `app/main.py` 接到 `model/sam_runtime.py`，完成点提示演示。

> `data/exports/images`、`data/exports/masks`、`data/annotations`、`data/splits` 已建好；空目录用 `.gitkeep` 占位，真实数据不会进 Git。


## 常用命令

```powershell
# 标注 JSON -> PNG mask（JSON 和图片位置不限）
python scripts\labelstudio_to_masks.py --export <导出的.json> --image-dir <原图目录> --out data\exports

# 校验、划分
python scripts\validate_dataset.py --data-dir data\exports
python scripts\split_dataset.py --data-dir data\exports --out data\splits

# zero-shot 推理、评测
python model\zero_shot_inference.py --checkpoint checkpoints\sam_vit_b_01ec64.pth --data-dir data\splits\val --out outputs\zero_shot
python evaluation\evaluate.py --gt data\splits\val --pred outputs\zero_shot --out outputs\zero_shot_metrics.json

# 微调后推理（二选一）
python model\zero_shot_inference.py --data-dir data\splits\val --lora-dir checkpoints\lora\encoder\<run_id> --out outputs\finetuned
python model\zero_shot_inference.py --data-dir data\splits\val --decoder-ckpt checkpoints\lora\mask_decoder\<run_id>\mask_decoder.pth --out outputs\mask_decoder_v1

# 汇总对比表
python scripts\run_ablation.py --metrics outputs\zero_shot_metrics.json outputs\finetuned_metrics.json --out outputs\ablation_table.md
```

## 硬节点

| 日期 | 事项 | 状态 |
|---|---|---|
| 10/11 | 报名邮件，主题 `深度学习_黄闻喆_曹庆科_葛瀚然_选题_2` | 已发送 |
| **10/25** | **交 `开题报告.ppt`（恰好 3 页）+ `开题报告.mp4`（3 分钟）** | 已完成（成品在本地，按课程要求单独提交） |
| 10/25 后 | zero-shot 跑通 → 双分支微调 → 消融 → 最终报告 | 进行中 |

提交物（PPT、视频、演讲稿）不进 Git，组内自行备份。

## 进度看板

- [x] 仓库骨架、分工、接口契约
- [x] 报名邮件已发送
- [x] 开题 PPT（3 页）+ 视频（3 分钟）
- [x] 数据工具链（JSON 转 mask → 校验 → 7:1:2 划分）
- [x] zero-shot 推理脚本与评测指标
- [ ] 组员 A：自采 80-120 张并标注（目标 400-600 个实例）
- [ ] 组员 B：补 `train_lora.py` 训练循环，产出 encoder LoRA
- [ ] 组长：补 `train_mask_decoder.py` 训练循环并接入 UI
- [ ] 三人：`zero-shot vs fine-tuned` 对比表
- [ ] 最终报告 + 答辩演示

## 环境准备

训练和评测统一使用仓库根目录的 `.venv`，PyCharm 的解释器也指向它。三个人装同一套依赖，避免版本漂移。Label Studio 是唯一例外，建议装在独立环境，避免 Django 等依赖污染训练环境。

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows；Linux/macOS 用 source .venv/bin/activate
pip install -r requirements.txt
```

| 角色 | 额外安装 |
|---|---|
| 组员 A | Label Studio（建议独立环境，见 [`data/README.md`](./data/README.md)） |
| 组员 B | `pip install -r model/requirements.txt` |
| 组长（要跑 UI） | `pip install -r app/requirements.txt` |

Windows 上 `torch` 必须用 cu118 轮子。`model/requirements.txt` 已固定 `torch==2.7.1+cu118` 与 `torchvision==0.22.1+cu118`，直接安装即可。单独装 torch 时若不指定索引，会装成 CPU 版，SAM 推理会慢几十倍。

验证环境：

```bash
python -c "import torch, segment_anything; print(torch.__version__, torch.cuda.is_available())"
```

## 仓库规则

1. 禁止 force push `main`。
2. 分支命名 `feature/<角色>-<简短描述>`，例如 `feature/a-label-export`、`feature/b-lora-train`。
3. **只改自己的目录**；`docs/` 和根目录由组长统一汇总，避免三个人同时改同一个文件。
4. 大文件一律不进 git：模型权重、原始照片、视频、PPT、checkpoints 都已写进 `.gitignore`。
5. 交付物命名严格按课程要求：`开题报告.ppt`、`开题报告.mp4`。

## 模块边界

- `data/`：只生产 `data/splits`，不碰模型。
- `model/`：只生产预测 mask 和 checkpoint，不算指标。
- `evaluation/`：只消费 GT 和预测 mask，产出 metrics JSON。
- `app/`：只读模型推理接口和 `outputs/`，不训练、不评测。
- `scripts/`：共享编排脚本，输入输出用 CLI 参数显式声明。

## 文档地图

| 文件 | 内容 | 谁维护 |
|---|---|---|
| [`team-plan.md`](./team-plan.md) | 分工、贡献值、周计划、风险预案 | 组长 |
| [`docs/project-brief.md`](./docs/project-brief.md) | 课程 PDF 原文逐条摘录 | 组长 |
| [`docs/data-protocol.md`](./docs/data-protocol.md) | 目录、命名、类别契约（唯一真源） | 组长 |
| [`docs/experiment-plan.md`](./docs/experiment-plan.md) | 三个实验怎么设计 | 组长 |
| [`app/README.md`](./app/README.md) | Gradio 最小演示启动 | 组长 |
| [`docs/app-design.md`](./docs/app-design.md) | UI/API/Docker 设计 | 组长 |
| [`docs/report/`](./docs/report) | 最终报告分章草稿 | 全员写，组长串稿 |

## 报告分章

| 章节 | 文件 | 负责人 |
|---|---|---|
| 1 背景与问题定义 | [`docs/report/background.md`](./docs/report/background.md) | 组长 |
| 2 数据来源与预处理 | 待建 `docs/report/data.md` | 组员 A |
| 3 方法与改进 | [`docs/report/method.md`](./docs/report/method.md) | 组员 B + 组长 |
| 4 实验设计与指标 | 待建 `docs/report/experiments.md` | 组长 |
| 5 结果与失败案例 | [`docs/report/results.md`](./docs/report/results.md) | 组员 A |
| 6 讨论与结论 | 待建 `docs/report/discussion.md` | 组长 |

## 技术栈

| 层 | 技术 |
|---|---|
| 分割模型 | `segment-anything`（SAM ViT-B）或 SAM2 |
| 微调 | PyTorch + `peft`（LoRA） |
| 标注 | Label Studio |
| 评测 | NumPy + SciPy，指标在 `evaluation/metrics.py` 自己实现，不用黑盒 |
| UI | Vue 3 + FastAPI（Gradio 保留为最小演示） |
| 部署 | 本地 Python；Docker Compose 可选 |
| 硬件 | 训练建议 ≥8G 显存（不足可租用算力）；4G 显存只够推理和单图 demo |
