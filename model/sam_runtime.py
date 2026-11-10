"""SAM 的加载与推理公共入口。

三个调用方共用本文件，保证 zero-shot、微调后推理、网页 demo 走同一套
预处理和提示逻辑，避免三处各写一份导致结果对不上：
  - model/zero_shot_inference.py
  - app/main.py
  - model/train_common.py（训练时的提示构造也复用 instance_prompts）
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def list_image_mask_pairs(data_dir: Path) -> list[tuple[Path, Path]]:
    """列出 images/ 与 masks/ 中同名配套的文件，缺 mask 直接报错。"""
    images_dir = Path(data_dir) / "images"
    masks_dir = Path(data_dir) / "masks"
    if not images_dir.is_dir():
        raise SystemExit(f"找不到 {images_dir}，请按 data/README.md 准备数据")

    pairs: list[tuple[Path, Path]] = []
    missing: list[str] = []
    for image_path in sorted(images_dir.iterdir()):
        if not image_path.is_file() or image_path.suffix.lower() not in IMAGE_EXTS:
            continue
        mask_path = masks_dir / f"{image_path.stem}.png"
        if not mask_path.is_file():
            missing.append(image_path.name)
            continue
        pairs.append((image_path, mask_path))

    if missing:
        raise SystemExit(
            "以下图片缺少同名 mask: " + ", ".join(missing[:10])
            + ("" if len(missing) <= 10 else f" 等 {len(missing)} 张")
        )
    if not pairs:
        raise SystemExit(f"{images_dir} 里没有可用图片")
    return pairs


def instance_prompts(
    gt_mask: np.ndarray,
) -> list[tuple[int, tuple[int, int], tuple[int, int, int, int], int]]:
    """把类别 mask 拆成实例，返回 (类别, 内部点, 外接框, 实例编号)。

    点取距离变换的最大值位置，比质心更不容易落到凹形物体的外面；
    外接框同时作为 box 提示，SAM 对框提示的响应明显比单点稳定。
    第四个返回值是 scipy.ndimage.label 的连通域编号，训练时用它取回该实例。
    """
    from scipy import ndimage

    prompts = []
    for label in sorted({int(x) for x in np.unique(gt_mask) if x not in (0, 255)}):
        labeled, count = ndimage.label(gt_mask == label)
        for inst in range(1, count + 1):
            ys, xs = np.nonzero(labeled == inst)
            if xs.size == 0:
                continue
            deepest = int(np.argmax(ndimage.distance_transform_edt(labeled == inst)[ys, xs]))
            point = (int(xs[deepest]), int(ys[deepest]))
            box = (int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max()))
            prompts.append((label, point, box, inst))
    return prompts


def load_sam(checkpoint: Path, model_type: str = "vit_b", device: str = "cuda"):
    try:
        from segment_anything import sam_model_registry
    except ImportError as exc:
        raise SystemExit(
            "当前解释器里没有 segment-anything。\n"
            f"  当前解释器: {sys.executable}\n"
            "  正确做法: 用仓库的 .venv 运行，例如\n"
            "    .\\.venv\\Scripts\\python.exe model\\train_lora.py --check\n"
            "  确认依赖装在 .venv 里: .\\.venv\\Scripts\\pip.exe install -r model\\requirements.txt"
        ) from exc

    checkpoint = Path(checkpoint)
    if not checkpoint.is_file():
        raise SystemExit(f"找不到权重 {checkpoint}，按 model/README.md 下载后放到 checkpoints/")
    sam = sam_model_registry[model_type](checkpoint=str(checkpoint))
    return sam.to(device=device)


def load_predictor(
    checkpoint: Path,
    model_type: str = "vit_b",
    device: str = "cuda",
    lora_dir: Path | None = None,
    decoder_ckpt: Path | None = None,
):
    """加载 SAM，可选叠加 LoRA adapter 与 mask decoder 权重，返回 SamPredictor。"""
    from segment_anything import SamPredictor

    sam = load_sam(checkpoint, model_type, device)

    if lora_dir is not None:
        try:
            from peft import PeftModel
        except ImportError as exc:
            raise SystemExit(
                "当前解释器里没有 peft。\n"
                f"  当前解释器: {sys.executable}\n"
                "  用 .venv 安装: .\\.venv\\Scripts\\pip.exe install -r model\\requirements.txt"
            ) from exc
        lora_dir = Path(lora_dir)
        if not (lora_dir / "adapter_config.json").is_file():
            raise SystemExit(f"{lora_dir} 不是 LoRA 目录，应包含 adapter_config.json")
        sam = PeftModel.from_pretrained(sam, str(lora_dir))

    if decoder_ckpt is not None:
        import torch

        decoder_ckpt = Path(decoder_ckpt)
        if not decoder_ckpt.is_file():
            raise SystemExit(f"找不到 mask decoder 权重 {decoder_ckpt}")
        payload = torch.load(str(decoder_ckpt), map_location=device)
        state = payload.get("model", payload) if isinstance(payload, dict) else payload
        sam.mask_decoder.load_state_dict(state)

    return SamPredictor(sam)


def predict_with_prompt(
    predictor,
    points: list[tuple[int, int]] | None,
    labels: list[int] | None,
    box: tuple[int, int, int, int] | None = None,
) -> tuple[np.ndarray, float]:
    """执行一次提示分割，返回 (布尔 mask, score)。"""
    if not points and box is None:
        raise ValueError("至少需要一个点或一个框")

    masks, scores, _ = predictor.predict(
        point_coords=np.array(points, dtype=np.float32) if points else None,
        point_labels=np.array(labels, dtype=np.int32) if labels else None,
        box=np.array(box, dtype=np.float32) if box is not None else None,
        multimask_output=False,
    )
    return masks[0].astype(bool), float(scores[0])
