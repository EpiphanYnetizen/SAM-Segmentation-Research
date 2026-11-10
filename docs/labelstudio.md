# 标注导出与转换（组员 A）

本文只说明一件事：你在 Label Studio 里标完之后，怎么把导出的 JSON 转成仓库需要的 `data/exports/{images,masks}`。

Label Studio 装在哪里、照片放在哪里、用 pip 还是 Docker 启动，由你按自己的习惯安排，仓库不做限制。仓库只接收转换后的结果。

## 1. 先确认类别

类别以 [`../data/categories.yaml`](../data/categories.yaml) 为准：

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

## 2. 在 Label Studio 中标注

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

标注取舍规则见 [`../data/README.md`](../data/README.md)。核心原则是**不追求标得最多，追求同一个人重标时结果一致**。

## 3. 导出 JSON

标注完成后，在项目页选择 **Export → JSON**。

- 不要选 JSON-MIN、CSV 或 COCO。
- 导出文件放在哪里都可以，只要下一步的 `--export` 指得到。
- 图片如果是拖拽上传进 Label Studio 的，转换时需要额外知道 Label Studio 的 data 目录；这个目录就是启动时 `--data-dir` 指向的位置。

## 4. 转成 PNG mask

在仓库根目录执行：

```powershell
python scripts\labelstudio_to_masks.py --export <导出的.json> --image-dir <原图目录> --out data\exports
```

例如：

```powershell
python scripts\labelstudio_to_masks.py --export D:\my-annotations\project.json --image-dir D:\my-photos --out data\exports
```

如果图片是上传进 Label Studio 的，加 `--ls-data-dir`：

```powershell
python scripts\labelstudio_to_masks.py --export D:\my-annotations\project.json --image-dir D:\my-photos --ls-data-dir D:\label-studio-data --out data\exports
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

脚本会处理：

- 多边形、画笔 RLE、矩形三种区域。
- 标签名到像素值的映射，中文名和英文名都可以。
- 图片 EXIF 方向，避免 mask 和原图上下颠倒。
- 同名图片、未知标签、旋转标注等异常会直接报错，不会静默写错数据。

输出：

```text
data/exports/images/<图片名>.jpg
data/exports/masks/<图片名>.png
```

mask 是单通道 `uint8`：`0` 背景，`1-5` 类别，`255` ignore。

## 5. 校验与划分

```powershell
python scripts\validate_dataset.py --data-dir data\exports
python scripts\split_dataset.py --data-dir data\exports --out data\splits
```

校验必须显示 `校验通过`。划分按图片进行，同一张图的 image 和 mask 会进入同一个 split。

## 6. 测试集规定

测试集 GT 必须 100% 人工标注。禁止用 SAM 输出、自动 mask 或其他模型结果直接作为测试集 GT；允许用模型结果做辅助预览，但最终每个像素必须由人确认。否则测试集不再独立，评测结果无效。
