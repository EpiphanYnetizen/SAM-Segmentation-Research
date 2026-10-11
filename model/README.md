# 模型与训练（组员 B）

这里负责 SAM/SAM2 的加载、zero-shot 推理、LoRA 微调与 checkpoint 管理。

## 依赖

```bash
pip install -r requirements.txt
```

## 权重

把权重放在 `checkpoints/`（本仓库忽略）。

- 首选：`sam_vit_b_01ec64.pth`（Meta SAM ViT-B）
- 备选：MobileSAM 或 HuggingFace `facebook/sam-vit-base`

## 启动顺序

1. `zero_shot_inference.py` 产出 `outputs/zero_shot/`
2. `train_lora.py` 基于 `data/splits/train` 微调，产出 `checkpoints/lora/<run_id>/`
3. `zero_shot_inference.py --lora-dir ...` 用微调模型再跑 `outputs/finetuned/`

## 接口约定

- 推理输入/输出目录都遵守 `data/README.md` 的 `images/` + `masks/` 命名。
- 脚本报错时要给用户能自检的一句话（缺包、缺权重、缺目录分别提示）。
