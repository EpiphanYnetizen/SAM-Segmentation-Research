"""SAM 提示分割推理：zero-shot 与微调后共用。

设计说明：SAM 本身不输出类别。为了能直接与类别 GT 对齐评测，
这里对每个 GT 实例做一次点提示（实例内部距离变换最大处，避免凹形物体
的质心落到物体外），把预测 mask 归入该类别。zero-shot 时模型权重
不做任何训练；加 --lora-dir 或 --decoder-ckpt 即复用同一脚本评测微调结果。

提示协议与训练一致：单点提示，见 docs/experiment-plan.md。

用法:
    python model/zero_shot_inference.py \
      --checkpoint checkpoints/sam_vit_b_01ec64.pth \
      --data-dir data/splits/val \
      --out outputs/zero_shot

    # 评测 image encoder LoRA
    python model/zero_shot_inference.py --data-dir data/splits/val \
      --lora-dir checkpoints/lora/encoder/<run_id> --out outputs/finetuned

    # 评测 mask decoder 微调
    python model/zero_shot_inference.py --data-dir data/splits/val \
      --decoder-ckpt checkpoints/lora/mask_decoder/<run_id>/mask_decoder.pth \
      --out outputs/mask_decoder_v1
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

from sam_runtime import instance_prompts, list_image_mask_pairs, load_predictor


def infer_one(image_path: Path, mask_path: Path, predictor) -> np.ndarray:
    image = cv2.cvtColor(cv2.imread(str(image_path)), cv2.COLOR_BGR2RGB)
    predictor.set_image(image)
    gt = np.asarray(Image.open(mask_path).convert("L"), dtype=np.uint8)
    out = np.zeros_like(gt)

    for label, point, _box, _inst in instance_prompts(gt):
        masks, _scores, _ = predictor.predict(
            point_coords=np.array([point], dtype=np.float32),
            point_labels=np.array([1], dtype=np.int32),
            multimask_output=False,
        )
        out[masks[0] > 0] = label
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--checkpoint", type=Path, default=Path("checkpoints/sam_vit_b_01ec64.pth")
    )
    parser.add_argument("--model-type", default="vit_b")
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--data-dir", type=Path, default=Path("data/splits/val"))
    parser.add_argument("--out", type=Path, default=Path("outputs/zero_shot"))
    parser.add_argument("--lora-dir", type=Path, help="image encoder LoRA adapter 目录")
    parser.add_argument("--decoder-ckpt", type=Path, help="mask decoder 权重 .pth")
    args = parser.parse_args()

    pairs = list_image_mask_pairs(args.data_dir)
    args.out.mkdir(parents=True, exist_ok=True)
    predictor = load_predictor(
        args.checkpoint,
        args.model_type,
        args.device,
        lora_dir=args.lora_dir,
        decoder_ckpt=args.decoder_ckpt,
    )

    results = {}
    for image_path, mask_path in pairs:
        pred = infer_one(image_path, mask_path, predictor)
        Image.fromarray(pred).save(args.out / f"{image_path.stem}.png")
        results[image_path.stem] = "ok"

    (args.out.parent / f"{args.out.name}_manifest.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"done: {len(results)}/{len(pairs)}")


if __name__ == "__main__":
    main()
