# 评测（组员 A · 曹庆科）

本模块负责对齐 GT 与预测 mask，计算 mIoU、mean Dice、mean Boundary F1。
指标全部由 `metrics.py` 使用 NumPy 与 SciPy 自行实现，报告可解释具体公式。

## 产出与消费关系

| 角色 | 动作 |
|---|---|
| 组员 B / 组长 | 生成预测 mask 至 `outputs/<run>/` |
| 组员 A | 运行本模块脚本，产出 `outputs/<run>_metrics.json` |
| 组长 | 使用 `scripts/run_ablation.py` 汇总对比表 |

## 使用

```bash
python evaluation/evaluate.py --gt data/splits/val --pred outputs/zero_shot --out outputs/zero_shot_metrics.json
```

预测 mask 与 GT mask 同名；`--gt` / `--pred` 支持 `masks/` 目录树或纯 PNG 目录。

微调后评测复用同一脚本，仅替换 `--pred` 为 `outputs/finetuned` 或 `outputs/mask_decoder_v1`。

## 输出格式

```json
{
  "n": 42,
  "summary": { "mIoU": 0.0, "meanDice": 0.0, "meanBoundaryF1": 0.0 },
  "per_image": { "img_001": { "mIoU": 0.0, "meanDice": 0.0, "meanBoundaryF1": 0.0 } }
}
```

## 交付物

- 每个实验组一份 `<run>_metrics.json`。
- 四类错误模式各选 3-5 张可视化，整理为失败案例图鉴：小目标、遮挡 / 重叠、低对比度 / 反光、细长 / 透明。
- 失败案例图鉴是报告第 5 章的核心素材，与指标数据共同构成评估结论。

## 口径说明

`compute_metrics` 默认忽略 `0`（背景）与 `255`（ignore），对其余前景类的三项指标取算术平均。

当前 summary 包含 `other`（id=5）。如报告口径为「主指标只报 1-4 类，`other` 单列」，需在结果阶段按类拆分，脚本不默认执行该筛选。
