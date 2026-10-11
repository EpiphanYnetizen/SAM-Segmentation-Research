import numpy as np

from evaluation import metrics


def test_iou_perfect():
    mask = np.zeros((10, 10), dtype=np.uint8)
    mask[2:8, 2:8] = 1
    assert metrics.iou(mask > 0, mask > 0) > 0.999


def test_compute_metrics_smoke():
    gt = np.zeros((10, 10), dtype=np.uint8)
    gt[1:5, 1:5] = 1
    gt[6:9, 6:9] = 2
    pred = gt.copy()
    result = metrics.compute_metrics(pred, gt)
    assert result["mIoU"] > 0.99
    assert result["meanDice"] > 0.99
