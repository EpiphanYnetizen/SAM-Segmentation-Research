# 公共脚本（组长）

原则：输入输出路径明确、可重复执行的 CLI，避免手改代码跑实验。

| 脚本 | 干什么 | 谁用 |
|---|---|---|
| `split_dataset.py` | `data/exports` -> `data/splits/{train,val,test}`，7:1:2，seed 固定 | 组员 A |
| `convert_masks.py` | 把标注导出的 PNG mask 规整成 0..5 类别编号，原文件备份为 `<name>_raw.png` | 组员 A |
| `run_ablation.py` | 多份 `*_metrics.json` -> 一张 Markdown 对比表，按 mIoU 排序 | 组长 |

```bash
python scripts/split_dataset.py --data-dir data/exports --out data/splits
python scripts/convert_masks.py --src data/exports/masks --dst data/exports/masks
python scripts/run_ablation.py --metrics outputs/zero_shot_metrics.json outputs/finetuned_metrics.json --out outputs/ablation_table.md
```

评测脚本在 `evaluation/evaluate.py`，归组员 A，不放在这里。
