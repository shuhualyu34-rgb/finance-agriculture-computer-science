"""信用评分卡训练(离线)。

数据源:仓库内种子 SQL(danqiu_rice_seed.sql),不依赖数据库。

用法:
    python -m backend.ml.train_credit_scorecard
    python -m backend.ml.train_credit_scorecard --seed 其他文件.sql --out backend/ml/models/credit_scorecard.joblib

产物:
    joblib 文件含 {model, scaler, feature_names, base_score, pdo, version, trained_at}
"""

from __future__ import annotations

import argparse
from datetime import UTC, datetime

import joblib
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, roc_auc_score
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from backend.ml.dataset import build_credit_dataset
from backend.ml.features import CREDIT_FEATURES
from backend.ml.scorecard import BASE_SCORE, PDO
from backend.ml.seed_loader import load_seed_sql

DEFAULT_SEED = "danqiu_rice_seed.sql"
DEFAULT_OUT = "backend/ml/models/credit_scorecard.joblib"


def main() -> None:
    parser = argparse.ArgumentParser(description="训练信用评分卡(逻辑回归)")
    parser.add_argument("--seed", default=DEFAULT_SEED)
    parser.add_argument("--out", default=DEFAULT_OUT)
    args = parser.parse_args()

    tables = load_seed_sql(args.seed)
    X_raw, y = build_credit_dataset(tables)
    if len(X_raw) < 20:
        raise SystemExit(f"训练样本不足({len(X_raw)} 条),请检查种子数据")

    X = np.array([[row[f] for f in CREDIT_FEATURES] for row in X_raw], dtype=float)
    y = np.array(y, dtype=int)
    n_pos = int(y.sum())
    print(f"[credit] 样本数={len(y)}  通过={n_pos}  拒绝={len(y) - n_pos}")

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    pipe = make_pipeline(
        StandardScaler(),
        LogisticRegression(max_iter=2000, class_weight="balanced", random_state=42),
    )
    auc_scores = cross_val_score(pipe, X, y, cv=cv, scoring="roc_auc")
    print(f"[credit] 5折交叉验证 AUC = {auc_scores.mean():.4f} (±{auc_scores.std():.4f})")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=42, stratify=y
    )
    pipe.fit(X_train, y_train)
    proba = pipe.predict_proba(X_test)[:, 1]
    test_auc = roc_auc_score(y_test, proba)
    test_acc = accuracy_score(y_test, (proba >= 0.5).astype(int))
    print(f"[credit] 测试集 AUC={test_auc:.4f}  ACC={test_acc:.4f}")

    coef = pipe.named_steps["logisticregression"].coef_[0]
    print("\n[credit] 特征权重(标准化后):")
    for name, w in sorted(zip(CREDIT_FEATURES, coef, strict=True), key=lambda x: -abs(x[1])):
        print(f"  {name:22s} {w:+.4f}")

    artifact = {
        "type": "credit_scorecard",
        "version": "v1",
        "trained_at": datetime.now(UTC).isoformat(),
        "feature_names": CREDIT_FEATURES,
        "base_score": BASE_SCORE,
        "pdo": PDO,
        "model": pipe,
        "metrics": {"cv_auc": float(auc_scores.mean()), "test_auc": float(test_auc)},
    }
    joblib.dump(artifact, args.out)
    print(f"\n[credit] 已保存模型: {args.out}")


if __name__ == "__main__":
    main()
