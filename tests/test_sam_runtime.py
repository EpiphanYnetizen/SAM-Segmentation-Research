from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from model.sam_runtime import instance_prompts, list_image_mask_pairs, predict_with_prompt


def test_instance_prompts_split_classes_and_instances() -> None:
    gt = np.zeros((40, 40), dtype=np.uint8)
    gt[2:10, 2:10] = 1
    gt[2:10, 20:30] = 1
    gt[20:35, 20:35] = 3

    prompts = instance_prompts(gt)

    assert len(prompts) == 3
    assert sorted(label for label, *_ in prompts) == [1, 1, 3]

    for label, point, box, _inst in prompts:
        x, y = point
        assert gt[y, x] == label, "提示点必须落在对应类别的实例内部"
        x1, y1, x2, y2 = box
        assert x1 <= x <= x2 and y1 <= y <= y2


def test_instance_prompts_ignores_background_and_ignore() -> None:
    gt = np.zeros((10, 10), dtype=np.uint8)
    gt[0:5, 0:5] = 255
    assert instance_prompts(gt) == []


def _write_pair(root: Path, name: str) -> None:
    (root / "images").mkdir(parents=True, exist_ok=True)
    (root / "masks").mkdir(parents=True, exist_ok=True)
    Image.fromarray(np.zeros((8, 8, 3), dtype=np.uint8)).save(root / "images" / name)
    Image.fromarray(np.zeros((8, 8), dtype=np.uint8)).save(
        root / "masks" / f"{Path(name).stem}.png"
    )


def test_list_image_mask_pairs_skips_gitkeep(tmp_path: Path) -> None:
    _write_pair(tmp_path, "a.jpg")
    _write_pair(tmp_path, "b.png")
    (tmp_path / "images" / ".gitkeep").write_text("")
    (tmp_path / "images" / "notes.txt").write_text("")

    pairs = list_image_mask_pairs(tmp_path)

    assert [image.stem for image, _ in pairs] == ["a", "b"]


def test_list_image_mask_pairs_reports_missing_mask(tmp_path: Path) -> None:
    _write_pair(tmp_path, "a.jpg")
    Image.fromarray(np.zeros((8, 8, 3), dtype=np.uint8)).save(tmp_path / "images" / "c.jpg")

    with pytest.raises(SystemExit, match="c.jpg"):
        list_image_mask_pairs(tmp_path)


def test_list_image_mask_pairs_requires_images(tmp_path: Path) -> None:
    (tmp_path / "images").mkdir()

    with pytest.raises(SystemExit):
        list_image_mask_pairs(tmp_path)


class _FakePredictor:
    def __init__(self) -> None:
        self.received: dict = {}

    def predict(self, point_coords, point_labels, box, multimask_output):
        self.received = {
            "points": point_coords,
            "labels": point_labels,
            "box": box,
            "multimask": multimask_output,
        }
        mask = np.ones((1, 4, 4), dtype=bool)
        return mask, np.array([0.9]), None


def test_predict_with_prompt_requires_a_prompt() -> None:
    with pytest.raises(ValueError):
        predict_with_prompt(_FakePredictor(), points=None, labels=None)


def test_predict_with_prompt_forwards_point_and_returns_mask() -> None:
    predictor = _FakePredictor()

    mask, score = predict_with_prompt(predictor, points=[(3, 4)], labels=[1])

    assert mask.shape == (4, 4) and mask.dtype == bool
    assert score == pytest.approx(0.9)
    assert predictor.received["points"].tolist() == [[3.0, 4.0]]
    assert predictor.received["labels"].tolist() == [1]
    assert predictor.received["box"] is None
    assert predictor.received["multimask"] is False
