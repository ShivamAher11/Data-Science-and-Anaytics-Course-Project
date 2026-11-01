"""Train and evaluate a host-held-out model for Airbnb guest value ratings."""

from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.inspection import permutation_importance
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import GroupKFold, GroupShuffleSplit, GridSearchCV
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.dummy import DummyRegressor


PROJECT_DIR = Path(__file__).resolve().parents[1]
DATA_PATH = PROJECT_DIR / "data" / "processed" / "airbnb_features.csv"
OUTPUT_DIR = PROJECT_DIR / "data" / "processed" / "modeling"
MODEL_PATH = OUTPUT_DIR / "value_rating_random_forest.joblib"
METRICS_PATH = OUTPUT_DIR / "value_rating_model_metrics.csv"
SUBGROUP_PATH = OUTPUT_DIR / "value_rating_subgroup_errors.csv"
IMPORTANCE_PATH = OUTPUT_DIR / "value_rating_permutation_importance.csv"
SPLIT_PATH = OUTPUT_DIR / "value_rating_split_summary.json"

TARGET = "review_scores_value"
GROUP = "host_id"
CATEGORICAL_FEATURES = [
    "neighbourhood_cleansed",
    "property_type",
    "room_type",
    "bathroom_privacy",
]
NUMERIC_FEATURES = [
    "accommodates",
    "bathrooms",
    "bedrooms",
    "beds",
    "price",
    "listed_price_per_guest_gbp",
    "host_listing_count",
    "amenity_count",
    "amenity_wifi",
    "amenity_kitchen",
    "amenity_washer",
    "amenity_air_conditioning",
    "amenity_workspace",
    "amenity_parking",
    "amenity_pool",
    "amenity_self_check_in",
    "description_length_chars",
    "description_word_count",
    "minimum_nights",
    "maximum_nights",
]
FEATURES = CATEGORICAL_FEATURES + NUMERIC_FEATURES
SUBGROUP_FIELDS = ["room_type", "host_portfolio_segment", "neighbourhood_cleansed"]
RANDOM_STATE = 42


def make_preprocessor(scale_numeric: bool) -> ColumnTransformer:
    numeric_steps = [("impute", SimpleImputer(strategy="median", add_indicator=True))]
    if scale_numeric:
        numeric_steps.append(("scale", StandardScaler(with_mean=False)))

    numeric_pipeline = Pipeline(numeric_steps)
    categorical_pipeline = Pipeline(
        [
            ("impute", SimpleImputer(strategy="most_frequent")),
            (
                "onehot",
                OneHotEncoder(
                    handle_unknown="ignore",
                    min_frequency=10,
                    sparse_output=True,
                ),
            ),
        ]
    )
    return ColumnTransformer(
        [
            ("numeric", numeric_pipeline, NUMERIC_FEATURES),
            ("categorical", categorical_pipeline, CATEGORICAL_FEATURES),
        ],
        remainder="drop",
    )


def metrics(actual: np.ndarray, predicted: np.ndarray) -> dict[str, float]:
    return {
        "mae": float(mean_absolute_error(actual, predicted)),
        "rmse": float(np.sqrt(mean_squared_error(actual, predicted))),
        "r2": float(r2_score(actual, predicted)),
    }


