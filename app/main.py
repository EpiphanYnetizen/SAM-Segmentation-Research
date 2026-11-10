"""Gradio 演示界面（尚未接入推理）。

保留界面骨架与启动参数，但不返回伪造的全零 mask：
现在点“提交”会明确报错，避免把空结果当成跑通的证据。

接入方式（负责人：组长）：
    from sam_runtime import load_predictor, predict_with_prompt
启动时加载一次 predictor，把点击坐标传进去即可。
"""
from __future__ import annotations

import argparse
from pathlib import Path

import gradio as gr
import numpy as np


def render_mask(input_image: np.ndarray) -> np.ndarray:
    raise gr.Error("分割推理尚未接入，见 app/README.md 的「待接入」一节")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", type=Path, default=Path("checkpoints/sam_vit_b_01ec64.pth"))
    parser.add_argument("--host", default="127.0.0.1", help="Docker 里必须传 0.0.0.0")
    parser.add_argument("--port", type=int, default=7860)
    args = parser.parse_args()

    if not args.checkpoint.is_file():
        print(f"警告: 找不到权重 {args.checkpoint}，接入推理后会因此启动失败")

    demo = gr.Interface(
        fn=render_mask,
        inputs=gr.Image(type="numpy"),
        outputs=gr.Image(type="numpy"),
        title="SAM Segmentation Demo",
    )
    demo.launch(server_name=args.host, server_port=args.port)


if __name__ == "__main__":
    main()
