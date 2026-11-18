"""mask decoder 微调训练脚本（组长 黄闻喆 负责）。

与 train_lora.py（组员 B 的 image encoder LoRA）分离，形成两个独立训练分支：
- encoder 分支：`model/train_lora.py`
- mask decoder 分支：本文件

训练策略：
- image encoder 与 prompt encoder 冻结，只开 mask_decoder 的参数；
- image encoder 只跑一次前向，不参与反向传播；
- loss 用 focal + dice，训练目标是与 SAM 低分辨率输出对齐的实例 mask；
- checkpoint 保存为 {"model": mask_decoder.state_dict()}，可直接给
  `zero_shot_inference.py --decoder-ckpt` 使用。

先自检：
    python model/train_mask_decoder.py --check

用假数据 smoke test：
    python model/train_mask_decoder.py --data-dir outputs/smoke_train --epochs 2 --limit 2 --out outputs/smoke_train_run
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import cv2
import numpy as np
import torch
import torch.nn.functional as F
import yaml
from PIL import Image
from scipy import ndimage

from sam_runtime import instance_prompts, list_image_mask_pairs, load_sam


def load_config(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def report_run(out_dir: Path, metrics: dict) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "run_config.json").write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def resolve_device(device: str) -> str:
    if device == "cuda" and not torch.cuda.is_available():
        print("未检测到 CUDA，改用 CPU")
        return "cpu"
    return device


def configure_trainable(sam, freeze: list[str]) -> tuple[int, int]:
    """冻结指定前缀的模块，返回 (可训练参数, 总参数)。"""
    frozen = set(freeze)
    for name, param in sam.named_parameters():
        param.requires_grad = not any(name.startswith(prefix) for prefix in frozen)

    trainable = sum(p.numel() for p in sam.parameters() if p.requires_grad)
    total = sum(p.numel() for p in sam.parameters())
    return trainable, total


def check(cfg: dict) -> None:
    """不训练，只验证权重加载与冻结策略，打印可训练参数量。"""
    device = resolve_device(cfg.get("device", "cuda"))
    sam = load_sam(
        Path(cfg["checkpoint"]),
        cfg.get("model_type", "vit_b"),
        device,
    )

    freeze = cfg.get("training", {}).get("freeze", [])
    trainable, total = configure_trainable(sam, freeze)
    print(f"冻结模块: {sorted(set(freeze))}")
    print(f"可训练 {trainable / 1e6:.3f} M / 总计 {total / 1e6:.1f} M")
    if trainable == 0:
        raise SystemExit("没有可训练参数，检查 config 里的 freeze 列表")


def load_image_and_gt(image_path: Path, mask_path: Path) -> tuple[np.ndarray, np.ndarray]:
    image_bgr = cv2.imread(str(image_path))
    if image_bgr is None:
        raise SystemExit(f"读不到图片: {image_path}")
    image = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
    gt = np.asarray(Image.open(mask_path).convert("L"), dtype=np.uint8)
    if gt.shape[:2] != image.shape[:2]:
        raise SystemExit(f"图片与 mask 尺寸不一致: {image_path.name} {image.shape[:2]} vs {gt.shape[:2]}")
    return image, gt


def iter_instances(gt: np.ndarray):
    """逐个产出 (实例点, 实例二值 mask)。"""
    for label, point, _box, inst in instance_prompts(gt):
        labeled, _ = ndimage.label(gt == label)
        target = labeled == inst
        if target.any():
            yield point, target


def prepare_target(target: np.ndarray, predictor, device: str) -> torch.Tensor:
    """把原图尺寸的实例 mask 对齐到 SAM 的 256x256 低分辨率输出。"""
    height, width = target.shape
    img_size = predictor.model.image_encoder.img_size
    new_h, new_w = predictor.transform.get_preprocess_shape(height, width, img_size)

    resized = cv2.resize(
        target.astype(np.uint8),
        (new_w, new_h),
        interpolation=cv2.INTER_NEAREST,
    )
    padded = np.zeros((img_size, img_size), dtype=np.uint8)
    padded[:new_h, :new_w] = resized
    low_res = cv2.resize(padded, (256, 256), interpolation=cv2.INTER_NEAREST)

    return torch.from_numpy(low_res).float()[None, None].to(device)


def focal_dice_loss(
    logits: torch.Tensor,
    target: torch.Tensor,
    alpha: float = 0.25,
    gamma: float = 2.0,
) -> torch.Tensor:
    bce = F.binary_cross_entropy_with_logits(logits, target, reduction="none")
    prob = torch.sigmoid(logits)
    pt = prob * target + (1 - prob) * (1 - target)
    focal = (alpha * target + (1 - alpha) * (1 - target)) * (1 - pt).pow(gamma) * bce
    focal = focal.mean()

    prob_flat = prob.flatten(1)
    target_flat = target.flatten(1)
    intersection = (prob_flat * target_flat).sum(dim=1)
    dice = 1 - (2 * intersection + 1) / (
        prob_flat.sum(dim=1) + target_flat.sum(dim=1) + 1
    )
    return focal + dice.mean()


def forward_instance(
    sam,
    predictor,
    point: tuple[int, int],
    device: str,
) -> tuple[torch.Tensor, torch.Tensor]:
    """单点提示前向，返回低分辨率 mask logits 和 IoU 预测。"""
    coords = torch.tensor([[point]], dtype=torch.float32, device=device)
    coords = predictor.transform.apply_coords_torch(coords, predictor.original_size)
    labels = torch.ones((1, 1), dtype=torch.int, device=device)

    sparse_embeddings, dense_embeddings = sam.prompt_encoder(
        points=(coords, labels),
        boxes=None,
        masks=None,
    )
    low_res_masks, iou_predictions = sam.mask_decoder(
        image_embeddings=predictor.features,
        image_pe=sam.prompt_encoder.get_dense_pe(),
        sparse_prompt_embeddings=sparse_embeddings,
        dense_prompt_embeddings=dense_embeddings,
        multimask_output=False,
    )
    return low_res_masks, iou_predictions


def train_epoch(
    sam,
    predictor,
    pairs: list[tuple[Path, Path]],
    optimizer: torch.optim.Optimizer,
    device: str,
    limit: int | None = None,
) -> tuple[float, int]:
    sam.image_encoder.eval()
    sam.prompt_encoder.eval()
    sam.mask_decoder.train()

    selected = pairs if limit is None else pairs[:limit]
    total_loss = 0.0
    total_instances = 0

    for image_path, mask_path in selected:
        image, gt = load_image_and_gt(image_path, mask_path)
        predictor.set_image(image)

        for point, target in iter_instances(gt):
            target_t = prepare_target(target, predictor, device)
            low_res_masks, _ = forward_instance(sam, predictor, point, device)
            loss = focal_dice_loss(low_res_masks, target_t)

            optimizer.zero_grad(set_to_none=True)
            loss.backward()
            optimizer.step()

            total_loss += float(loss.detach())
            total_instances += 1

    if total_instances == 0:
        raise SystemExit("训练集里没有可用实例，检查 mask 是否为 1..5 类别")
    return total_loss / total_instances, total_instances


@torch.no_grad()
def validate(
    sam,
    predictor,
    pairs: list[tuple[Path, Path]],
    device: str,
    limit: int | None = None,
) -> tuple[float, int]:
    sam.image_encoder.eval()
    sam.prompt_encoder.eval()
    sam.mask_decoder.eval()

    selected = pairs if limit is None else pairs[:limit]
    total_dice = 0.0
    total_instances = 0

    for image_path, mask_path in selected:
        image, gt = load_image_and_gt(image_path, mask_path)
        predictor.set_image(image)

        for point, target in iter_instances(gt):
            target_t = prepare_target(target, predictor, device)
            low_res_masks, _ = forward_instance(sam, predictor, point, device)
            pred = (torch.sigmoid(low_res_masks) > 0.5).float()
            intersection = (pred * target_t).sum()
            dice = (2 * intersection + 1) / (pred.sum() + target_t.sum() + 1)
            total_dice += float(dice)
            total_instances += 1

    if total_instances == 0:
        return 0.0, 0
    return total_dice / total_instances, total_instances


def save_checkpoint(sam, out_dir: Path, name: str = "mask_decoder.pth") -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / name
    torch.save({"model": sam.mask_decoder.state_dict()}, path)
    return path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=Path("model/config/mask_decoder.yaml"))
    parser.add_argument("--check", action="store_true", help="只做权重加载与冻结策略自检")
    parser.add_argument("--data-dir", type=Path, help="覆盖 config 里的训练集目录")
    parser.add_argument("--val-dir", type=Path, help="覆盖 config 里的验证集目录")
    parser.add_argument("--out", type=Path, help="覆盖 config 里的输出目录")
    parser.add_argument("--epochs", type=int, help="覆盖训练轮数")
    parser.add_argument("--limit", type=int, help="只取前 N 张图，用于 smoke test")
    args = parser.parse_args()

    cfg = load_config(args.config)
    if args.data_dir is not None:
        cfg["data_dir"] = str(args.data_dir)
    if args.val_dir is not None:
        cfg["val_dir"] = str(args.val_dir)
    if args.out is not None:
        cfg["out_dir"] = str(args.out)

    if args.check:
        check(cfg)
        return

    device = resolve_device(cfg.get("device", "cuda"))
    cfg["device"] = device
    torch.manual_seed(int(cfg.get("seed", 42)))
    np.random.seed(int(cfg.get("seed", 42)))

    data_dir = Path(cfg["data_dir"])
    pairs = list_image_mask_pairs(data_dir)

    val_pairs: list[tuple[Path, Path]] = []
    val_dir = cfg.get("val_dir")
    if val_dir and Path(val_dir).is_dir():
        try:
            val_pairs = list_image_mask_pairs(Path(val_dir))
        except SystemExit as exc:
            print(f"跳过验证集: {exc}")

    out_dir = Path(cfg["out_dir"])
    training = cfg.get("training", {})
    epochs = args.epochs if args.epochs is not None else int(training.get("epochs", 5))
    learning_rate = float(training.get("learning_rate", 1e-4))
    freeze = list(training.get("freeze", ["image_encoder", "prompt_encoder"]))

    sam = load_sam(
        Path(cfg["checkpoint"]),
        cfg.get("model_type", "vit_b"),
        device,
    )
    trainable, total = configure_trainable(sam, freeze)
    if trainable == 0:
        raise SystemExit("没有可训练参数，检查 config 里的 freeze 列表")

    from segment_anything import SamPredictor

    predictor = SamPredictor(sam)
    optimizer = torch.optim.AdamW(
        [p for p in sam.mask_decoder.parameters() if p.requires_grad],
        lr=learning_rate,
    )

    print(f"训练集: {data_dir} ({len(pairs)} 张)")
    print(f"验证集: {'跳过' if not val_pairs else f'{len(val_pairs)} 张'}")
    print(f"可训练 {trainable / 1e6:.3f} M / 总计 {total / 1e6:.1f} M")
    print(f"设备: {device} | epochs: {epochs} | lr: {learning_rate}")

    metrics = {"config": cfg, "epochs": []}
    best_dice = -1.0

    for epoch in range(1, epochs + 1):
        train_loss, train_instances = train_epoch(
            sam, predictor, pairs, optimizer, device, args.limit
        )
        row = {
            "epoch": epoch,
            "train_loss": train_loss,
            "train_instances": train_instances,
        }

        if val_pairs:
            val_dice, val_instances = validate(
                sam, predictor, val_pairs, device, args.limit
            )
            row["val_dice"] = val_dice
            row["val_instances"] = val_instances
            if val_dice > best_dice:
                best_dice = val_dice
                saved = save_checkpoint(sam, out_dir)
                row["saved"] = str(saved)
        else:
            saved = save_checkpoint(sam, out_dir)
            row["saved"] = str(saved)

        print(
            f"epoch {epoch}/{epochs} | loss {train_loss:.4f} | "
            f"instances {train_instances}"
            + (f" | val_dice {row['val_dice']:.4f}" if "val_dice" in row else "")
        )
        metrics["epochs"].append(row)

    last_path = save_checkpoint(sam, out_dir, "mask_decoder_last.pth")
    metrics["best_val_dice"] = best_dice if best_dice >= 0 else None
    metrics["checkpoint"] = str(out_dir / "mask_decoder.pth")
    (out_dir / "metrics.json").write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    report_run(out_dir, {"config": cfg, "last_checkpoint": str(last_path)})
    print(f"完成。checkpoint: {out_dir / 'mask_decoder.pth'}")
    print(f"训练日志: {out_dir / 'metrics.json'}")


if __name__ == "__main__":
    main()
