# app

当前 `main.py` 是 Gradio 演示界面，已接入 SAM 点提示推理。正式的 Vue + FastAPI
方案见 [`../docs/app-design.md`](../docs/app-design.md)，仍是设计稿。

## 启动

```bash
pip install -r app/requirements.txt
python app/main.py --checkpoint checkpoints/sam_vit_b_01ec64.pth
```

浏览器访问 <http://localhost:7860>。上传图片后，直接点图中的菜品，或输入 x/y
坐标后点“分割”。点图会自动把坐标填入 x/y，并返回叠加后的 mask。

可选参数：

```bash
python app/main.py --lora-dir checkpoints/lora/encoder/<run_id>
python app/main.py --decoder-ckpt checkpoints/lora/mask_decoder/<run_id>/mask_decoder.pth
```

## 说明

1. 启动时用 `model/sam_runtime.py` 的 `load_predictor()` 加载一次 SAM，可用
   `--lora-dir` / `--decoder-ckpt` 指定微调权重；
2. 点击坐标交给 `predict_with_prompt()`，返回布尔 mask 和 score；
3. 类别下拉框只决定叠加颜色，SAM 本身不分类。真正的类别识别需要另加分类头。

`main.py` 会把 `model/` 加入 `sys.path`，因此可以从仓库根目录直接运行：

```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "model"))
```

PyCharm 里如果 `sam_runtime` 显示红色，右键 `model` 目录 →
`Mark Directory as` → `Sources Root`。
