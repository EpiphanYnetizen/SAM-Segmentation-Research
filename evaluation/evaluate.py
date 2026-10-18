"""按同名 mask 评估 GT 与预测。"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image

from metrics import compute_metrics


def find_masks(root: Path) -> dict[str, Path]:
    masks = list(root.glob("masks/*.png"))
    if not masks and (root / "masks").is_dir() is False:
        masks = list(root.glob("*.png"))
    return {p.stem: p for p in masks}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--gt", type=Path, default=Path("data/splits/val"))
    parser.add_argument("--pred", type=Path, default=Path("outputs/zero_shot"))
    parser.add_argument("--out", type=Path, default=Path("outputs/zero_shot_metrics.json"))
    args = parser.parse_args()

    gt_map = find_masks(args.gt)
    pred_map = find_masks(args.pred)
    common = sorted(set(gt_map) & set(pred_map))
    per_image = {}
    for name in common:
        gt = np.asarray(Image.open(gt_map[name]).convert("L"), dtype=np.uint8)
        pred = np.asarray(Image.open(pred_map[name]).convert("L"), dtype=np.uint8)
        per_image[name] = compute_metrics(pred, gt)

    agg: dict[str, float] = {}
    if common:
        keys = ["mIoU", "meanDice", "meanBoundaryF1"]
        agg = {k: float(np.mean([per_image[n][k] for n in common])) for k in keys}
    payload = {"n": len(common), "summary": agg, "per_image": per_image}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
