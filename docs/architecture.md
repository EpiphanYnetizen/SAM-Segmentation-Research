# 系统流程

```text
自采 data/raw
   -> Label Studio 标注
   -> data/exports
   -> scripts/split_dataset.py
   -> data/splits/{train,val,test}

model/zero_shot_inference.py
   -> outputs/zero_shot

model/train_lora.py
   -> checkpoints/lora/<run>
   -> model/zero_shot_inference.py --lora-dir
   -> outputs/finetuned

evaluation/evaluate.py
   -> outputs/*_metrics.json
   -> scripts/make_report_tables.py
   -> docs/report/
```

## 模块边界

- `data`：不碰模型，只生产 splits。
- `model`：不碰指标，只生产 mask。
- `evaluation`：不碰模型，只消费 GT 和预测 mask。
- `app`：只读 model 和 outputs。
