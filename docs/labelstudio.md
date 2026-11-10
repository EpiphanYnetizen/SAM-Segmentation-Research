# Label Studio 标注流程（组员 A）

本文只讲组员 A 怎么把照片变成 `data/exports/{images,masks}`。类别定义和标注取舍规则见 [`../data/README.md`](../data/README.md)，目录契约见 [`data-protocol.md`](./data-protocol.md)。

## 0. 目录约定

Label Studio 的数据库、上传副本和导出 JSON 都不进入 Git 仓库，统一放在仓库外的 `project/tools/labelstudio`：

```text
project/
  envs/
    labelstudio/                 # Label Studio 独立 Python 环境
  tools/
    labelstudio/
      images/                    # 待标注原图
      data/                      # Label Studio 数据库与 media
      exports/                   # 导出的 JSON
  SAM-Segmentation-Research/     # Git 仓库
    scripts/start_labelstudio.bat
    data/exports/{images,masks}  # 转换后的训练数据
```

不要把这些内容放进仓库的 `.venv` 或 `data/annotations`。Label Studio 依赖 Django 等组件，和项目训练环境分开，避免版本冲突。

## 1. 安装 Label Studio（只做一次）

在 `project` 目录下执行：

```powershell
py -3.10 -m venv envs\labelstudio
envs\labelstudio\Scripts\pip.exe install --upgrade pip
envs\labelstudio\Scripts\pip.exe install label-studio
```

仓库根目录的 `.venv` 只装训练依赖，不装 Label Studio。

## 2. 启动

在仓库根目录双击：

```text
scripts\start_labelstudio.bat
```

脚本会自动创建 `project/tools/labelstudio/{images,data,exports}`，并检查 `project/envs/labelstudio` 是否已安装。

浏览器打开 <http://localhost:8080>。首次使用在本地注册一个账号即可，数据只保存在本机。

启动脚本已经设置好两个环境变量：

- `LABEL_STUDIO_LOCAL_FILES_SERVING_ENABLED=true`
- `LABEL_STUDIO_LOCAL_FILES_DOCUMENT_ROOT=project/tools/labelstudio/images`

因此 Label Studio 可以直接读取 `tools/labelstudio/images` 下的原图。

## 3. 放照片

把待标注照片复制到 `project/tools/labelstudio/images/`。命名示例：

```text
canteen_20261020_001.jpg
canteen_20261020_002.jpg
```

只使用 `.jpg` 或 `.png`，不要使用 `.heic`、`.raw`、`.dng`。照片要求见 [`../data/README.md`](../data/README.md)。

## 4. 新建项目

1. 在 Label Studio 中点击 **Create Project**。
2. 打开 **Labeling Interface**，切换到 **Code**，粘贴下面的配置：

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

说明：

- `value` 必须和 [`../data/categories.yaml`](../data/categories.yaml) 的 `name` 完全一致，转换脚本按这个字段映射像素值。
- 推荐使用多边形。菜品边界不规则时，多边形比矩形更贴近真实轮廓。
- 如果某张图确实无法判断，才使用 `ignore`，转换后像素值为 255，评测会跳过。
- 如果更习惯画笔，把 `<polygonlabels ...>` 换成 `<brushlabels name="label" toName="image">`，标签行不变；不要同时启用两套控件，避免同一张图混用两种标注方式。

## 5. 导入图片

在项目页点击 **Import**，选择 **Local Files**，路径填：

```text
D:\learning\深度学习\project\tools\labelstudio\images
```

如果路径不同，以本机实际路径为准。导入后点击 **Sync**，任务列表会出现所有照片。

也可以直接拖拽上传。上传方式会把图片复制到 `tools/labelstudio/data/media/upload`，转换时额外加 `--ls-data-dir` 参数即可。

## 6. 标注

对每张图：

1. 选择对应类别。
2. 沿食物可见边界依次点击，闭合多边形。
3. 一张图的所有实例标完后，再处理下一张。
4. 同一张图必须由同一个人一次标完，不要两个人各标一半。

具体取舍：

- 面积小于整图 0.5%、或任一边小于 20px 的实例不标。
- 被遮挡且可见部分不足一半的实例不标。
- 粘连时只标可见轮廓，不人为补全。
- 非食物（餐具、包装、桌面）不标，保持背景 0。
- 不属于 1-4 类的食物标 `other`，不能标成背景。

## 7. 导出 JSON

标注完成后：

1. 项目页点击 **Export**。
2. 选择 **JSON**，不要选 JSON-MIN、CSV 或 COCO。
3. 保存到 `project/tools/labelstudio/exports/`，例如 `project-20261020.json`。

JSON 中每条任务包含 `data.image`、`annotations[].result[]`，转换脚本依赖这些字段。

## 8. 转成 PNG mask

回到仓库根目录执行：

```powershell
python scripts\labelstudio_to_masks.py --export ..\tools\labelstudio\exports\project-20261020.json --image-dir ..\tools\labelstudio\images --out data\exports
```

如果是上传方式（图片在 Label Studio 的 media 目录），改用：

```powershell
python scripts\labelstudio_to_masks.py --export ..\tools\labelstudio\exports\project-20261020.json --image-dir ..\tools\labelstudio\images --ls-data-dir ..\tools\labelstudio\data --out data\exports
```

常用参数：

| 参数 | 作用 |
|---|---|
| `--overwrite` | 覆盖已有图片和 mask；修改标注后重新导出时使用 |
| `--skip-empty` | 跳过没有任何区域的图片 |
| `--unknown-label other` | 未知标签归到 `other`，默认直接报错 |

输出：

```text
data/exports/images/canteen_20261020_001.jpg
data/exports/masks/canteen_20261020_001.png
```

mask 是单通道 `uint8`：`0` 背景，`1` meat，`2` fish，`3` vegetable，`4` rice，`5` other，`255` ignore。

## 9. 校验与划分

```powershell
python scripts\validate_dataset.py --data-dir data\exports
python scripts\split_dataset.py --data-dir data\exports --out data\splits
```

校验必须显示 `校验通过`。划分按图片进行，同一张图的 image 和 mask 会进入同一个 split。

## 10. 常见问题

| 现象 | 原因 | 处理 |
|---|---|---|
| 找不到图片 | `--image-dir` 不对，或图片是上传到 Label Studio 的 | 检查路径；上传方式加 `--ls-data-dir` |
| 未知标签 | 标签值不在 `categories.yaml` | 改 Label Studio 配置或补类别，不要静默改成背景 |
| 同名图片 | 不同子目录下有同名文件 | 重命名后再导入 |
| mask 已存在 | 默认不覆盖 | 确认要重跑时加 `--overwrite` |
| 标注包含图片旋转 | Label Studio 中旋转过图片 | 关闭旋转，重新导出 |
| 输出全背景 | 任务没有区域，或区域类型不支持 | 查看脚本警告；必要时加 `--skip-empty` |

## 11. 测试集特别规定

测试集 GT 必须 100% 人工标注。禁止用 SAM 输出、自动 mask 或其他模型结果直接作为测试集 GT；允许用模型结果做辅助预览，但最终每个像素必须由人确认。否则测试集不再独立，评测结果无效。
