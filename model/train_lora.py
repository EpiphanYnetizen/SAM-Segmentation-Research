"""LoRA 微调脚手架（组员 B 在确定 SAM 版本后填充训练循环）。

目标：冻结 SAM 主干，只对 image encoder 的 target_modules 挂 LoRA，
并用 GT 点提示训练 mask decoder 输出。这里先固定配置加载和 LoRA 注入，
训练循环因不同 SAM / SAM2 API 差异较大，需按实际依赖适配。
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass
class TrainConfig:
    model_type: str
    checkpoint: Path
    data_dir: Path
    out_dir: Path
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
            lora=cfg["lora"],
            training=cfg["training"],
        )


def inject_lora(sam_model, cfg: TrainConfig):
    try:
        from peft import LoraConfig, get_peft_model
    except ImportError as exc:
        raise SystemExit(
            "缺少 peft，先执行: pip install -r model/requirements.txt"
        ) from exc

    lora = LoraConfig(
        r=cfg.lora["rank"],
        lora_alpha=cfg.lora["alpha"],
        lora_dropout=cfg.lora["dropout"],
        target_modules=cfg.lora["target_modules"],
    )
    return get_peft_model(sam_model, lora)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=Path("model/config/default.yaml"))
    args = parser.parse_args()

    cfg = TrainConfig.from_yaml(args.config)
    print(f"loaded config: {cfg.model_type} | {cfg.checkpoint}")
    print("TODO(组员 B): 在这里接入 SAM checkpoint 与训练循环")


if __name__ == "__main__":
    main()
