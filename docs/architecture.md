# 系统流程与模块边界

目录与命名规则见 [`data-protocol.md`](./data-protocol.md)，本文只说明流程与模块职责边界。

## 端到端流程

```text
待标注照片（位置不限，不入库）
  -> Label Studio 标注 -> JSON
  -> scripts/labelstudio_to_masks.py -> data/exports/{images,masks}
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

## 模块边界（越界操作是返工的主要来源）

- `data/`：不碰模型，只生产 splits；标注工具装在哪、原始 JSON 放哪由组员 A 自行安排，仓库只接收转换后的 `data/exports`。
- `model/`：不算指标，只生产 mask 和 checkpoint。
- `evaluation/`：不碰模型，只消费 GT 和预测 mask。
- `app/`：只读 `model/` 的推理函数和 `outputs/`。
- `scripts/`：组长的编排脚本，输入输出均由 CLI 参数显式声明。
