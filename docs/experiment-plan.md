# 实验方案

## 实验 1：zero-shot 基线

- 组别：`val`。
- 提示：每个 GT 实例重心单点提示，预测掩码归 GT 类别。
- 指标：mIoU、mean Dice、mean Boundary F1。

## 实验 2：LoRA 微调

- 组别：`train` -> `val` 复测。
- 变量：LoRA rank、冻结点、target_modules。
- 结论不预设；微调不涨也允许写进报告。

## 实验 3：失败案例定性

按四个错误模式分组：小目标、遮挡/重叠、低对比度/反光、细长/透明。每类挑 3-5 张可视化，形成失败案例图鉴。

## 对比表

由 `scripts/make_report_tables.py` 从两个 metrics JSON 生成。
