# app

当前 `main.py` 是 Gradio 界面骨架，**尚未接入推理**。点“提交”会明确报错，
不会返回全零 mask 冒充结果。正式的 Vue + FastAPI 方案见
[`../docs/app-design.md`](../docs/app-design.md)，同样只是设计稿。

## 启动

```bash
pip install -r app/requirements.txt
python app/main.py --checkpoint checkpoints/sam_vit_b_01ec64.pth
```

浏览器访问 <http://localhost:7860>，界面能打开，但提交会提示“尚未接入”。

## 待接入（负责人：组长）

1. 启动时用 `model/sam_runtime.py` 的 `load_predictor()` 加载一次 SAM，可用 `--lora-dir` / `--decoder-ckpt` 指定微调权重；
2. 把界面上传入的点击坐标交给 `predict_with_prompt()`；
3. 返回叠加图与二值 mask，类别由用户在下拉框选择（SAM 只出 mask，不分类）。

接入前需要 `sam_runtime.py` 在 `sys.path` 里，跨目录导入可参考：

```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "model"))
```

## 为什么现在也能启动

骨架阶段先保证 `--checkpoint`、`--host`、`--port` 三个参数和 Docker 入口不变，
接入推理时只改 `render_mask()` 内部，不用动部署配置。
