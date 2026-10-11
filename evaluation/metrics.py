"""纯 NumPy + SciPy 语义分割指标。

背景类(id=0)不计入类别均值；直接调用 compute_metrics 返回类别级均值。
"""
from __future__ import annotations

import numpy as np
from scipy import ndimage


def mask_boundary(mask: np.ndarray) -> np.ndarray:
    eroded = ndimage.binary_erosion(mask, iterations=1)
    return mask & ~eroded


def boundary_f1(
    pred: np.ndarray,
    gt: np.ndarray,
    tolerance: int = 2,
    eps: float = 1e-7,
) -> float:
    pred_b = mask_boundary(pred.astype(bool))
    gt_b = mask_boundary(gt.astype(bool))
    dist_to_gt = ndimage.distance_transform_edt(~gt_b)
    dist_to_pred = ndimage.distance_transform_edt(~pred_b)
    tp_pred = int((pred_b & (dist_to_gt <= tolerance)).sum())
    tp_gt = int((gt_b & (dist_to_pred <= tolerance)).sum())
    precision = tp_pred / max(int(pred_b.sum()), 1)
    recall = tp_gt / max(int(gt_b.sum()), 1)
    if precision + recall == 0:
        return 0.0
    return 2 * precision * recall / (precision + recall + eps)


def iou(pred: np.ndarray, gt: np.ndarray, eps: float = 1e-7) -> float:
    inter = np.logical_and(pred, gt).sum()
    union = np.logical_or(pred, gt).sum()
    return float(inter / (union + eps))


def dice(pred: np.ndarray, gt: np.ndarray, eps: float = 1e-7) -> float:
    inter = np.logical_and(pred, gt).sum()
    return float(2 * inter / (pred.sum() + gt.sum() + eps))


def compute_metrics(pred: np.ndarray, gt: np.ndarray) -> dict[str, float]:
    """返回 mIoU/meanDice/meanBoundaryF1（按 1..N 前景类别平均）。"""
    labels = sorted({int(x) for x in np.unique(gt) if x != 0})
    if not labels:
        return {"mIoU": 0.0, "meanDice": 0.0, "meanBoundaryF1": 0.0}

    ious, dices, bf1s = [], [], []
    for lab in labels:
        pred_b = (pred == lab).astype(bool)
        gt_b = (gt == lab).astype(bool)
        ious.append(iou(pred_b, gt_b))
        dices.append(dice(pred_b, gt_b))
        bf1s.append(boundary_f1(pred_b, gt_b))

    return {
        "mIoU": float(np.mean(ious)),
        "meanDice": float(np.mean(dices)),
        "meanBoundaryF1": float(np.mean(bf1s)),
    }
