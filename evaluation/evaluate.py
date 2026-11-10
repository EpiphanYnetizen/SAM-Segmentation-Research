"""按同名 mask 评估 GT 与预测。

匹配数必须大于 0，否则直接报错退出，避免生成 n=0 的“全零指标”被误读。
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image

try:
    from .metrics import compute_metrics
except ImportError:
    from metrics import compute_metrics


def find_masks(root: Path, role: str) -> dict[str, Path]:
    if not root.is_dir():
        raise SystemExit(f"{role} 目录不存在: {root}")
    masks_dir = root / "masks"
    files = sorted((masks_dir if masks_dir.is_dir() else root).glob("*.png"))
    if not files:
        raise SystemExit(f"{role} 目录里没有 PNG mask: {masks_dir if masks_dir.is_dir() else root}")
    return {p.stem: p for p in files}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--gt", type=Path, default=Path("data/splits/val"))
    parser.add_argument("--pred", type=Path, default=Path("outputs/zero_shot"))
    parser.add_argument("--out", type=Path, default=Path("outputs/zero_shot_metrics.json"))
    args = parser.parse_args()

    gt_map = find_masks(args.gt, "GT")
    pred_map = find_masks(args.pred, "预测")
    common = sorted(set(gt_map) & set(pred_map))
    if not common:
        raise SystemExit(
            "GT 与预测没有任何同名 mask，无法评测。\n"
            f"  GT 示例: {', '.join(sorted(gt_map)[:5])}\n"
            f"  预测示例: {', '.join(sorted(pred_map)[:5])}\n"
            "检查 --pred 是否指向 outputs/<run>（直接含 PNG），以及文件名是否与 GT 一致。"
        )
    if len(common) < len(gt_map):
        print(f"警告: {len(gt_map) - len(common)} 张 GT 没有对应预测，已跳过")

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
