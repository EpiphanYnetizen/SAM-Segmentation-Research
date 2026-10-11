# 可视化 Demo（组长 PM）

用 Gradio 做最小可演示闭环：上传图片 -> 点/框提示 -> 显示 zero-shot / 微调后的 mask。

## 启动

```bash
pip install -r app/requirements.txt
python app/main.py --checkpoint checkpoints/sam_vit_b_01ec64.pth
```

## 对接

- 推理复用 `model/zero_shot_inference.py` 的 `load_predictor`。
- 模型切换放在 `--lora-dir`，没有时走 zero-shot。
