# 实验方案

## 实验 1：zero-shot 基线

- 组别：`val`。
- 提示：每个 GT 实例做单点提示，点取实例内部距离变换最大处（凹形物体的质心会落到物体外，
  用质心会低估 SAM 能力）；预测掩码归 GT 类别。
- 指标：mIoU、mean Dice、mean Boundary F1。

> 本实验是 **oracle-point / prompted segmentation**：提示点来自 GT mask，回答的是
> “已知每个菜品实例的位置时，SAM 能否把它分割出来”，**不能**回答“SAM 能否自动发现
> 并分割图中所有菜品”。报告、PPT 和答辩必须写明提示协议，不能把该指标表述成自动
> 实例分割能力。自动模式（网格点或自动 mask）只能作为补充实验单独报告。

> 重叠处理：当前推理按实例顺序写入 mask，重叠像素归后写入的类别；遮挡或菜品重叠时
> 会引入类别偏差。后续可按 SAM score 或实例面积归属，并单独统计实例级指标。

微调后的复测必须用同一套提示与同一份 `val`，否则两条曲线不可比。

## 实验 2：LoRA 后训练（两条分支并行）

同一个基座、同一份 `data/splits/train`，两个人各跑一条线，最后对比：

| 分支 | 脚本 | 负责人 | 冻结什么 |
|---|---|---|---|
| image encoder LoRA | `model/train_lora.py` | 组员 B | image encoder 主体，只训 LoRA 适配器 |
| mask decoder 微调 | `model/train_mask_decoder.py` | 组长 | image encoder + prompt encoder，只训 mask decoder |

- 组别：`train` -> `val` 复测。
- 变量：LoRA rank、冻结点、target_modules、学习率。
- 结论不预设；微调不涨也允许写进报告。

## 实验 3：失败案例定性

按四个错误模式分组：小目标、遮挡/重叠、低对比度/反光、细长/透明。每类挑 3-5 张可视化，形成失败案例图鉴。

## 对比表

由 `scripts/run_ablation.py` 从多份 metrics JSON 生成，按 mIoU 排序。

```bash
python scripts/run_ablation.py --metrics outputs/zero_shot_metrics.json outputs/finetuned_metrics.json outputs/mask_decoder_v1_metrics.json --out outputs/ablation_table.md
```
