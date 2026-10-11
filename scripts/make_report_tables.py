"""从 metrics JSON 生成 Markdown 对比表，便于写报告。"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--metrics", nargs="+", required=True)
    parser.add_argument("--out", type=Path, default=Path("outputs/report_table.md"))
    args = parser.parse_args()

    rows = []
    for path in args.metrics:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        rows.append((Path(path).stem, data))

    lines = ["| 实验 | mIoU | Dice | Boundary F1 |", "|---|---|---|---|"]
    for name, data in rows:
        lines.append(
            f"| {name} | {data.get('mIoU', 0):.3f} | {data.get('meanDice', 0):.3f} | {data.get('meanBoundaryF1', 0):.3f} |"
        )
    args.out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(args.out)


if __name__ == "__main__":
    main()
