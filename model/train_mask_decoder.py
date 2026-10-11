"""mask decoder 微调（组长 PM 负责）。

与 train_lora.py（组员 B 的 image encoder LoRA）分离，形成两个独立训练分支：
- encoder 分支：`model/train_lora.py`
- mask decoder 分支：本文件

两者最终统一评测，才能回答题目里“哪里该微调”的核心问题。
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import yaml


def load_config(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def report_run(out_dir: Path, metrics: dict) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "run_config.json").write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=Path("model/config/mask_decoder.yaml"))
    args = parser.parse_args()

    cfg = load_config(args.config)
    print(f"mask decoder config: {cfg}")
    print("TODO(组长): 冻结 image encoder，只更新 mask_decoder 参数")
    print("推荐 loss: 二值 focal + dice；优化器 AdamW lr=1e-4")
    print("每次实验都写 run_config.json + outputs/mask_decoder_{run}/")


if __name__ == "__main__":
    main()
