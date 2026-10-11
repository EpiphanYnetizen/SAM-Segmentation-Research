"""Gradio 分割 demo 骨架。

当前先占用文件与 CLI，不伪装成已跑通；SAM predictor 由 model/zero_shot_inference.py 提供。
"""
from __future__ import annotations

import argparse
from pathlib import Path

import gradio as gr
import numpy as np
from PIL import Image


def render_mask(input_image: np.ndarray) -> np.ndarray:
    # TODO(PM): 替换为真实 SAM 推理
    return np.zeros((*input_image.shape[:2], 1), dtype=np.uint8)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", type=Path, default=Path("checkpoints/sam_vit_b_01ec64.pth"))
    args = parser.parse_args()

    demo = gr.Interface(
        fn=render_mask,
        inputs=gr.Image(type="numpy"),
        outputs=gr.Image(type="numpy"),
        title="SAM Segmentation Demo",
    )
    demo.launch()


if __name__ == "__main__":
    main()
