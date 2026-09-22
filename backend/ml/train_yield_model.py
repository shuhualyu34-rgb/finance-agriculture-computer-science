"""产量预测模型训练(离线):线性回归 vs 随机森林,择优保存。

数据源:仓库内种子 SQL(danqiu_rice_seed.sql),不依赖数据库。

用法:
    python -m backend.ml.train_yield_model
    python -m backend.ml.train_yield_model --seed 其他文件.sql --out backend/ml/models/yield_model.joblib

产物:
    joblib 文件含 {model, feature_names, target, model_name, metrics, version, trained_at}
"""

from __future__ import annotations

import argparse
from datetime import UTC, datetime

import joblib
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split

from backend.ml.dataset import build_yield_dataset
from backend.ml.features import YIELD_FEATURES
from backend.ml.seed_loader import load_seed_sql

DEFAULT_SEED = "danqiu_rice_seed.sql"
DEFAULT_OUT = "backend/ml/models/yield_model.joblib"


def _evaluate(name: str, model, X_train, X_test, y_train, y_test) -> tuple[float, float]:
    model.fit(X_train, y_train)
    pred = model.predict(X_test)
    mae = float(mean_absolute_error(y_test, pred))
    r2 = float(r2_score(y_test, pred))
    print(f"[yield] {name:20s} 测试集 MAE={mae:.1f} 斤/亩  R²={r2:.4f}")
    return mae, r2


def main() -> None:
    parser = argparse.ArgumentParser(description="训练产量预测模型(线性回归 vs 随机森林)")
    parser.add_argument("--seed", default=DEFAULT_SEED)
    parser.add_argument("--out", default=DEFAULT_OUT)
    args = parser.parse_args()

    tables = load_seed_sql(args.seed)
    X_raw, y_raw = build_yield_dataset(tables)
    if len(X_raw) < 20:
        raise SystemExit(f"训练样本不足({len(X_raw)} 条),请检查种子数据")

    X = np.array([[row[f] for f in YIELD_FEATURES] for row in X_raw], dtype=float)
    y = np.array(y_raw, dtype=float)
    mean_y = float(y.mean())
    print(f"[yield] 地块样本={len(y)}  平均亩产={mean_y:.1f} 斤/亩  范围=[{y.min():.0f}, {y.max():.0f}]")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    lr_mae, lr_r2 = _evaluate("LinearRegression", LinearRegression(), X_train, X_test, y_train, y_test)
    rf_mae, rf_r2 = _evaluate(
        "RandomForestRegressor",
        RandomForestRegressor(n_estimators=300, min_samples_leaf=3, random_state=42, n_jobs=-1),
        X_train, X_test, y_train, y_test,
    )

    if rf_r2 >= lr_r2:
        best_name = "RandomForestRegressor"
        best_model = RandomForestRegressor(
            n_estimators=300, min_samples_leaf=3, random_state=42, n_jobs=-1
        )
        best_metrics = {"mae": rf_mae, "r2": rf_r2}
    else:
        best_name = "LinearRegression"
        best_model = LinearRegression()
        best_metrics = {"mae": lr_mae, "r2": lr_r2}
    best_model.fit(X, y)

    artifact = {
        "type": "yield_model",
        "version": "v1",
        "trained_at": datetime.now(UTC).isoformat(),
        "feature_names": YIELD_FEATURES,
        "target": "output_per_mu",
        "model_name": best_name,
        "model": best_model,
        "metrics": {
            "linear_regression": {"mae": lr_mae, "r2": lr_r2},
            "random_forest": {"mae": rf_mae, "r2": rf_r2},
            "selected": best_metrics,
        },
    }
    joblib.dump(artifact, args.out)
    print(f"\n[yield] 择优模型: {best_name}  已保存: {args.out}")


if __name__ == "__main__":
    main()
