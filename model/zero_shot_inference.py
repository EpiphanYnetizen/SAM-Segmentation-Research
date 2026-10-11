"""SAM zero-shot 推理（提示来自每个 GT mask 的中心点）。

设计说明：SAM 本身不输出类别。为了能直接与类别 GT 对齐评测，
这里对每个 GT mask 的中心做一次点提示，把预测 mask 归入该类别。
这仍然是 zero-shot：模型权重不做任何训练。

用法:
    python model/zero_shot_inference.py \
      --checkpoint checkpoints/sam_vit_b_01ec64.pth \
      --data-dir data/splits/val \
      --out outputs/zero_shot
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import cv2
import numpy as np
from PIL import Image


def load_predictor(checkpoint: Path, model_type: str, device: str):
    try:
        from segment_anything import SamPredictor, sam_model_registry
    except ImportError as exc:
        raise SystemExit(
            "缺少 segment-anything，先执行: pip install -r model/requirements.txt"
        ) from exc

    sam = sam_model_registry[model_type](checkpoint=str(checkpoint))
    sam.to(device=device)
    return SamPredictor(sam)


def infer_one(
    image_path: Path,
    mask_path: Path,
    predictor,
) -> np.ndarray:
    image = cv2.cvtColor(cv2.imread(str(image_path)), cv2.COLOR_BGR2RGB)
    predictor.set_image(image)
    gt = np.asarray(Image.open(mask_path).convert("L"), dtype=np.uint8)
    out = np.zeros_like(gt)

    from scipy import ndimage

    for label in sorted({int(x) for x in np.unique(gt) if x != 0}):
        cls = (gt == label).astype(np.uint8)
        labeled, n = ndimage.label(cls)
        for inst in range(1, n + 1):
            ys, xs = np.nonzero(labeled == inst)
            if len(xs) == 0:
                continue
            point = np.array([[int(xs.mean()), int(ys.mean())]])
            masks, scores, _ = predictor.predict(
                point_coords=point,
                point_labels=np.array([1]),
                multimask_output=False,
            )
            out[masks[0] > 0] = label
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--model-type", default="vit_b")
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--data-dir", type=Path, default=Path("data/splits/val"))
    parser.add_argument("--out", type=Path, default=Path("outputs/zero_shot"))
    args = parser.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)
    predictor = load_predictor(args.checkpoint, args.model_type, args.device)

    images = sorted((args.data_dir / "images").glob("*"))
    results = {}
    for image_path in images:
        mask_path = args.data_dir / "masks" / f"{image_path.stem}.png"
        if not mask_path.exists():
            results[image_path.stem] = "skip: no gt mask"
            continue
        pred = infer_one(image_path, mask_path, predictor)
        Image.fromarray(pred).save(args.out / f"{image_path.stem}.png")
        results[image_path.stem] = "ok"

    (args.out.parent / f"{args.out.name}_manifest.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"done: {sum(v == 'ok' for v in results.values())}/{len(images)}")


if __name__ == "__main__":
    main()
