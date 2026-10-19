# 模型与训练

## 职责划分

| 文件 | 归属 | 职责 |
|---|---|---|
| `zero_shot_inference.py` | 组员 B | 加载 SAM，用 GT 点提示跑零样本推理 |
| `train_lora.py` | 组员 B | 冻结主干，给 image encoder 的 query/value 挂 LoRA 微调 |
| `train_mask_decoder.py` | 组长 | 冻结 image encoder + prompt encoder，只训 mask decoder |
| `config/default.yaml` | 组员 B | `train_lora.py` 的超参 |
| `config/mask_decoder.yaml` | 组长 | `train_mask_decoder.py` 的超参 |

两条实验分支独立推进，最终在 `evaluation/` 统一对比。

## 组员 B 任务

### 1. 安装依赖

```bash
pip install -r model/requirements.txt
```

### 2. 下载权重

放置于 `checkpoints/`（git 忽略）：

- 首选 `sam_vit_b_01ec64.pth`（Meta SAM ViT-B）
- 显存不足时改用 MobileSAM，或使用 HuggingFace `facebook/sam-vit-base`

### 3. zero-shot 推理

```bash
python model/zero_shot_inference.py --checkpoint checkpoints/sam_vit_b_01ec64.pth --data-dir data/splits/val --out outputs/zero_shot
```

产出 `outputs/zero_shot/`，移交组员 A 评测。

### 4. LoRA 微调 image encoder

```bash
python model/train_lora.py --config model/config/default.yaml
```

产出 `checkpoints/lora/<run_id>/`，并以 `--lora-dir` 再次推理得到 `outputs/finetuned/`。

## 组长任务

```bash
python model/train_mask_decoder.py --config model/config/mask_decoder.yaml
```

分工与时间安排见 [`../team-plan.md`](../team-plan.md)。

## 接口约定

- 输入输出目录一律遵守 [`../docs/data-protocol.md`](../docs/data-protocol.md)。
- 脚本报错信息应说明排查方向：缺少依赖 / 缺少权重 / 缺少目录分别提示。

## 当前状态

三个脚本当前为框架代码，尚未在真实数据上完成训练或推理验证。完成后请在本文件补充实测命令。
