# 模型与训练

## 谁做什么

| 文件 | 归属 | 干什么 |
|---|---|---|
| `zero_shot_inference.py` | 组员 B | 加载 SAM，用 GT 点提示跑零样本推理 |
| `train_lora.py` | 组员 B | 冻结主干，给 image encoder 的 query/value 挂 LoRA 微调 |
| `train_mask_decoder.py` | 组长 | 冻结 image encoder + prompt encoder，只训 mask decoder |
| `config/default.yaml` | 组员 B | `train_lora.py` 的超参 |
| `config/mask_decoder.yaml` | 组长 | `train_mask_decoder.py` 的超参 |

两条实验线各跑各的，最后在 `evaluation/` 合流对比。

## 组员 B 的活

### 1. 装依赖

```bash
pip install -r model/requirements.txt
```

### 2. 下权重

放 `checkpoints/`（git 忽略，不进仓库）：

- 首选 `sam_vit_b_01ec64.pth`（Meta SAM ViT-B）
- 显存不够就退 MobileSAM，或用 HuggingFace `facebook/sam-vit-base`

### 3. 跑通 zero-shot

```bash
python model/zero_shot_inference.py --checkpoint checkpoints/sam_vit_b_01ec64.pth --data-dir data/splits/val --out outputs/zero_shot
```

产出 `outputs/zero_shot/`，交给组员 A 评测。

### 4. LoRA 微调 image encoder

```bash
python model/train_lora.py --config model/config/default.yaml
```

产出 `checkpoints/lora/<run_id>/`，再用 `--lora-dir` 跑一遍推理得到 `outputs/finetuned/`。

## 组长的活

```bash
python model/train_mask_decoder.py --config model/config/mask_decoder.yaml
```

分工与时间表见 [`../team-plan.md`](../team-plan.md)。

## 接口约定

- 输入输出目录一律遵守 [`../docs/data-protocol.md`](../docs/data-protocol.md)。
- 脚本报错必须给一句人话自检提示：缺包 / 缺权重 / 缺目录，分别说清。

## 现状

三个脚本都是**待接入骨架**，还没在真实数据上跑通过。谁跑通谁在这里补一条实测命令。
