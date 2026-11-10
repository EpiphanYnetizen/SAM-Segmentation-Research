"""mask decoder 微调的脚手架（组长 黄闻喆 负责补训练循环）。

与 train_lora.py（组员 B 的 image encoder LoRA）分离，形成两个独立训练分支：
- encoder 分支：`model/train_lora.py`
- mask decoder 分支：本文件

已提供：配置加载、SAM 加载、冻结策略自检（--check）。
未提供：训练循环、checkpoint 保存。

训练要点（避免走弯路）：
- image encoder 与 prompt encoder 冻结，只开 mask_decoder 的参数；
- encoder 前向放在 torch.no_grad() 里，否则 1024 输入的反向传播会白占显存；
- 保存格式写成 {"model": mask_decoder.state_dict()}，推理时用
  `zero_shot_inference.py --decoder-ckpt` 直接加载。

先跑自检：
    python model/train_mask_decoder.py --check
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import yaml

from sam_runtime import load_sam


def load_config(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def report_run(out_dir: Path, metrics: dict) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "run_config.json").write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def check(cfg: dict) -> None:
    """不训练，只验证权重加载与冻结策略，打印可训练参数量。"""
    sam = load_sam(Path(cfg["checkpoint"]), cfg.get("model_type", "vit_b"), cfg.get("device", "cuda"))

    frozen = set(cfg.get("training", {}).get("freeze", []))
    for name, param in sam.named_parameters():
        param.requires_grad = not any(name.startswith(prefix) for prefix in frozen)

    trainable = sum(p.numel() for p in sam.parameters() if p.requires_grad)
    total = sum(p.numel() for p in sam.parameters())
    print(f"冻结模块: {sorted(frozen)}")
    print(f"可训练 {trainable / 1e6:.3f} M / 总计 {total / 1e6:.1f} M")
    if trainable == 0:
        raise SystemExit("没有可训练参数，检查 config 里的 freeze 列表")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=Path("model/config/mask_decoder.yaml"))
    parser.add_argument("--check", action="store_true", help="只做权重加载与冻结策略自检")
    args = parser.parse_args()

    cfg = load_config(args.config)
    print(f"mask decoder config: {cfg}")

    if args.check:
        check(cfg)
        return

    raise SystemExit(
        "训练循环尚未实现（负责人：组长）。\n"
        "需要补的部分写在 model/README.md 的「组长待办」里；\n"
        "先用 python model/train_mask_decoder.py --check 确认冻结策略。"
    )


if __name__ == "__main__":
    main()
