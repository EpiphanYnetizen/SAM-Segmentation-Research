# 实验方案

## 实验 1：zero-shot 基线

- 组别：`val`。
- 提示：每个 GT 实例重心单点提示，预测掩码归 GT 类别。
- 指标：mIoU、mean Dice、mean Boundary F1。

## 实验 2：LoRA 后训练（两条分支并行）

同一个基座、同一份 `data/splits/train`，两个人各跑一条线，最后对比：

| 分支 | 脚本 | 负责人 | 冻结什么 |
|---|---|---|---|
| image encoder LoRA | `model/train_lora.py` | 组员 B | image encoder 主体，只训 LoRA 适配器 |
| mask decoder 微调 | `model/train_mask_decoder.py` | 组长 | image encoder + prompt encoder，只训 mask decoder |

- 组别：`train` -> `val` 复测。
- 变量：LoRA rank、冻结点、target_modules、学习率。
- 结论不预设；微调不涨也允许写进报告。

## 实验 3：失败案例定性

按四个错误模式分组：小目标、遮挡/重叠、低对比度/反光、细长/透明。每类挑 3-5 张可视化，形成失败案例图鉴。

## 对比表

由 `scripts/run_ablation.py` 从多份 metrics JSON 生成，按 mIoU 排序。

```bash
python scripts/run_ablation.py --metrics outputs/zero_shot_metrics.json outputs/finetuned_metrics.json outputs/mask_decoder_v1_metrics.json --out outputs/ablation_table.md
```
