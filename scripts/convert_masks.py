"""把标注好的 PNG mask 整理成 0..N 类别树。

用法示例:
    python scripts/convert_masks.py --src data/exports/masks --dst data/exports/masks

会在 --dst 下把原始导出备份成 <name>_raw.png；已备份过的文件跳过，可重复执行。

当前版本假定 mask 已经是单通道、每像素等于类别编号(0..N)。
如果 Label Studio 导出的是实例 id 而非类别，先手工把实例映射到 categories.yaml。
"""
from __future__ import annotations

import argparse
import shutil
from pathlib import Path

import numpy as np
from PIL import Image


def normalize_mask(src: Path, dst: Path, category_ids: set[int]) -> None:
    arr = np.asarray(Image.open(src).convert("L"), dtype=np.uint8)
    out = np.zeros_like(arr)
    for cid in category_ids:
        out[arr == cid] = cid
    out[arr == 255] = 255
    Image.fromarray(out).save(dst)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--src", type=Path, default=Path("data/exports/masks"))
    parser.add_argument("--dst", type=Path, default=Path("data/exports/masks_normalized"))
    parser.add_argument("--category-ids", default="1,2,3,4,5")
    args = parser.parse_args()

    cids = {int(x) for x in args.category_ids.split(",") if x}
    args.dst.mkdir(parents=True, exist_ok=True)

    files = sorted(p for p in args.src.glob("*.png") if not p.stem.endswith("_raw"))
    for src in files:
        backup = args.dst / f"{src.stem}_raw.png"
        if backup.exists():
            continue
        shutil.copy2(src, backup)
        normalize_mask(src, args.dst / src.name, cids)

    print(f"normalized {len(files)} masks -> {args.dst}")


if __name__ == "__main__":
    main()
