# 数据与标注（组员 A · 曹庆科）

本模块负责将采集的照片转换为模型可直接使用的 `images/` 与 `masks/`，并划分为 train/val/test。
本模块产出是组员 B 与组长的上游输入，规则如需调整，**变更前须在全组同步**。

## 目录

```text
data/
  raw/                  # 可选归档；主标注目录在仓库外 tools/labelstudio/images
  exports/              # 标注产物，下游只读
    images/xxx.jpg
    masks/xxx.png       # 单通道 uint8：0 背景，1..5 类别，255 ignore
  annotations/          # 其他标注工具的原始导出（git 忽略；Label Studio 不放这里）
  splits/               # 由 scripts/split_dataset.py 生成
  categories.yaml       # 类别清单，唯一真源
```

## 交付物

| 交付 | 路径 | 消费方 |
|---|---|---|
| 待标注照片 | `project/tools/labelstudio/images/`（仓库外，不入库） | Label Studio |
| 标注产物 | `data/exports/images/` 与 `data/exports/masks/` | 组长验收 |
| 数据集划分 | `data/splits/{train,val,test}/` | 组员 B 训练、本模块评测 |
| 指标结果 | `outputs/*_metrics.json` | 组长汇总对比表 |

## 照片格式要求

照片统一放 `project/tools/labelstudio/images/`，不要直接提交到仓库。`data/raw/` 仅用于可选归档，且已被 git 忽略。

- 格式：`.jpg`（优先）或 `.png`；不使用 iPhone 默认的 `.heic`、`.raw`、`.dng`。
- 尺寸：保留原图，或统一缩放至长边 1024-2048；同一批次避免混合横竖比例。
- 命名：`<场景>_<日期>_<序号>.jpg`，例如 `canteen_20261020_001.jpg`。
- 拍摄：不使用滤镜、美颜、裁剪或拼接；同一菜品不连续拍摄大量近似图。
- 不拍摄人脸。
- 单张照片尽量包含 3-8 个可标注食物实例，以提升单位标注成本下的样本密度。
- 入库前筛选：模糊、重复、仅拍到桌面的样本应剔除。

## 类别体系

类别定义以 `data/categories.yaml` 为准，本文件仅作说明。

- `0` 背景；`1-4` 为评测目标类；`5 other` 为兜底类；`255 ignore` 不参与计算。
- 总量建议 80-120 张（4 类合计），单图 3-8 个实例，实际可得到约 400-600 个标注实例；先完成最小闭环，再扩充规模。

### 目标类之外的食物

`meat` / `fish` / `vegetable` / `rice` 是本项目的评测目标类，不等同于「数据中只允许出现这些物体」。
食堂场景会自然包含鸡蛋、豆腐、土豆丝、汤、水果等，处理规则如下：

- 明显为食物但不属于 1-4 类 → 标注为 `5 other`。
- 非食物（餐具、包装袋、饮料瓶、纸巾、桌布、桌面）→ 不标注，作背景 0。
- **不得将「其他食物」标注为背景。** 否则会向模型传递错误信号，使部署时将其误判为背景，该偏差来自标注而非模型。
- 混合菜（青椒炒肉丝、番茄炒蛋等）不应强行拆分，整份按主导属性归类，难以判断时标 `other`。
- 同一菜品在所有照片中应保持同一类别，对照表如下：

| 菜名 | 类别 |
|---|---|
| 红烧肉 | meat |
| 清蒸鱼 | fish |
| 炒青菜 | vegetable |
| 米饭 | rice |
| 番茄炒蛋 | other |

> 上表为示例，按实际采集菜品调整。

### 新增类别条件

- 某类食物占比超过 10%（如鸡蛋、土豆）→ 不再归入 `other`，新增为类别 6。
- `other` 占比超过 20% → 表明类别体系需要调整（可改为按主食 / 荤菜 / 素菜划分，而非按食材）。

### 评测口径（报告中需明确）

- 当前脚本忽略 `0` 背景与 `255 ignore`，对剩余前景类取平均。
- 如报告要求「主指标只报 1-4 类，`other` 单列」，需在结果阶段按类拆分。
- `255 ignore` 仅用于确实无法判断的区域，不得作为降低标注成本的批量手段。

## 标注取舍规则

原则：**不追求标注完整，追求标注一致**。同一张图由不同人重标，结果应基本一致。

- 上限：单张图最多 15 个实例，超出时按面积取前 15 个，其余不标。
- 下限：面积不足整图 0.5%，或任一边小于 20px 的实例不标。
- 遮挡：被其他食物遮挡且可见部分不足一半者不标。
- 不确定：标注为 255，评测自动忽略，不计算为错误。
- 粘连：实例难以区分时只标可见轮廓，不人为补全。
- 稀疏样本：单图不足 3 个实例，归入「稀疏 / 失败样本」，不进入主训练集。
- 标注分工：同一张图的所有 mask 必须由同一人一次完成，避免不同标注风格引入噪声。

Label Studio 中未覆盖区域自动视为背景 0，因此「不标」即等同于「作背景」，无需额外处理。

## 标注步骤

完整操作见 [`../docs/labelstudio.md`](../docs/labelstudio.md)。最小流程：

1. 在独立环境安装 Label Studio：`pip install label-studio`，不要装进项目 `.venv`。
2. 把照片放入 `project/tools/labelstudio/images/`，在仓库根目录双击 `scripts/start_labelstudio.bat` 启动。
3. 按 [`../docs/labelstudio.md`](../docs/labelstudio.md) 的配置建立项目，使用多边形逐类标注。
4. 导出 **JSON** 到 `project/tools/labelstudio/exports/`。
5. 转成 PNG mask：

```powershell
python scripts\labelstudio_to_masks.py --export ..\tools\labelstudio\exports\project.json --image-dir ..\tools\labelstudio\images --out data\exports
```

6. 校验并划分：

```powershell
python scripts\validate_dataset.py --data-dir data\exports
python scripts\split_dataset.py --data-dir data\exports --out data\splits
```

> 划分必须按图片维度进行。同一张图的 mask 不得分散到 train 与 test，否则构成数据泄漏。

## 下一步

完成标注与划分后，按 [`../evaluation/README.md`](../evaluation/README.md) 执行评测。
