from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from scripts.split_dataset import split


def _write_pair(root: Path, index: int) -> None:
    Image.fromarray(np.zeros((8, 8, 3), dtype=np.uint8)).save(
        root / "images" / f"img_{index}.jpg"
    )
    Image.fromarray(np.zeros((8, 8), dtype=np.uint8)).save(
        root / "masks" / f"img_{index}.png"
    )


def test_split_ignores_gitkeep(tmp_path: Path) -> None:
    data = tmp_path / "data"
    (data / "images").mkdir(parents=True)
    (data / "masks").mkdir()
    (data / "images" / ".gitkeep").write_text("")
    (data / "masks" / ".gitkeep").write_text("")
    for index in range(10):
        _write_pair(data, index)

    out = tmp_path / "splits"
    split(data, out)

    assert len(list((out / "train" / "images").glob("*.jpg"))) == 7
    assert len(list((out / "val" / "images").glob("*.jpg"))) == 1
    assert len(list((out / "test" / "images").glob("*.jpg"))) == 2
    assert not list(out.rglob(".gitkeep"))


def test_split_rejects_missing_mask(tmp_path: Path) -> None:
    data = tmp_path / "data"
    (data / "images").mkdir(parents=True)
    (data / "masks").mkdir()
    Image.fromarray(np.zeros((8, 8, 3), dtype=np.uint8)).save(
        data / "images" / "img_0.jpg"
    )

    with pytest.raises(SystemExit):
        split(data, tmp_path / "splits")
