"""随机划分 train/val/test。

约定输入目录包含 images/ 和 masks/，文件名一一对应。
输出 data/splits/{train,val,test}/{images,masks}。
"""
from __future__ import annotations

import argparse
import shutil
from pathlib import Path

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def split(
    data_dir: Path,
    out_dir: Path,
    ratios: tuple[float, float, float] = (0.7, 0.1, 0.2),
    seed: int = 42,
) -> None:
    import random

    rng = random.Random(seed)
    images = sorted(
        path
        for path in (data_dir / "images").glob("*")
        if path.is_file() and path.suffix.lower() in IMAGE_EXTS
    )
    if not images:
        raise SystemExit(f"{data_dir / 'images'} 里没有图片")

    missing_masks = [
        image.name
        for image in images
        if not (data_dir / "masks" / f"{image.stem}.png").is_file()
    ]
    if missing_masks:
        raise SystemExit(
            "以下图片缺少同名 mask: " + ", ".join(missing_masks[:10])
        )

    rng.shuffle(images)
    n = len(images)
    n_train = round(n * ratios[0])
    n_val = round(n * ratios[1])
    parts = {
        "train": images[:n_train],
        "val": images[n_train : n_train + n_val],
        "test": images[n_train + n_val :],
    }

    for split_name, files in parts.items():
        for kind in ("images", "masks"):
            dst_dir = out_dir / split_name / kind
            dst_dir.mkdir(parents=True, exist_ok=True)
        for img in files:
            shutil.copy2(img, out_dir / split_name / "images" / img.name)
            mask = data_dir / "masks" / f"{img.stem}.png"
            if mask.exists():
                shutil.copy2(mask, out_dir / split_name / "masks" / mask.name)
        print(f"{split_name}: {len(files)}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, default=Path("data/exports"))
    parser.add_argument("--out", type=Path, default=Path("data/splits"))
    args = parser.parse_args()
    split(args.data_dir, args.out)


if __name__ == "__main__":
    main()
