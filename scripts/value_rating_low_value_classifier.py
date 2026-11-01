"""Classify lower-quartile Airbnb value ratings with host-held-out evaluation."""

from pathlib import Path
import json

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import GroupKFold, GroupShuffleSplit
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "processed" / "airbnb_features.csv"
OUT = ROOT / "data" / "processed" / "modeling"
TARGET = "review_scores_value"
CAT = ["neighbourhood_cleansed", "property_type", "room_type", "bathroom_privacy"]
NUM = [
    "accommodates", "bathrooms", "bedrooms", "beds", "price",
    "listed_price_per_guest_gbp", "host_listing_count", "amenity_count",
    "amenity_wifi", "amenity_kitchen", "amenity_washer",
    "amenity_air_conditioning", "amenity_workspace", "amenity_parking",
    "amenity_pool", "amenity_self_check_in", "description_length_chars",
    "description_word_count", "minimum_nights", "maximum_nights",
    "train_fold_price_position_pct",
]
FEATURES = CAT + [c for c in NUM if c != "train_fold_price_position_pct"]
SEED = 42


def preprocessor(scale: bool) -> ColumnTransformer:
    nsteps = [("impute", SimpleImputer(strategy="median", add_indicator=True))]
    if scale:
        nsteps.append(("scale", StandardScaler(with_mean=False)))
    cats = Pipeline([
        ("impute", SimpleImputer(strategy="most_frequent")),
        ("onehot", OneHotEncoder(handle_unknown="ignore", min_frequency=10)),
    ])
    nums = Pipeline(nsteps)
    return ColumnTransformer([("num", nums, NUM), ("cat", cats, CAT)])


