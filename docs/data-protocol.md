# 数据协议

所有下游消费方（模型、评测、UI）都只认以下两条规则。

## 目录规则

```
data/splits/{train,val,test}/
  images/<img_id>.jpg
  masks/<img_id>.png
```

- `<img_id>.png` 是单通道 uint8；0 背景，1..N 类别。
- 模型产出的预测也遵循同样命名，放 `outputs/{run}/` 下。

## 类别

类别定义以 `data/categories.yaml` 为准，改类别要同步通知组员 B 和组长，并 commit。

## 评测输入输出

```bash
python evaluation/evaluate.py --gt data/splits/val --pred outputs/zero_shot --out outputs/zero_shot_metrics.json
```

输出 JSON：`n`、`summary`（mIoU/meanDice/meanBoundaryF1）、`per_image`。
