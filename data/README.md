# 数据与标注（组员 A · 曹庆科）

本模块负责将采集的照片转换为模型可直接使用的 `images/` 与 `masks/`，并划分为 train/val/test。
本模块产出是组员 B 与组长的上游输入，规则如需调整，**变更前须在全组同步**。

## 目录

```text
data/
  raw/
    .gitkeep            # 占位文件；照片放这里或你自己的目录，内容 git 忽略
  annotations/
    .gitkeep            # 占位文件；Label Studio JSON 可放这里，内容 git 忽略
  exports/
    images/
      .gitkeep          # 占位文件；转换后的原图放这里
    masks/
      .gitkeep          # 占位文件；转换后的 mask 放这里
  splits/               # 由 scripts/split_dataset.py 生成
    .gitkeep
  categories.yaml       # 类别清单，唯一真源
```

`.gitkeep` 只是让 Git 保留空文件夹，不是数据，不要删，也不要把它当图片。

## 路径是固定的

- `data/exports/images/` 和 `data/exports/masks/` 是固定路径。`validate_dataset.py` 和 `split_dataset.py` 默认都读 `data/exports`。
- 如果你把输出目录改成别的名字，必须同时给校验和切分脚本传 `--data-dir` 和 `--out`；后续训练、评测文档默认仍按 `data/exports`，所以**不建议改**。
- `data/annotations/` 只是留底，没有任何脚本读它，名字可以不同；但为了组内一致，建议沿用。
- `data/raw/` 只是归档，脚本不读；照片放你自己的目录也可以。
- `data/splits/` 由脚本生成，不要手动重命名或移动。
- 真实图片、mask、JSON 都不会进 Git，只有 `.gitkeep` 和文档会进 Git。

## 目录里放什么

| 内容 | 放哪 | 是否必须 |
|---|---|---|
| 原始照片 | `data/raw/` 或你自己的目录 | 否 |
| Label Studio 导出的 JSON | `data/annotations/` 或你自己的目录 | 否 |
| 转换后的原图 | `data/exports/images/` | 是 |
| 转换后的 mask | `data/exports/masks/` | 是 |
| 划分结果 | `data/splits/` | 由脚本生成 |

## 交付物

| 交付 | 路径 | 消费方 |
|---|---|---|
| 待标注照片 | 由你自行存放，不要提交到 Git | Label Studio |
| 标注产物 | `data/exports/images/` 与 `data/exports/masks/` | 组长验收 |
| 数据集划分 | `data/splits/{train,val,test}/` | 组员 B 训练、本模块评测 |
| 指标结果 | `outputs/*_metrics.json` | 组长汇总对比表 |

## 照片格式要求

照片放在你自己的目录，不要直接提交到仓库。如果需要在仓库内归档，放 `data/raw/`，该目录已被 git 忽略。

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

## 标注与转换

Label Studio 装在哪里、照片放在哪里、用 pip 还是 Docker 启动，由你按自己的习惯安排，仓库不做限制。仓库只接收转换后的 `data/exports/{images,masks}`。

### 类别

类别以 [`categories.yaml`](./categories.yaml) 为准：

| 像素值 | 标签值 | 含义 |
|---|---|---|
| 0 | 背景 | 不标即可 |
| 1 | `meat` | 肉块 |
| 2 | `fish` | 鱼块 |
| 3 | `vegetable` | 青菜 |
| 4 | `rice` | 米饭 |
| 5 | `other` | 其他食物 |
| 255 | `ignore` | 不确定，评测跳过 |

Label Studio 里的标签值必须和上表的英文名一致，转换脚本按这个名字映射像素值。

### 标注

建议单独建一个环境安装 Label Studio，不要装进项目 `.venv`：

```powershell
pip install label-studio
```

新建项目后，在 **Labeling Interface → Code** 中粘贴：

```xml
<labeling>
  <image name="image" value="$image" zoom="true" zoomControl="true"/>
  <polygonlabels name="label" toName="image" strokeWidth="2">
    <label value="meat" background="#DC143C"/>
    <label value="fish" background="#1E90FF"/>
    <label value="vegetable" background="#228B22"/>
    <label value="rice" background="#FFD700"/>
    <label value="other" background="#FFA500"/>
    <label value="ignore" background="#808080"/>
  </polygonlabels>
</labeling>
```

推荐用多边形。菜品边界不规则时，多边形比矩形更贴近真实轮廓。如果更习惯画笔，把 `<polygonlabels ...>` 换成 `<brushlabels name="label" toName="image">`，标签行不变。不要同一张图混用两种方式。

标注时遵守上一节的取舍规则。核心原则是**不追求标得最多，追求同一个人重标时结果一致**。

### 导出 JSON

标注完成后，在项目页选择 **Export → JSON**。

- 不要选 JSON-MIN、CSV 或 COCO。
- 导出文件放在哪里都可以，只要下一步的 `--export` 指得到。
- 图片如果是拖拽上传进 Label Studio 的，转换时需要额外知道 Label Studio 的 data 目录；这个目录就是启动时 `--data-dir` 指向的位置。

### 转成 PNG mask

在仓库根目录执行：

```powershell
python scripts\labelstudio_to_masks.py --export <导出的.json> --image-dir <原图目录> --out data\exports
```

如果图片是上传进 Label Studio 的，加 `--ls-data-dir`：

```powershell
python scripts\labelstudio_to_masks.py --export <导出的.json> --image-dir <原图目录> --ls-data-dir <Label Studio 的 data 目录> --out data\exports
```

常用参数：

| 参数 | 作用 |
|---|---|
| `--export` | Label Studio 导出的 JSON，必填 |
| `--image-dir` | 原图所在目录 |
| `--ls-data-dir` | Label Studio 的 data 目录，仅上传图片时需要 |
| `--out` | 输出目录，默认 `data/exports` |
| `--overwrite` | 覆盖已有图片和 mask；修改标注后重新导出时使用 |
| `--skip-empty` | 跳过没有任何区域的图片 |
| `--unknown-label other` | 未知标签归到 `other`，默认直接报错 |

脚本支持多边形、画笔 RLE、矩形三种区域，会处理图片 EXIF 方向，并对同名图片、未知标签、旋转标注直接报错。

输出：

```text
data/exports/images/<图片名>.jpg
data/exports/masks/<图片名>.png
```

mask 是单通道 `uint8`：`0` 背景，`1-5` 类别，`255` ignore。

### 校验与划分

```powershell
python scripts\validate_dataset.py --data-dir data\exports
python scripts\split_dataset.py --data-dir data\exports --out data\splits
```

校验必须显示 `校验通过`。划分按图片进行，同一张图的 image 和 mask 会进入同一个 split。

### 测试集规定

测试集 GT 必须 100% 人工标注。禁止用 SAM 输出、自动 mask 或其他模型结果直接作为测试集 GT；允许用模型结果做辅助预览，但最终每个像素必须由人确认。否则测试集不再独立，评测结果无效。

## 下一步

完成标注与划分后，按 [`../evaluation/README.md`](../evaluation/README.md) 执行评测。
