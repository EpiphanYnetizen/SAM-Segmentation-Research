# 公共脚本（组长 PM）

- `split_dataset.py`：导出目录 -> train/val/test 划分
- `evaluation/evaluate.py`：GT vs 预测目录 -> metrics JSON；不复制，脚本放 `evaluation/`
- `make_report_tables.py`：多组 metrics JSON -> Markdown 对比表

这两个类别的脚本都应是「输入输出路径明确、可重复执行」的 CLI，避免手改代码跑实验。
