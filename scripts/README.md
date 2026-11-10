# 公共脚本（组长）

原则：脚本以 CLI 形式交付，输入输出路径显式声明，可重复执行。

| 脚本 | 功能 | 使用者 |
|---|---|---|
| `start_labelstudio.bat` | 启动仓库外 `project/tools/labelstudio` 中的 Label Studio，并设置 Local Files 根目录 | 组员 A |
| `labelstudio_to_masks.py` | Label Studio 导出的 JSON → `data/exports/{images,masks}`，按 `categories.yaml` 映射类别 | 组员 A |
| `split_dataset.py` | 将 `data/exports` 划分为 `data/splits/{train,val,test}`，比例 7:1:2，随机种子固定 | 组员 A |
| `convert_masks.py` | 将其他工具导出的 PNG mask 规整为 0..5 类别，原始导出备份为 `<name>_raw.png` | 组员 A |
| `run_ablation.py` | 汇总多份 `*_metrics.json`，按 mIoU 排序生成 Markdown 对比表 | 组长 |
| `validate_dataset.py` | 校验图片与 mask 配套、尺寸一致、类别合法、重复图片 | 组员 A / 组长 |

```powershell
# 启动标注工具（首次使用先按 docs/labelstudio.md 安装）
scripts\start_labelstudio.bat

# Label Studio JSON -> PNG mask
python scripts\labelstudio_to_masks.py --export ..\tools\labelstudio\exports\project.json --image-dir ..\tools\labelstudio\images --out data\exports

# 校验、划分、汇总
python scripts\validate_dataset.py --data-dir data\exports
python scripts\split_dataset.py --data-dir data\exports --out data\splits
python scripts\run_ablation.py --metrics outputs\zero_shot_metrics.json outputs\finetuned_metrics.json --out outputs\ablation_table.md
```

`labelstudio_to_masks.py` 支持多边形、画笔 RLE 和矩形区域。完整标注流程见 [`../docs/labelstudio.md`](../docs/labelstudio.md)。

`convert_masks.py` 只用于其他标注工具直接导出 PNG mask 的情况；Label Studio JSON 请使用 `labelstudio_to_masks.py`，不要先手工导出 PNG 再规整。

评测脚本位于 `evaluation/evaluate.py`，归属组员 A 模块，不纳入本目录。
