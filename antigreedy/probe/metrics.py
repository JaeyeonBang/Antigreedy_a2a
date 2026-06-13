"""Detection metrics (pure) + the Phase-1.5 gate.

detection_report folds (truth, prediction) pairs into TP/FP/FN/TN + P/R/F1.
phase15_gate is the entry condition for the probe phase: the monitor must catch
the probe in >= min_caught of the episodes with <= max_fp false positives total
(outside-voice #5: n=1 positive/episode means many episodes before P/R is real).
"""
from __future__ import annotations
from typing import Any, Iterable


def detection_report(labels: Iterable[tuple[bool, bool]]) -> dict[str, Any]:
    tp = fp = fn = tn = 0
    for truth, pred in labels:
        if truth and pred:
            tp += 1
        elif (not truth) and pred:
            fp += 1
        elif truth and (not pred):
            fn += 1
        else:
            tn += 1
    precision = tp / (tp + fp) if (tp + fp) else 1.0
    recall = tp / (tp + fn) if (tp + fn) else 1.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
    return {"tp": tp, "fp": fp, "fn": fn, "tn": tn,
            "precision": precision, "recall": recall, "f1": f1}


def phase15_gate(per_episode_caught: list[bool], fp_total: int,
                 min_caught: int = 6, max_fp: int = 1) -> dict[str, Any]:
    caught = sum(1 for c in per_episode_caught if c)
    passed = caught >= min_caught and fp_total <= max_fp
    return {"caught": caught, "episodes": len(per_episode_caught),
            "fp_total": fp_total, "min_caught": min_caught, "max_fp": max_fp,
            "passed": passed}