def add_train_fold_price_context(train: pd.DataFrame, other: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    keys = ["neighbourhood_cleansed", "room_type"]
    group = train.groupby(keys, dropna=False)["price"]
    medians = group.median()
    counts = group.count()
    global_median = train["price"].median()
    usable = {key: value for key, value in medians.items() if counts.loc[key] >= 20}

    def apply(frame: pd.DataFrame) -> pd.DataFrame:
        result = frame.copy()
        local = pd.Series(
            [usable.get((n, r), global_median) for n, r in zip(frame[keys[0]], frame[keys[1]])],
            index=frame.index,
            dtype="float64",
        )
        result["train_fold_price_position_pct"] = (result["price"] / local - 1.0) * 100.0
        return result

    return apply(train), apply(other)


def run_repeated_group_cv(df: pd.DataFrame) -> pd.DataFrame:
    """Evaluate the fixed classifier across 3 repeats of host-grouped 5-fold CV."""
    rows = []
    groups = df["host_id"].astype(str)
    for repeat, seed in enumerate([11, 42, 73], start=1):
        cv = GroupKFold(n_splits=5, shuffle=True, random_state=seed)
        for fold, (train_idx, valid_idx) in enumerate(cv.split(df, groups=groups), start=1):
            train, valid = df.iloc[train_idx].copy(), df.iloc[valid_idx].copy()
            threshold = float(train[TARGET].quantile(0.25))
            y_train = (train[TARGET] <= threshold).astype(int)
            y_valid = (valid[TARGET] <= threshold).astype(int)
            X_train, X_valid = add_train_fold_price_context(train, valid)
            X_train = X_train[FEATURES + ["train_fold_price_position_pct"]].copy()
            X_valid = X_valid[FEATURES + ["train_fold_price_position_pct"]].copy()
            for col in NUM:
                X_train[col] = pd.to_numeric(X_train[col], errors="coerce")
                X_valid[col] = pd.to_numeric(X_valid[col], errors="coerce")

            model = Pipeline([
                ("prep", preprocessor(scale=False)),
                ("model", RandomForestClassifier(
                    n_estimators=150, max_depth=24, min_samples_leaf=5,
                    max_features=0.7, class_weight="balanced_subsample",
                    n_jobs=-1, random_state=SEED,
                )),
            ])
            model.fit(X_train, y_train)
            prob = model.predict_proba(X_valid)[:, 1]
            k = max(1, int(np.ceil(0.10 * len(prob))))
            top = np.argsort(prob)[-k:]
            top_precision = float(y_valid.iloc[top].mean())
            rows.append({
                "repeat": repeat,
                "fold": fold,
                "n_train": len(train_idx),
                "n_valid": len(valid_idx),
                "threshold_from_training_q25": threshold,
                "validation_low_value_rate": float(y_valid.mean()),
                "average_precision_pr_auc": average_precision_score(y_valid, prob),
                "roc_auc": roc_auc_score(y_valid, prob),
                "precision_at_top_10pct": top_precision,
                "recall_at_top_10pct": float(y_valid.iloc[top].sum() / max(1, y_valid.sum())),
                "lift_at_top_10pct": top_precision / float(y_valid.mean()),
                "brier_score": brier_score_loss(y_valid, prob),
                "host_overlap": len(set(groups.iloc[train_idx]) & set(groups.iloc[valid_idx])),
            })
    return pd.DataFrame(rows)


def main() -> None:
    if not DATA.exists():
        raise FileNotFoundError(f"Missing {DATA}; run feature engineering first.")
    OUT.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(DATA, low_memory=False).dropna(subset=[TARGET, "host_id"]).copy()
    df[TARGET] = pd.to_numeric(df[TARGET], errors="coerce")
    df = df.dropna(subset=[TARGET])
    groups = df["host_id"].astype(str)
    splitter = GroupShuffleSplit(n_splits=1, test_size=0.20, random_state=SEED)
    tr, te = next(splitter.split(df, groups=groups))
    train, test = df.iloc[tr].copy(), df.iloc[te].copy()

    # Threshold is estimated on training ratings only. The task flags the bottom
    # quartile, making the output a review-prioritization aid, not a quality label.
    threshold = float(train[TARGET].quantile(0.25))
    y_train = (train[TARGET] <= threshold).astype(int)
    y_test = (test[TARGET] <= threshold).astype(int)
    X_train, X_test = add_train_fold_price_context(train, test)
    X_train, X_test = X_train[FEATURES + ["train_fold_price_position_pct"]], X_test[FEATURES + ["train_fold_price_position_pct"]]
    for col in NUM:
        X_train[col] = pd.to_numeric(X_train[col], errors="coerce")
        X_test[col] = pd.to_numeric(X_test[col], errors="coerce")

    models = {
        "prevalence_baseline": DummyClassifier(strategy="prior"),
        "logistic_regression": Pipeline([
            ("prep", preprocessor(scale=True)),
            ("model", LogisticRegression(max_iter=500, class_weight="balanced", C=0.5)),
        ]),
        "random_forest_classifier": Pipeline([
            ("prep", preprocessor(scale=False)),
            ("model", RandomForestClassifier(
                n_estimators=200, max_depth=24, min_samples_leaf=5,
                max_features=0.7, class_weight="balanced_subsample",
                n_jobs=-1, random_state=SEED,
            )),
        ]),
    }

    rows = []
    fitted = {}
    for name, model in models.items():
        model.fit(X_train, y_train)
        fitted[name] = model
        prob = model.predict_proba(X_test)[:, 1]
        k = max(1, int(np.ceil(0.10 * len(prob))))
        top = np.argsort(prob)[-k:]
        if name == "prevalence_baseline":
            precision_top = float(y_test.mean())
            recall_top = 0.10
            lift_top = 1.0
        else:
            precision_top = float(y_test.iloc[top].mean())
            recall_top = float(y_test.iloc[top].sum() / max(1, y_test.sum()))
            lift_top = float(precision_top / y_test.mean())
        rows.append({
            "model": name,
            "n_test": len(y_test),
            "low_value_test_prevalence": float(y_test.mean()),
            "average_precision_pr_auc": float(average_precision_score(y_test, prob)),
            "roc_auc": float(roc_auc_score(y_test, prob)),
            "precision_at_top_10pct": precision_top,
            "recall_at_top_10pct": recall_top,
            "lift_at_top_10pct": lift_top,
            "brier_score": float(brier_score_loss(y_test, prob)),
        })

    results = pd.DataFrame(rows).sort_values("average_precision_pr_auc", ascending=False)
    results.to_csv(OUT / "low_value_classifier_metrics.csv", index=False)
    joblib.dump(fitted["random_forest_classifier"], OUT / "low_value_random_forest_classifier.joblib")

    forest_prob = fitted["random_forest_classifier"].predict_proba(X_test)[:, 1]
    forest_pred = (forest_prob >= 0.5).astype(int)
    subgroup = test[["room_type", "host_portfolio_segment", "neighbourhood_cleansed"]].copy()
    subgroup["actual_low_value"] = y_test.to_numpy()
    subgroup["predicted_low_value"] = forest_pred
    subgroup["risk_probability"] = forest_prob
    summaries = []
    for field in ["room_type", "host_portfolio_segment", "neighbourhood_cleansed"]:
        for label, part in subgroup.groupby(field, dropna=False):
            if len(part) < 30:
                continue
            summaries.append({
                "group_field": field,
                "group": str(label),
                "n": len(part),
                "actual_low_value_rate": part["actual_low_value"].mean(),
                "mean_predicted_risk": part["risk_probability"].mean(),
                "recall_at_0_5_threshold": recall_score(part["actual_low_value"], part["predicted_low_value"], zero_division=0),
            })
    pd.DataFrame(summaries).to_csv(OUT / "low_value_classifier_subgroups.csv", index=False)

    repeated = run_repeated_group_cv(df)
    repeated.to_csv(OUT / "low_value_repeated_group_cv.csv", index=False)
    repeated_summary = repeated.drop(columns=["repeat", "fold", "n_train", "n_valid", "threshold_from_training_q25", "host_overlap"]).agg(["mean", "std"]).T
    repeated_summary.to_csv(OUT / "low_value_repeated_group_cv_summary.csv", header=["mean", "std"])

    metadata = {
        "target": TARGET,
        "classification_definition": "low value = score at or below the 25th percentile of training ratings",
        "training_quantile_threshold": threshold,
        "train_rows": len(train), "test_rows": len(test),
        "train_hosts": int(groups.iloc[tr].nunique()),
        "test_hosts": int(groups.iloc[te].nunique()),
        "host_overlap": len(set(groups.iloc[tr]) & set(groups.iloc[te])),
        "train_low_value_prevalence": float(y_train.mean()),
        "test_low_value_prevalence": float(y_test.mean()),
        "price_position": "calculated using train partition medians by neighbourhood x room_type; groups under 20 use train global median",
        "seed": SEED,
    }
    (OUT / "low_value_classifier_summary.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    print(f"Low-value threshold from training data: {threshold:.2f}")
    print(results.to_string(index=False, float_format=lambda x: f"{x:.4f}"))
    print("Repeated 5-fold x 3 host-grouped CV (mean ± SD):")
    print(repeated_summary.to_string(float_format=lambda x: f"{x:.4f}"))
    print(f"Host overlap: {metadata['host_overlap']}")
    print(f"Outputs: {OUT}")


if __name__ == "__main__":
    main()
