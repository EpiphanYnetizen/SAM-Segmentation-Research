"""把 Label Studio 导出的 JSON 转成逐类别的 PNG mask。

支持的区域类型：
- polygonlabels：多边形，坐标为百分比
- brushlabels：画笔，Label Studio 自定义 RLE
- rectanglelabels：矩形，坐标为百分比

用法::

    python scripts/labelstudio_to_masks.py \\
        --export ../tools/labelstudio/exports/project.json \\
        --image-dir ../tools/labelstudio/images \\
        --out data/exports

输出：
- data/exports/images/<stem>.<ext>：与标注对应的原图副本
- data/exports/masks/<stem>.png：单通道 uint8，0 背景，1..5 类别，255 ignore

约定：
- 标签名从 data/categories.yaml 读取，英文名和中文名都可用。
- 每张图的所有区域画到同一张 mask；后画的区域覆盖先画的区域。
- 默认不覆盖已存在的 mask，确认要重跑时加 --overwrite。
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlsplit

import numpy as np
import yaml
from PIL import Image, ImageDraw, ImageOps

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
MASK_EXTS = {".jpg", ".jpeg", ".png"}


def load_categories(path: Path) -> tuple[dict[str, int], int]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    categories = data.get("categories") or {}
    if not categories:
        raise ValueError(f"{path} 中没有 categories")

    names: dict[str, int] = {}
    for raw_id, meta in categories.items():
        cid = int(raw_id)
        if not 1 <= cid <= 254:
            raise ValueError(f"类别编号必须在 1..254 之间，收到 {cid}")
        name = str(meta["name"]).strip().lower()
        names[name] = cid
        if meta.get("cn"):
            names[str(meta["cn"]).strip().lower()] = cid
        names[str(cid)] = cid

    ignore = int(data.get("ignore", 255))
    for alias in ("ignore", "ignored", "忽略", "不确定", "uncertain"):
        names[alias] = ignore
    return names, ignore


def category_id(label: str, names: dict[str, int], unknown: str) -> int:
    key = str(label).strip().lower()
    if key in names:
        return names[key]
    if unknown == "other":
        for fallback in ("other", "其他食物"):
            if fallback in names:
                return names[fallback]
    if unknown == "ignore":
        for fallback in ("ignore", "忽略"):
            if fallback in names:
                return names[fallback]
    raise ValueError(f"未知标签 {label!r}；可用标签: {', '.join(sorted(names))}")


def load_tasks(paths: list[Path]) -> list[dict]:
    tasks: list[dict] = []
    for path in paths:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
        if isinstance(data, dict):
            data = data.get("tasks", [data])
        if not isinstance(data, list):
            raise ValueError(f"{path} 不是 Label Studio 任务数组")
        tasks.extend(item for item in data if isinstance(item, dict))
    return tasks


def task_image_value(task: dict) -> str:
    data = task.get("data") or {}
    for key in ("image", "img", "photo", "file"):
        value = data.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    for value in data.values():
        if isinstance(value, str) and (
            value.startswith("/data/") or Path(value).suffix.lower() in IMAGE_EXTS
        ):
            return value
    raise ValueError(f"任务 {task.get('id', '?')} 找不到图片路径")


def build_image_index(roots: list[Path]) -> dict[str, list[Path]]:
    index: dict[str, list[Path]] = {}
    for root in roots:
        if not root or not root.is_dir():
            continue
        for path in root.rglob("*"):
            if path.is_file() and path.suffix.lower() in IMAGE_EXTS:
                index.setdefault(path.name.lower(), []).append(path)
    return index


def _match_index(value: str, index: dict[str, list[Path]], where: str) -> Path | None:
    matches = index.get(Path(value).name.lower(), [])
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        listed = "\\n".join(f"  - {item}" for item in matches)
        raise ValueError(f"{where} 中存在同名图片，请明确指定 --image-dir：\\n{listed}")
    return None


def resolve_image(
    value: str,
    image_dir: Path,
    ls_data_dir: Path | None,
    image_index: dict[str, list[Path]],
    ls_index: dict[str, list[Path]],
) -> Path:
    raw = value.strip()
    direct = Path(raw)
    if direct.is_file():
        return direct

    parsed = urlsplit(raw)
    url_path = unquote(parsed.path)

    if "/data/local-files" in url_path or "/data/local-files" in raw:
        relative = parse_qs(parsed.query).get("d", [""])[0]
        relative = unquote(relative)
        if relative:
            for candidate in (image_dir / relative, image_dir / Path(relative).name):
                if candidate.is_file():
                    return candidate
            matched = _match_index(relative, image_index, "Local Files 目录")
            if matched:
                return matched

    if "/data/upload/" in url_path:
        if ls_data_dir is None:
            raise ValueError(
                "这张图是上传到 Label Studio 的，请加 --ls-data-dir 指向 Label Studio 数据目录"
            )
        relative = url_path.split("/data/upload/", 1)[1]
        candidate = ls_data_dir / "media" / "upload" / relative
        if candidate.is_file():
            return candidate
        matched = _match_index(relative, ls_index, "Label Studio media 目录")
        if matched:
            return matched

    matched = _match_index(raw, image_index, "--image-dir")
    if matched:
        return matched
    raise ValueError(
        f"找不到图片 {value!r}；请确认 --image-dir 或 --ls-data-dir 是否指向正确目录"
    )


def select_annotation(task: dict) -> dict | None:
    annotations = task.get("annotations") or []
    valid = [item for item in annotations if not item.get("was_cancelled")]
    if valid:
        return max(
            valid,
            key=lambda item: str(item.get("updated_at") or item.get("created_at") or ""),
        )
    if task.get("result"):
        return task
    return None


def flatten_result(result: dict) -> dict:
    flat = dict(result)
    value = result.get("value")
    if isinstance(value, dict):
        for key, item in value.items():
            flat.setdefault(key, item)
    return flat


def labels_from(flat: dict, primary: str) -> list[str]:
    for key in (primary, "labels", "label"):
        value = flat.get(key)
        if value:
            if isinstance(value, str):
                return [value]
            return [str(item) for item in value]
    return []


def original_size(flat: dict, width: int, height: int) -> tuple[int, int]:
    width_value = flat.get("original_width") or width
    height_value = flat.get("original_height") or height
    original_width = int(float(width_value))
    original_height = int(float(height_value))
    if original_width <= 0 or original_height <= 0:
        raise ValueError("original_width / original_height 非法")
    return original_width, original_height


def decode_ls_rle(rle: list[int]) -> np.ndarray:
    """解码 Label Studio 画笔使用的 RLE。"""
    data = np.asarray(rle, dtype=np.uint8).ravel()
    bits = np.unpackbits(data)
    position = 0

    def read(size: int) -> int:
        nonlocal position
        if position + size > bits.size:
            raise ValueError("RLE 数据不完整")
        value = 0
        for bit in bits[position : position + size]:
            value = (value << 1) | int(bit)
        position += size
        return value

    total = read(32)
    word_size = read(5) + 1
    rle_sizes = [read(4) + 1 for _ in range(4)]
    output = np.zeros(total, dtype=np.uint8)

    index = 0
    while index < total:
        repeated = read(1)
        end = index + 1 + read(rle_sizes[read(2)])
        end = min(end, total)
        if repeated:
            output[index:end] = read(word_size)
            index = end
        else:
            while index < end:
                output[index] = read(word_size)
                index += 1
    return output


def brush_region(
    flat: dict, original_width: int, original_height: int, width: int, height: int
) -> np.ndarray:
    rle = flat.get("rle")
    if not rle:
        raise ValueError("brushlabels 区域缺少 rle")
    decoded = decode_ls_rle(rle)
    expected_rgba = original_width * original_height * 4
    expected_gray = original_width * original_height

    if decoded.size == expected_rgba:
        region = decoded.reshape(original_height, original_width, 4)[:, :, 3]
    elif decoded.size == expected_gray:
        region = decoded.reshape(original_height, original_width)
    else:
        raise ValueError(
            f"RLE 长度 {decoded.size} 与 original_width/original_height 不匹配"
        )

    region = (region > 0).astype(np.uint8)
    if (original_width, original_height) != (width, height):
        resized = Image.fromarray(region * 255).resize(
            (width, height), Image.Resampling.NEAREST
        )
        region = (np.asarray(resized) > 0).astype(np.uint8)
    return region.astype(bool)


def polygon_points(
    points: list, original_width: int, original_height: int, width: int, height: int
) -> list[tuple[float, float]]:
    if len(points) < 3:
        raise ValueError("多边形至少需要 3 个点")
    scale_x = width / original_width
    scale_y = height / original_height
    result = []
    for point in points:
        x, y = float(point[0]), float(point[1])
        result.append(
            (x / 100.0 * original_width * scale_x, y / 100.0 * original_height * scale_y)
        )
    return result


def rectangle_points(
    flat: dict, original_width: int, original_height: int, width: int, height: int
) -> list[tuple[float, float]]:
    x = float(flat["x"])
    y = float(flat["y"])
    rect_width = float(flat["width"])
    rect_height = float(flat["height"])
    corners = [(x, y), (x + rect_width, y), (x + rect_width, y + rect_height), (x, y + rect_height)]
    return polygon_points(corners, original_width, original_height, width, height)


def paint_region(canvas: np.ndarray, region: np.ndarray, value: int) -> int:
    overlap = int(np.count_nonzero((canvas != 0) & (canvas != value) & region))
    canvas[region] = np.uint8(value)
    return overlap


def write_image(
    source: Path,
    stem: str,
    out_dir: Path,
    normalize: bool,
    overwrite: bool,
) -> Path:
    suffix = source.suffix.lower()
    if suffix not in MASK_EXTS:
        suffix = ".png"
        normalize = True
    target = out_dir / f"{stem}{suffix}"
    if target.exists() and not overwrite:
        return target
    if normalize:
        with Image.open(source) as image:
            ImageOps.exif_transpose(image).convert("RGB").save(target)
    else:
        shutil.copy2(source, target)
    return target


def convert_task(
    task: dict,
    names: dict[str, int],
    ignore_value: int,
    unknown: str,
    image_dir: Path,
    ls_data_dir: Path | None,
    image_index: dict[str, list[Path]],
    ls_index: dict[str, list[Path]],
    out_dir: Path,
    overwrite: bool,
    skip_empty: bool,
) -> tuple[str, int, list[str]]:
    source = resolve_image(
        task_image_value(task), image_dir, ls_data_dir, image_index, ls_index
    )
    annotation = select_annotation(task)
    if annotation is None:
        raise ValueError("任务没有可用标注")

    with Image.open(source) as opened:
        orientation = opened.getexif().get(274, 1)
        oriented = ImageOps.exif_transpose(opened)
        width, height = oriented.size
        normalize = orientation not in (0, 1) or oriented.size != opened.size

    canvas = np.zeros((height, width), dtype=np.uint8)
    warnings: list[str] = []
    overlaps = 0
    regions = 0

    for raw_result in annotation.get("result") or []:
        flat = flatten_result(raw_result)
        rotation = int(float(flat.get("image_rotation") or 0)) % 360
        if rotation:
            raise ValueError("标注包含图片旋转，请关闭旋转后重新导出")

        original_width, original_height = original_size(flat, width, height)
        region_type = str(flat.get("type", "")).lower()

        if region_type == "brushlabels" or "rle" in flat:
            labels = labels_from(flat, "brushlabels")
            if not labels:
                raise ValueError("画笔区域缺少 brushlabels")
            value = category_id(labels[0], names, unknown)
            region = brush_region(flat, original_width, original_height, width, height)
        elif region_type == "polygonlabels" or "points" in flat:
            labels = labels_from(flat, "polygonlabels")
            if not labels:
                raise ValueError("多边形区域缺少 polygonlabels")
            value = category_id(labels[0], names, unknown)
            points = polygon_points(
                flat.get("points") or [], original_width, original_height, width, height
            )
            region_image = Image.new("L", (width, height), 0)
            ImageDraw.Draw(region_image).polygon(points, fill=1)
            region = np.asarray(region_image) > 0
        elif region_type == "rectanglelabels" or "rectanglelabels" in flat:
            labels = labels_from(flat, "rectanglelabels")
            if not labels:
                raise ValueError("矩形区域缺少 rectanglelabels")
            value = category_id(labels[0], names, unknown)
            points = rectangle_points(flat, original_width, original_height, width, height)
            region_image = Image.new("L", (width, height), 0)
            ImageDraw.Draw(region_image).polygon(points, fill=1)
            region = np.asarray(region_image) > 0
        else:
            warnings.append(f"跳过不支持的区域类型 {region_type or '未知'}")
            continue

        if len(labels) > 1:
            warnings.append(f"区域包含多个标签 {labels}，只使用第一个")
        overlaps += paint_region(canvas, region, value)
        regions += 1

    if overlaps:
        warnings.append(f"有 {overlaps} 个像素存在不同类别重叠，后画区域会覆盖先画区域")
    if regions == 0:
        warnings.append("没有可用区域，输出全背景 mask")
        if skip_empty:
            return "skipped", 0, warnings

    out_images = out_dir / "images"
    out_masks = out_dir / "masks"
    out_images.mkdir(parents=True, exist_ok=True)
    out_masks.mkdir(parents=True, exist_ok=True)

    stem = source.stem
    write_image(source, stem, out_images, normalize, overwrite)

    mask_path = out_masks / f"{stem}.png"
    if mask_path.exists() and not overwrite:
        warnings.append(f"mask 已存在，未覆盖: {mask_path}")
        return "skipped", regions, warnings

    Image.fromarray(canvas, mode="L").save(mask_path)
    return "written", regions, warnings


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Label Studio JSON -> 类别 mask PNG")
    parser.add_argument("--export", nargs="+", type=Path, required=True, help="导出的 JSON 文件")
    parser.add_argument("--image-dir", type=Path, default=Path("data/raw"), help="原图目录")
    parser.add_argument("--ls-data-dir", type=Path, help="Label Studio 数据目录（上传图片时使用）")
    parser.add_argument("--out", type=Path, default=Path("data/exports"), help="输出目录")
    parser.add_argument("--categories", type=Path, default=Path("data/categories.yaml"))
    parser.add_argument(
        "--unknown-label",
        choices=("error", "other", "ignore"),
        default="error",
        help="遇到 categories.yaml 之外的标签时如何处理",
    )
    parser.add_argument("--overwrite", action="store_true", help="覆盖已存在的图片和 mask")
    parser.add_argument("--skip-empty", action="store_true", help="跳过没有任何区域的图片")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    names, ignore_value = load_categories(args.categories)
    tasks = load_tasks(args.export)
    if not tasks:
        print("导出文件中没有任务", file=sys.stderr)
        return 1

    image_index = build_image_index([args.image_dir])
    ls_index = build_image_index([args.ls_data_dir / "media"] if args.ls_data_dir else [])

    written = skipped = 0
    errors: list[str] = []
    warnings: list[str] = []
    seen: dict[str, Path] = {}

    for index, task in enumerate(tasks, 1):
        try:
            source = resolve_image(
                task_image_value(task),
                args.image_dir,
                args.ls_data_dir,
                image_index,
                ls_index,
            )
            if source.stem in seen:
                if seen[source.stem].resolve() != source.resolve():
                    raise ValueError(
                        f"不同图片使用同一文件名 {source.stem!r}，会导致 mask 覆盖"
                    )
                warnings.append(f"重复任务，已跳过: {source}")
                skipped += 1
                continue
            seen[source.stem] = source

            status, regions, task_warnings = convert_task(
                task,
                names,
                ignore_value,
                args.unknown_label,
                args.image_dir,
                args.ls_data_dir,
                image_index,
                ls_index,
                args.out,
                args.overwrite,
                args.skip_empty,
            )
            if status == "written":
                written += 1
            else:
                skipped += 1
            warnings.extend(f"task {index}: {item}" for item in task_warnings)
            print(f"[task {index}] {status}: {source.name} ({regions} 个区域)")
        except Exception as exc:  # noqa: BLE001
            errors.append(f"task {index}: {exc}")

    if warnings:
        print("\\n警告:")
        for item in warnings[:20]:
            print(f"  - {item}")
        if len(warnings) > 20:
            print(f"  ... 其余 {len(warnings) - 20} 条省略")

    print(f"\\n完成: 写入 {written} 张，跳过 {skipped} 张，失败 {len(errors)} 张")
    if errors:
        print("\\n错误:", file=sys.stderr)
        for item in errors[:20]:
            print(f"  - {item}", file=sys.stderr)
        if len(errors) > 20:
            print(f"  ... 其余 {len(errors) - 20} 条省略", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
