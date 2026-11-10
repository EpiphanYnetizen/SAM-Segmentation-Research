# app

当前 `main.py` 是最小 Gradio 演示，正式 UI 设计见 [`../docs/app-design.md`](../docs/app-design.md)。

## 启动

```bash
pip install -r app/requirements.txt
python app/main.py --checkpoint checkpoints/sam_vit_b_01ec64.pth
```

浏览器访问 <http://localhost:7860>。

## 状态

`render_mask()` 目前仍返回全零，尚未接入真实 SAM 推理。接入方式和正式 Vue + FastAPI 方案见 [`../docs/app-design.md`](../docs/app-design.md)。
