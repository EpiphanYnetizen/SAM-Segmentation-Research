# 系统流程与模块边界

目录与命名规则见 [`data-protocol.md`](./data-protocol.md)，这里只说流程，以及谁该碰谁不该碰。

## 端到端流程

```text
自采照片 data/raw
  -> Label Studio 标注 -> data/exports
  -> scripts/split_dataset.py -> data/splits/{train,val,test}
        |
        +-> zero-shot 推理（组员 B） ------------------+
        |                                             |
        +-> LoRA 微调（B: image encoder / 组长: mask decoder）
        |      -> checkpoints/lora/<run>/
        |      -> 带 --lora-dir 再推理 ----------------+
        |                                             |
        +---------------------------------------------+
                      |
             evaluation/evaluate.py（组员 A）
                      -> outputs/*_metrics.json
                      -> scripts/run_ablation.py
                      -> outputs/ablation_table.md
                      -> docs/report/

app/main.py 只读 checkpoints/ 和 outputs/
```

## 模块边界（越界就是返工的源头）

- `data/`：不碰模型，只生产 splits。
- `model/`：不算指标，只生产 mask 和 checkpoint。
- `evaluation/`：不碰模型，只消费 GT 和预测 mask。
- `app/`：只读 `model/` 的推理函数和 `outputs/`。
- `scripts/`：组长的编排脚本，输入输出都写死在 CLI 参数里。
