# 数据协议（唯一真源）

下游三方（组员 B 的推理、组员 A 的评测、组长的 UI）只认本文件。改这里要通知全组。

## 目录规则

```text
data/splits/{train,val,test}/
  images/<img_id>.jpg
  masks/<img_id>.png
```

- `<img_id>.png` 是单通道 uint8：
  - `0` 背景
  - `1..5` 前景类别，定义见 [`../data/categories.yaml`](../data/categories.yaml)
  - `255` ignore，评测时完全跳过
- 预测 mask 与 GT mask **同名**，放在 `outputs/<run>/` 下。

## 类别

以 `data/categories.yaml` 为唯一真源。当前：1 meat / 2 fish / 3 vegetable / 4 rice / 5 other。

标注细则（哪些该标、哪些不标）见 [`../data/README.md`](../data/README.md)，本文件不重复。

## 接口契约

| 接口 | 路径 | 谁产出 | 谁消费 |
|---|---|---|---|
| 标注产物 | `data/exports/{images,masks}/` | 组员 A | 组长验收 |
| 数据集划分 | `data/splits/{train,val,test}/` | 组员 A | 组员 B、组长 |
| 推理结果 | `outputs/<run>/` | 组员 B、组长 | 组员 A 评测、组长 UI |
| 评测指标 | `outputs/<run>_metrics.json` | 组员 A | 组长出对比表 |
| encoder checkpoint | `checkpoints/lora/encoder/<run_id>/` | 组员 B | 推理与 UI |
| mask decoder checkpoint | `checkpoints/lora/mask_decoder/<run_id>/` | 组长 | 推理与 UI |

## 评测输入输出

```bash
python evaluation/evaluate.py --gt data/splits/val --pred outputs/zero_shot --out outputs/zero_shot_metrics.json
```

输出 JSON：`n`、`summary`（mIoU / meanDice / meanBoundaryF1）、`per_image`。
