# 评测（组员 A）

本目录只负责读取 GT mask 和预测 mask，输出可复现的指标。所有指标都由本目录直接计算：mIoU、mean Dice、mean Boundary F1。输入约定见 `../data/README.md` 的 mask 树。微调后评测用同一脚本，只是 `--pred` 换成 `outputs/mask_decoder_v1` 或 `outputs/finetuned`。

## 使用

```bash
python evaluation/evaluate.py \
  --gt data/splits/val \
  --pred outputs/zero_shot \
  --out outputs/zero_shot_metrics.json
```

`--pred` 目录中每个预测 mask 与 GT mask 同名；也可以传 `--pred-out-dir` 来匹配 `images/` + `masks/` 结构。
