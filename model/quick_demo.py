"""单张图片快速验证 SAM，不需要人工标注。

自动模式（SAM 自己找出图中物体）:
    python model/quick_demo.py --image data/raw/xxx.jpg

点提示模式（模拟用户点一下）:
    python model/quick_demo.py --image data/raw/xxx.jpg --point 320 240
"""
from __future__ import annotations

import argparse
from pathlib import Path

import cv2
import numpy as np


def load_sam(checkpoint: Path, model_type: str, device: str):
    try:
        from segment_anything import (
            SamAutomaticMaskGenerator,
            SamPredictor,
            sam_model_registry,
        )
    except ImportError as exc:
        raise SystemExit(
            "缺少 segment-anything，先执行: pip install segment-anything"
        ) from exc

    if device == "cuda":
        import torch

        if not torch.cuda.is_available():
            device = "cpu"
            print("未检测到 CUDA，改用 CPU")

    sam = sam_model_registry[model_type](checkpoint=str(checkpoint))
    sam.to(device=device)
    generator = SamAutomaticMaskGenerator(
        sam,
        points_per_side=12,
        pred_iou_thresh=0.86,
        stability_score_thresh=0.92,
    )
    return SamPredictor(sam), generator


PALETTE = [
    (255, 59, 48),
    (0, 199, 190),
    (255, 204, 0),
    (88, 86, 214),
    (52, 199, 89),
    (255, 149, 0),
]


def color_for(index: int) -> tuple[int, int, int]:
    return PALETTE[index % len(PALETTE)]


def draw(image: np.ndarray, masks: list[np.ndarray]) -> np.ndarray:
    canvas = image.copy()
    overlay = image.copy()
    for index, mask in enumerate(masks):
        color = color_for(index)
        overlay[mask] = color
        contours, _ = cv2.findContours(
            mask.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )
        cv2.drawContours(canvas, contours, -1, color, 3)
    return cv2.addWeighted(overlay, 0.55, canvas, 0.45, 0)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", type=Path, required=True)
    parser.add_argument(
        "--checkpoint", type=Path, default=Path("checkpoints/sam_vit_b_01ec64.pth")
    )
    parser.add_argument("--model-type", default="vit_b")
    parser.add_argument("--device", default="cuda")
    parser.add_argument(
        "--point",
        nargs=2,
        type=int,
        metavar=("X", "Y"),
        help="点提示坐标；省略则自动寻找所有物体",
    )
    parser.add_argument("--out", type=Path, default=Path("outputs/demo"))
    args = parser.parse_args()

    image_bgr = cv2.imread(str(args.image))
    if image_bgr is None:
        raise SystemExit(f"读不到图片: {args.image}")
    image = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)

    predictor, generator = load_sam(args.checkpoint, args.model_type, args.device)

    if args.point:
        predictor.set_image(image)
        masks, scores, _ = predictor.predict(
            point_coords=np.array([args.point]),
            point_labels=np.array([1]),
            multimask_output=True,
        )
        best = int(np.argmax(scores))
        mask_list = [masks[best] > 0]
        print(f"点提示: score={scores[best]:.3f}")
    else:
        results = generator.generate(image)
        results.sort(key=lambda item: item["area"], reverse=True)
        mask_list = [item["segmentation"] for item in results]
        print(f"自动模式: 找到 {len(mask_list)} 个物体")

    args.out.mkdir(parents=True, exist_ok=True)
    mode = "point" if args.point else "auto"
    out_path = args.out / f"{args.image.stem}_sam_{mode}.png"
    cv2.imwrite(
        str(out_path), cv2.cvtColor(draw(image, mask_list), cv2.COLOR_RGB2BGR)
    )
    print(f"已保存: {out_path}")


if __name__ == "__main__":
    main()
