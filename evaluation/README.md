# 评测（组员 A）

本目录只干一件事：读 GT mask 和预测 mask，算 mIoU、mean Dice、mean Boundary F1。
指标全在 `metrics.py` 里自己实现（NumPy + SciPy），不用第三方黑盒，报告里能讲清公式。

## 谁产出、谁消费

| 角色 | 动作 |
|---|---|
| 组员 B / 组长 | 产出预测 mask 到 `outputs/<run>/` |
| **你（组员 A）** | 跑本目录脚本，产出 `outputs/<run>_metrics.json` |
| 组长 | 用 `scripts/run_ablation.py` 把多份 metrics JSON 汇成对比表 |

## 使用

```bash
python evaluation/evaluate.py --gt data/splits/val --pred outputs/zero_shot --out outputs/zero_shot_metrics.json
```

预测 mask 和 GT mask 同名即可；`--gt` / `--pred` 既能传 `masks/` 目录树，也能传纯 PNG 目录。

微调后评测用同一个脚本，只换 `--pred`：`outputs/finetuned` 或 `outputs/mask_decoder_v1`。

## 输出格式

```json
{
  "n": 42,
  "summary": { "mIoU": 0.0, "meanDice": 0.0, "meanBoundaryF1": 0.0 },
  "per_image": { "img_001": { "mIoU": 0.0, "meanDice": 0.0, "meanBoundaryF1": 0.0 } }
}
```

## 你要交的东西

- 每个实验组一份 `<run>_metrics.json`
- 四个错误模式各挑 3-5 张可视化，做成「失败案例图鉴」：小目标、遮挡/重叠、低对比度/反光、细长/透明
- 这四组失败案例是报告第 5 章的核心素材，比单纯刷指标更值钱

## 注意

`compute_metrics` 默认不计背景类（id=0）进类别均值。`other`（id=5）单独报，不要混进主指标。
