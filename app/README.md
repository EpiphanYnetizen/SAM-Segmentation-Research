# 可视化 Demo（组长）

Gradio 最小闭环：上传图片 -> 点/框提示 -> 显示分割 mask。

## 现状

`main.py` 目前是**骨架**。CLI、界面和参数都在，但 `render_mask()` 还只返回全零，**没有真正调用 SAM** —— 别当成已跑通。

## 启动

```bash
pip install -r app/requirements.txt
python app/main.py --checkpoint checkpoints/sam_vit_b_01ec64.pth
# 浏览器打开 http://localhost:7860
```

## 还要做什么

1. 把 `render_mask()` 换成真实 SAM 推理，复用 `model/zero_shot_inference.py` 的 `load_predictor`。
2. 加模型切换：没有 `--lora-dir` 走 zero-shot，有就走微调后的模型。
3. 进 Docker 必须 `--host 0.0.0.0`，否则容器外打不开（见 [`../docker/README.md`](../docker/README.md)）。
