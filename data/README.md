# 数据与标注（组员 A）

把自采图片放进 `raw/`，标注导出的 mask 放进 `exports/`。类别由 `categories.yaml` 统一维护，其他成员只读。

## 目录

```
data/
  raw/                  # 原始手机拍摄图（git 忽略）
  exports/              # 标注后按 masks/ 树组织
    images/xxx.jpg
    masks/xxx.png       # 单通道，0 背景，1..N 类别
  annotations/          # Label Studio 原始导出（git 忽略）
  splits/               # 由 scripts/split_dataset.py 生成
  categories.yaml       # 类别清单（手工维护）
```

## 类别约定

- 0 固定为背景；1..N 为前景类别。
- 建议首期 4 类：`meat`、`fish`、`vegetable`、`rice`，可替换为你们真正采集的类。
- 每类建议 40-60 张真实照片，先保闭环再扩容。

## 标注步骤

1. 本地或 Docker 启动 Label Studio。
2. 用 brush/rectangle 标出 mask 模板。
3. 导出 PNG mask，统一成 `images-id.png`，放进 `exports/masks/`。
4. 用 `scripts/convert_masks.py` 把 mask 按类别拆成树，或直接按 0..N 约定保存。
