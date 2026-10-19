# 公共脚本（组长）

原则：脚本以 CLI 形式交付，输入输出路径显式声明，可重复执行。

| 脚本 | 功能 | 使用者 |
|---|---|---|
| `split_dataset.py` | 将 `data/exports` 划分为 `data/splits/{train,val,test}`，比例 7:1:2，随机种子固定 | 组员 A |
| `convert_masks.py` | 将标注导出的 PNG mask 规整为 0..5 类别，原始导出备份为 `<name>_raw.png` | 组员 A |
| `run_ablation.py` | 汇总多份 `*_metrics.json`，按 mIoU 排序生成 Markdown 对比表 | 组长 |

```bash
python scripts/split_dataset.py --data-dir data/exports --out data/splits
python scripts/convert_masks.py --src data/exports/masks --dst data/exports/masks
python scripts/run_ablation.py --metrics outputs/zero_shot_metrics.json outputs/finetuned_metrics.json --out outputs/ablation_table.md
```

评测脚本位于 `evaluation/evaluate.py`，归属组员 A 模块，不纳入本目录。
