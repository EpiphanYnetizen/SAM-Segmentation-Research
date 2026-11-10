import json
from pathlib import Path

import numpy as np
from PIL import Image

from scripts.labelstudio_to_masks import decode_ls_rle, main


CATEGORIES = Path(__file__).resolve().parents[1] / "data" / "categories.yaml"


def test_decode_ls_rle():
    rle = [0, 0, 0, 64, 57, 27, 253, 176, 24, 192, 45, 128, 226, 48, 0]
    decoded = decode_ls_rle(rle)
    assert decoded.size == 64
    mask = decoded.reshape(4, 4, 4)[:, :, 3]
    expected = np.zeros((4, 4), dtype=np.uint8)
    expected[0:2, 0:3] = 1
    assert np.array_equal(mask, expected)


def test_polygon_export_to_mask(tmp_path):
    image_dir = tmp_path / "images"
    image_dir.mkdir()
    Image.fromarray(np.zeros((80, 100, 3), dtype=np.uint8)).save(
        image_dir / "canteen_001.jpg"
    )

    points = [[5, 5], [45, 5], [45, 45], [5, 45]]
    export = [
        {
            "id": 1,
            "data": {"image": "/data/local-files/?d=canteen_001.jpg"},
            "annotations": [
                {
                    "result": [
                        {
                            "type": "polygonlabels",
                            "original_width": 100,
                            "original_height": 80,
                            "value": {
                                "points": points,
                                "polygonlabels": ["鱼块"],
                            },
                        }
                    ]
                }
            ],
        }
    ]
    export_path = tmp_path / "export.json"
    export_path.write_text(json.dumps(export, ensure_ascii=False), encoding="utf-8")

    out_dir = tmp_path / "exports"
    code = main(
        [
            "--export",
            str(export_path),
            "--image-dir",
            str(image_dir),
            "--out",
            str(out_dir),
            "--categories",
            str(CATEGORIES),
        ]
    )
    assert code == 0
    assert (out_dir / "images" / "canteen_001.jpg").is_file()
    mask = np.asarray(Image.open(out_dir / "masks" / "canteen_001.png"))
    assert mask.shape == (80, 100)
    assert set(np.unique(mask)) <= {0, 2}
    assert (mask[10:30, 10:40] == 2).mean() > 0.95