def main() -> None:
    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"Missing {DATA_PATH}. Run scripts/feature_engineering.py first."
        )
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    data = pd.read_csv(DATA_PATH, low_memory=False)
    required = set(FEATURES + [TARGET, GROUP] + SUBGROUP_FIELDS)
    missing = sorted(required.difference(data.columns))
    if missing:
        raise ValueError(f"Model input is missing required fields: {missing}")

    # Use rated listings for this target; missing ratings are unknown outcomes.
    data = data.dropna(subset=[TARGET]).copy()
    data[TARGET] = pd.to_numeric(data[TARGET], errors="coerce")
    data = data.dropna(subset=[TARGET]).copy()
    data = data[data[TARGET].between(0, 5)].copy()

    # IDs are split keys only. Rows without a host ID get unique groups so they
    # cannot all be forced into one giant group; no ID enters the feature matrix.
    groups = data[GROUP].astype("string")
    missing_host = groups.isna()
    groups.loc[missing_host] = [f"missing_host_row_{i}" for i in data.index[missing_host]]

    X = data[FEATURES].copy()
    for field in NUMERIC_FEATURES:
        X[field] = pd.to_numeric(X[field], errors="coerce")
    y = data[TARGET].astype(float)

    splitter = GroupShuffleSplit(n_splits=1, test_size=0.20, random_state=RANDOM_STATE)
    train_idx, test_idx = next(splitter.split(X, y, groups=groups))
    X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
    y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]

    models = {
        "mean_baseline": DummyRegressor(strategy="mean"),
        "median_baseline": DummyRegressor(strategy="median"),
        "ridge": Pipeline(
            [
                ("preprocess", make_preprocessor(scale_numeric=True)),
                ("model", Ridge(alpha=10.0)),
            ]
        ),
        "random_forest": Pipeline(
            [
                ("preprocess", make_preprocessor(scale_numeric=False)),
                (
                    "model",
                    RandomForestRegressor(
                        n_estimators=150,
                        max_depth=24,
                        min_samples_leaf=3,
                        max_features=0.7,
                        n_jobs=-1,
                        random_state=RANDOM_STATE,
                    ),
                ),
            ]
        ),
    }

    metric_rows = []
    predictions: dict[str, np.ndarray] = {}
    for name, model in models.items():
        model.fit(X_train, y_train)
        pred = model.predict(X_test)
        predictions[name] = pred
        metric_rows.append(
            {"model": name, "n_train": len(train_idx), "n_test": len(test_idx), **metrics(y_test, pred)}
        )

    # Tune a more flexible forest using only host-grouped folds in the training
    # partition. The final host-held-out test remains untouched by tuning.
    tuned_search = GridSearchCV(
        models["random_forest"],
        param_grid={
            "model__max_depth": [24, None],
            "model__min_samples_leaf": [1, 5],
        },
        scoring="neg_mean_absolute_error",
        cv=GroupKFold(n_splits=3),
        n_jobs=1,
        refit=True,
    )
    tuned_search.fit(X_train, y_train, groups=groups.iloc[train_idx])
    rf = tuned_search.best_estimator_
    tuned_pred = rf.predict(X_test)
    predictions["random_forest_tuned"] = tuned_pred
    metric_rows.append(
        {"model": "random_forest_tuned", "n_train": len(train_idx), "n_test": len(test_idx), **metrics(y_test, tuned_pred)}
    )

    metric_table = pd.DataFrame(metric_rows).sort_values("mae")
    metric_table.to_csv(METRICS_PATH, index=False)

    # Save the host-grouped-CV-tuned forest; compare its holdout score with both
    # mean and median baselines before making any claim about usefulness.
    joblib.dump(rf, MODEL_PATH)
    chosen_pred = predictions["random_forest_tuned"]

    eval_data = data.iloc[test_idx].copy()
    eval_data["actual"] = y_test.to_numpy()
    eval_data["predicted"] = chosen_pred
    eval_data["error"] = eval_data["predicted"] - eval_data["actual"]
    subgroup_rows = []
    for field in SUBGROUP_FIELDS:
        for group_value, frame in eval_data.groupby(field, dropna=False):
            if len(frame) < 30:
                continue
            subgroup_rows.append(
                {
                    "group_field": field,
                    "group": "Missing" if pd.isna(group_value) else str(group_value),
                    "n": len(frame),
                    "mae": mean_absolute_error(frame["actual"], frame["predicted"]),
                    "rmse": np.sqrt(mean_squared_error(frame["actual"], frame["predicted"])),
                    "mean_error_predicted_minus_actual": frame["error"].mean(),
                }
            )
    pd.DataFrame(subgroup_rows).to_csv(SUBGROUP_PATH, index=False)

    # Permutation importance is calculated on a fixed, at-most-1,000-row holdout
    # sample and on raw input columns, making categorical importance readable.
    importance_n = min(1_000, len(X_test))
    importance_idx = np.random.default_rng(RANDOM_STATE).choice(
        len(X_test), size=importance_n, replace=False
    )
    importance = permutation_importance(
        rf,
        X_test.iloc[importance_idx],
        y_test.iloc[importance_idx],
        scoring="neg_mean_absolute_error",
        n_repeats=3,
        random_state=RANDOM_STATE,
        n_jobs=-1,
    )
    importance_table = pd.DataFrame(
        {
            "feature": FEATURES,
            "mean_mae_increase_when_permuted": importance.importances_mean,
            "std_mae_increase": importance.importances_std,
        }
    ).sort_values("mean_mae_increase_when_permuted", ascending=False)
    importance_table.to_csv(IMPORTANCE_PATH, index=False)

    split_summary = {
        "target": TARGET,
        "target_scale": [0, 5],
        "rated_rows_used": int(len(data)),
        "unrated_rows_excluded": int(pd.read_csv(DATA_PATH, usecols=[TARGET])[TARGET].isna().sum()),
        "train_rows": int(len(train_idx)),
        "test_rows": int(len(test_idx)),
        "train_hosts": int(groups.iloc[train_idx].nunique()),
        "test_hosts": int(groups.iloc[test_idx].nunique()),
        "host_overlap": int(
            len(set(groups.iloc[train_idx]).intersection(set(groups.iloc[test_idx])))
        ),
        "missing_host_ids_treated_as_individual_groups": int(missing_host.sum()),
        "features": FEATURES,
        "excluded_columns": [
            "all identifiers and exact coordinates",
            "overall and sub-score rating fields other than the target",
            "review volume, timing, text, sentiment, and review-derived features",
            "calendar availability, occupancy, and revenue estimates",
            "full-sample local price benchmarks and host_portfolio_segment",
            "host_is_superhost because status may depend on ratings",
            "host response/acceptance fields and instant_bookable because they are 100% missing in this snapshot",
        ],
        "random_state": RANDOM_STATE,
        "random_forest_parameters": {
            "n_estimators": 150,
            "max_depth": tuned_search.best_params_["model__max_depth"],
            "min_samples_leaf": tuned_search.best_params_["model__min_samples_leaf"],
            "max_features": 0.7,
            "grouped_cv_mae": float(-tuned_search.best_score_),
        },
        "metrics_file": str(METRICS_PATH.relative_to(PROJECT_DIR)),
    }
    SPLIT_PATH.write_text(json.dumps(split_summary, indent=2), encoding="utf-8")

    print("Held-out host-group evaluation (lower MAE/RMSE is better):")
    print(metric_table.to_string(index=False, float_format=lambda v: f"{v:.4f}"))
    print(f"Host overlap between train/test: {split_summary['host_overlap']}")
    print("Top permutation-importance features:")
    print(importance_table.head(10).to_string(index=False, float_format=lambda v: f"{v:.4f}"))
    print(f"Outputs written under {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
