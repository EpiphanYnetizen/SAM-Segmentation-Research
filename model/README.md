# 模型与训练

## 职责划分

| 文件 | 归属 | 职责 |
|---|---|---|
| `zero_shot_inference.py` | 组员 B | 加载 SAM，用 GT 点提示跑零样本推理 |
| `train_lora.py` | 组员 B | 冻结主干，给 image encoder 的 `qkv`/`proj` 挂 LoRA 微调 |
| `train_mask_decoder.py` | 组长 | 冻结 image encoder + prompt encoder，只训 mask decoder |
| `config/default.yaml` | 组员 B | `train_lora.py` 的超参 |
| `config/mask_decoder.yaml` | 组长 | `train_mask_decoder.py` 的超参 |
| `sam_runtime.py` | 组长 | 权重/Adapter 加载、实例提示构造，推理与训练共用 |

两条实验分支独立推进，最终在 `evaluation/` 统一对比。

## 组员 B（葛瀚然）任务

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

### 4. LoRA 微调 image encoder（待补训练循环）

先自检环境和挂载点，输出应类似 `0.5 M 可训练参数`：

```bash
python model/train_lora.py --check
```

自检通过后再补训练循环。需要实现的部分：

1. 从 `data/splits/train` 读 (image, mask)，用 `sam_runtime.instance_prompts` 把 mask 拆成实例；
2. 每个实例取内部点，按 `SamPredictor` 相同的前处理后跑 `image_encoder → prompt_encoder → mask_decoder`；
3. 只反传 LoRA 参数（`get_peft_model` 已自动冻结其余参数），loss 用 BCE + Dice；
4. 保存 adapter 到 `checkpoints/lora/encoder/<run_id>/`（`save_pretrained` 会写 `adapter_config.json` 和 `adapter_model.bin`）；
5. 保存 `train_config.json`，记录 epoch、lr、rank、训练集大小，方便复现。

训练完成后用同一个推理脚本评测：

```bash
python model/zero_shot_inference.py --data-dir data/splits/val \
  --lora-dir checkpoints/lora/encoder/<run_id> --out outputs/finetuned
```

`target_modules` 必须是 `qkv` 和 `proj`。写成 `query`/`value` 会直接报
`Target modules not found in the base model`，这是 SAM 与 HuggingFace 模型的命名差异。

### 5. 不标注也能先验证环境

```bash
python model/quick_demo.py --image data/raw/xxx.jpg
python model/quick_demo.py --image data/raw/xxx.jpg --point 800 600
```

自动模式不需要任何标注，用来确认权重能加载、显卡能跑；结果保存在 `outputs/demo/`。

## 组长任务

```bash
python model/train_mask_decoder.py --check          # 先确认冻结策略
python model/train_mask_decoder.py --config model/config/mask_decoder.yaml
```

需要补的部分：数据加载与提示构造同上一节第 4 步；encoder 前向放进 `torch.no_grad()`，
只保留 `mask_decoder` 参数的梯度；保存 `{"model": state_dict}` 到
`checkpoints/lora/mask_decoder/<run_id>/mask_decoder.pth`，推理时用 `--decoder-ckpt` 加载。

分工与时间安排见 [`../team-plan.md`](../team-plan.md)。

## 接口约定

- 输入输出目录一律遵守 [`../docs/data-protocol.md`](../docs/data-protocol.md)。
- 脚本报错信息应说明排查方向：缺少依赖 / 缺少权重 / 缺少目录分别提示。

## 当前状态

- `zero_shot_inference.py`、`quick_demo.py`、`sam_runtime.py`：已实现，尚未在真实数据上批量跑过。
- `train_lora.py`、`train_mask_decoder.py`：只有配置加载、LoRA 注入/冻结策略和 `--check` 自检，
  训练循环未实现，直接运行会报错退出。

补完训练循环后，请在本文件登记实测命令与耗时。
