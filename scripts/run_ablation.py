"""消融对比汇总：读取多组 metrics JSON，输出分组表。"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--metrics", nargs="+", required=True)
    parser.add_argument("--out", type=Path, default=Path("outputs/ablation_table.md"))
    args = parser.parse_args()

    rows = []
    for path in args.metrics:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        summary = data.get("summary", {})
        rows.append(
            {
                "run": Path(path).stem,
                "mIoU": summary.get("mIoU", 0),
                "meanDice": summary.get("meanDice", 0),
                "meanBoundaryF1": summary.get("meanBoundaryF1", 0),
            }
        )

    lines = ["| run | mIoU | Dice | BoundaryF1 |", "|---|---|---|---|"]
    for row in sorted(rows, key=lambda x: -x["mIoU"]):
        lines.append(
            f"| {row['run']} | {row['mIoU']:.3f} | {row['meanDice']:.3f} | {row['meanBoundaryF1']:.3f} |"
        )
    args.out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
