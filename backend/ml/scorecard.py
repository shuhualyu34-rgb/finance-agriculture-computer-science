"""评分卡分数换算(无 sklearn 依赖,推理与训练共用)。"""

from __future__ import annotations

import math

BASE_SCORE = 600.0
PDO = 50.0  # 分数每增加 50,违约几率(odds)减半


def score_from_probability(probability: float) -> int:
    """标准评分卡换算:score = base - PDO/ln2 * ln(odds),clamp [300, 900]。

    违约概率越低(odds 越小),分数越高;违约概率 0.5 对应基准分 600。
    """
    p = min(max(float(probability), 1e-6), 1 - 1e-6)
    odds = p / (1 - p)
    score = BASE_SCORE - (PDO / math.log(2)) * math.log(odds)
    return int(round(min(900.0, max(300.0, score))))


def risk_band(score: int) -> str:
    if score < 450:
        return "HIGH"
    if score < 600:
        return "MEDIUM"
    return "LOW"
