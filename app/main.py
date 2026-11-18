"""Gradio 演示界面：点图或输入坐标，调用 SAM 生成 mask。"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import cv2
import gradio as gr
import numpy as np
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "model"))

from sam_runtime import load_predictor, predict_with_prompt  # noqa: E402


PREDICTOR = None
LAST_IMAGE_HASH = None
CATEGORIES = []
COLOR_BY_ID = {}


def load_categories() -> list[tuple[int, str, tuple[int, int, int]]]:
    """读取 data/categories.yaml；读不到时退回四类默认值。"""
    fallback = [
        (1, "肉块", (220, 20, 60)),
        (2, "鱼块", (30, 144, 255)),
        (3, "青菜", (34, 139, 34)),
        (4, "米饭", (255, 215, 0)),
        (5, "其他食物", (255, 165, 0)),
    ]
    path = ROOT / "data" / "categories.yaml"
    if not path.is_file():
        return fallback
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    categories = []
    for raw_id, item in sorted(payload.get("categories", {}).items()):
        if not isinstance(item, dict):
            continue
        color = tuple(int(v) for v in item.get("color", (255, 0, 0)))
        categories.append((int(raw_id), str(item.get("cn", raw_id)), color))
    return categories or fallback


def set_image_once(image: np.ndarray) -> None:
    """同一张图只跑一次 image encoder，重复点击只重跑 mask decoder。"""
    global LAST_IMAGE_HASH
    image_hash = hash(image.tobytes())
    if image_hash != LAST_IMAGE_HASH:
        PREDICTOR.set_image(image)
        LAST_IMAGE_HASH = image_hash


def overlay_mask(
    image: np.ndarray, mask: np.ndarray, color: tuple[int, int, int]
) -> np.ndarray:
    canvas = image.copy()
    if mask.any():
        blend = canvas[mask].astype(np.float32) * 0.55 + np.array(
            color, dtype=np.float32
        ) * 0.45
        canvas[mask] = blend.astype(np.uint8)
        contours, _ = cv2.findContours(
            mask.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )
        cv2.drawContours(canvas, contours, -1, color, 2)
    return canvas


def render_mask(
    image: np.ndarray, x: float, y: float, category_id: int
) -> tuple[np.ndarray, str]:
    if image is None:
        raise gr.Error("请先上传图片")
    if PREDICTOR is None:
        raise gr.Error("模型尚未加载")

    height, width = image.shape[:2]
    px, py = int(x), int(y)
    if not (0 <= px < width and 0 <= py < height):
        raise gr.Error(f"坐标超出图片范围：图片是 {width}×{height}")

    set_image_once(image)
    mask, score = predict_with_prompt(PREDICTOR, [(px, py)], [1])
    color = COLOR_BY_ID.get(int(category_id), (255, 0, 0))
    result = overlay_mask(image, mask, color)
    status = f"类别: {category_id} | score: {score:.3f} | 前景像素: {int(mask.sum())}"
    return result, status


def on_image_select(
    image: np.ndarray, category_id: int, evt: gr.SelectData
) -> tuple[float, float, np.ndarray, str]:
    x, y = evt.index
    result, status = render_mask(image, x, y, category_id)
    return float(x), float(y), result, status


def clear_result() -> tuple[None, str]:
    return None, ""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--checkpoint",
        type=Path,
        default=ROOT / "checkpoints/sam_vit_b_01ec64.pth",
    )
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--lora-dir", type=Path, help="可选：image encoder LoRA 目录")
    parser.add_argument("--decoder-ckpt", type=Path, help="可选：mask decoder 权重")
    parser.add_argument("--host", default="127.0.0.1", help="Docker 里必须传 0.0.0.0")
    parser.add_argument("--port", type=int, default=7860)
    args = parser.parse_args()

    if not args.checkpoint.is_file():
        raise SystemExit(f"找不到权重 {args.checkpoint}，按 model/README.md 下载后放到 checkpoints/")

    if args.device == "cuda":
        import torch

        if not torch.cuda.is_available():
            print("未检测到 CUDA，改用 CPU")
            args.device = "cpu"

    global PREDICTOR, CATEGORIES, COLOR_BY_ID
    PREDICTOR = load_predictor(
        args.checkpoint,
        model_type="vit_b",
        device=args.device,
        lora_dir=args.lora_dir,
        decoder_ckpt=args.decoder_ckpt,
    )
    CATEGORIES = load_categories()
    COLOR_BY_ID = {category_id: color for category_id, _, color in CATEGORIES}
    choices = [(f"{name} ({category_id})", category_id) for category_id, name, _ in CATEGORIES]

    with gr.Blocks(title="SAM Segmentation Demo") as demo:
        gr.Markdown(
            "## SAM 食堂菜品分割\n"
            "上传图片后，直接点图中的菜品，或在下面输入 x/y 坐标后点“分割”。"
        )
        with gr.Row():
            image_input = gr.Image(type="numpy", label="上传图片")
            image_output = gr.Image(type="numpy", label="分割结果")

        with gr.Row():
            x_input = gr.Number(value=0, precision=0, label="x 坐标")
            y_input = gr.Number(value=0, precision=0, label="y 坐标")
            category_input = gr.Dropdown(
                choices=choices,
                value=CATEGORIES[0][0],
                label="类别（仅用于显示颜色，SAM 不分类）",
            )
            run_button = gr.Button("分割", variant="primary")

        status_output = gr.Textbox(label="结果", interactive=False)

        image_input.select(
            fn=on_image_select,
            inputs=[image_input, category_input],
            outputs=[x_input, y_input, image_output, status_output],
        )
        run_button.click(
            fn=render_mask,
            inputs=[image_input, x_input, y_input, category_input],
            outputs=[image_output, status_output],
        )
        image_input.clear(fn=clear_result, outputs=[image_output, status_output])

    demo.launch(server_name=args.host, server_port=args.port, show_error=True)


if __name__ == "__main__":
    main()
