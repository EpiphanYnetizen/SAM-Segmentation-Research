"""image encoder LoRA 微调的脚手架（组员 B 负责补训练循环）。

已提供：配置加载、SAM 加载、LoRA 注入、环境自检（--check）。
未提供：训练循环、checkpoint 保存。补完后请在 model/README.md 登记实测命令。

先跑自检确认环境与挂载点正确：
    python model/train_lora.py --check
"""
from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path

import yaml

from sam_runtime import load_sam


@dataclass
class TrainConfig:
    model_type: str
    checkpoint: Path
    data_dir: Path
    out_dir: Path
    device: str
    lora: dict
    training: dict

    @classmethod
    def from_yaml(cls, path: Path) -> "TrainConfig":
        cfg = yaml.safe_load(path.read_text(encoding="utf-8"))
        return cls(
            model_type=cfg["model_type"],
            checkpoint=Path(cfg["checkpoint"]),
            data_dir=Path(cfg["data_dir"]),
            out_dir=Path(cfg["out_dir"]),
            device=cfg.get("device", "cuda"),
            lora=cfg["lora"],
            training=cfg["training"],
        )


def inject_lora(sam_model, cfg: TrainConfig):
    try:
        from peft import LoraConfig, get_peft_model
    except ImportError as exc:
        raise SystemExit(
            "当前解释器里没有 peft。\n"
            f"  当前解释器: {sys.executable}\n"
            "  用 .venv 安装: .\\.venv\\Scripts\\pip.exe install -r model\\requirements.txt"
        ) from exc

    lora = LoraConfig(
        r=cfg.lora["rank"],
        lora_alpha=cfg.lora["alpha"],
        lora_dropout=cfg.lora["dropout"],
        target_modules=cfg.lora["target_modules"],
    )
    return get_peft_model(sam_model, lora)


def check(cfg: TrainConfig) -> None:
    """不训练，只验证权重能加载、LoRA 能挂上，并打印可训练参数量。"""
    sam = load_sam(cfg.checkpoint, cfg.model_type, cfg.device)
    model = inject_lora(sam, cfg)

    trainable = [(n, p.numel()) for n, p in model.named_parameters() if p.requires_grad]
    total = sum(count for _, count in trainable)
    print(f"LoRA 注入成功：{len(trainable)} 个张量，{total / 1e6:.3f} M 可训练参数")
    print(f"target_modules: {cfg.lora['target_modules']}")
    for name, _ in trainable[:5]:
        print(f"  {name}")
    if not trainable:
        raise SystemExit("没有可训练参数，检查 config 里的 target_modules")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=Path("model/config/default.yaml"))
    parser.add_argument("--check", action="store_true", help="只做环境与 LoRA 挂载自检")
    args = parser.parse_args()

    cfg = TrainConfig.from_yaml(args.config)
    print(f"loaded config: {cfg.model_type} | {cfg.checkpoint}")

    if args.check:
        check(cfg)
        return

    raise SystemExit(
        "训练循环尚未实现（负责人：组员 B）。\n"
        "需要补的部分写在 model/README.md 的「组员 B 待办」里；\n"
        "先用 python model/train_lora.py --check 确认环境。"
    )


if __name__ == "__main__":
    main()
