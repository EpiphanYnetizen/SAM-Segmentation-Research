# 可视化 Demo（组长）

Gradio 演示闭环：上传图片 -> 点 / 框提示 -> 输出分割 mask。

## 当前状态

`main.py` 已完成 CLI、界面与参数框架，但 `render_mask()` 当前返回全零，尚未接入真实 SAM 推理，请勿视为已完成。

## 启动

```bash
pip install -r app/requirements.txt
python app/main.py --checkpoint checkpoints/sam_vit_b_01ec64.pth
# 浏览器访问 http://localhost:7860
```

## 待实现

1. 将 `render_mask()` 替换为真实 SAM 推理，复用 `model/zero_shot_inference.py` 的 `load_predictor`。
2. 增加模型切换：未提供 `--lora-dir` 时使用 zero-shot，提供时使用微调模型。
3. Docker 环境需传入 `--host 0.0.0.0`（详见 [`../docker/README.md`](../docker/README.md)）。
