"""校验 data/exports 的图片与 mask 是否配套、尺寸一致、类别合法。

用法:
    python scripts/validate_dataset.py --data-dir data/exports
"""
from __future__ import annotations

import argparse
import hashlib
from collections import Counter
from pathlib import Path

import numpy as np
from PIL import Image

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
ALLOWED_LABELS = {0, 1, 2, 3, 4, 5, 255}
LABEL_NAMES = {
    0: "background",
    1: "meat",
    2: "fish",
    3: "vegetable",
    4: "rice",
    5: "other",
    255: "ignore",
}


def file_md5(path: Path) -> str:
    digest = hashlib.md5()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, default=Path("data/exports"))
    parser.add_argument("--max-report", type=int, default=20)
    args = parser.parse_args()

    root: Path = args.data_dir
    image_dir = root / "images"
    mask_dir = root / "masks"
    errors: list[str] = []
    warnings: list[str] = []

    if not image_dir.is_dir():
        errors.append(f"缺少图片目录: {image_dir}")
    if not mask_dir.is_dir():
        errors.append(f"缺少标注目录: {mask_dir}")

    images = (
        sorted(p for p in image_dir.glob("*") if p.suffix.lower() in IMAGE_EXTS)
        if image_dir.is_dir()
        else []
    )
    masks = sorted(mask_dir.glob("*.png")) if mask_dir.is_dir() else []

    if not images:
        errors.append(f"没有可用图片: {image_dir}")

    image_stems = {p.stem for p in images}
    mask_stems = {p.stem for p in masks}

    for stem in sorted(image_stems - mask_stems)[: args.max_report]:
        errors.append(f"缺 mask: {stem}.png")
    for stem in sorted(mask_stems - image_stems)[: args.max_report]:
        errors.append(f"多出 mask（没有对应图片）: {stem}.png")

    hashes: dict[str, list[str]] = {}
    for path in images:
        hashes.setdefault(file_md5(path), []).append(path.name)
    for names in hashes.values():
        if len(names) > 1:
            errors.append(f"图片内容重复: {', '.join(names)}")

    label_counts: Counter[int] = Counter()
    checked = 0
    for image_path in images:
        mask_path = mask_dir / f"{image_path.stem}.png"
        if not mask_path.exists():
            continue
        checked += 1
        try:
            with Image.open(image_path) as image:
                image_size = image.size
            with Image.open(mask_path) as mask_image:
                mask_size = mask_image.size
                mask_mode = mask_image.mode
                mask = np.asarray(mask_image)
        except Exception as exc:
            errors.append(f"{image_path.name}: 读取失败 ({exc})")
            continue

        if image_size != mask_size:
            errors.append(
                f"{image_path.name}: 尺寸不一致 image={image_size} mask={mask_size}"
            )
        if mask_mode not in ("L", "P"):
            warnings.append(f"{mask_path.name}: mode={mask_mode}，建议单通道 uint8")
        if mask.ndim != 2:
            errors.append(f"{mask_path.name}: 应为单通道，实际 shape={mask.shape}")
            continue

        unexpected = sorted(set(int(v) for v in np.unique(mask)) - ALLOWED_LABELS)
        if unexpected:
            errors.append(f"{mask_path.name}: 非法类别值 {unexpected}")

        counts = np.bincount(mask.reshape(-1), minlength=256)
        for label in range(256):
            if counts[label]:
                label_counts[label] += int(counts[label])

    print(f"图片 {len(images)} 张，mask {len(masks)} 个，成功配对 {checked} 组")
    total = sum(label_counts.values())
    if total:
        print("像素占比：")
        for label in sorted(label_counts):
            name = LABEL_NAMES.get(label, "未知")
            print(f"  {label:>3} {name:<11} {label_counts[label] / total:6.2%}")

    if warnings:
        print(f"\n警告 {len(warnings)} 条：")
        for item in warnings[: args.max_report]:
            print(f"  - {item}")

    if errors:
        print(f"\n错误 {len(errors)} 条：")
        for item in errors[: args.max_report]:
            print(f"  - {item}")
        if len(errors) > args.max_report:
            print(f"  ... 另有 {len(errors) - args.max_report} 条未显示")
        return 1

    print("\n校验通过")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
