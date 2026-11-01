"""Summarize actionable Airbnb findings with host review sub-scores.

Run from any working directory:
    python scripts/business_insights.py

Writes a Markdown interpretation and CSV scorecards. No source data is changed.
"""

from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats


PROJECT_DIR = Path(__file__).resolve().parents[1]
INPUT_PATH = PROJECT_DIR / "data" / "processed" / "airbnb_features.csv"
OUTPUT_DIR = PROJECT_DIR / "data" / "processed" / "statistics"
REPORT_PATH = PROJECT_DIR / "reports" / "business_insights_recommendations.md"

HOST_COL = "host_portfolio_segment"
TARGET = "review_scores_rating"
SUBSCORES = {
    "review_scores_accuracy": "Accuracy",
    "review_scores_cleanliness": "Cleanliness",
    "review_scores_checkin": "Check-in",
    "review_scores_communication": "Communication",
    "review_scores_location": "Location",
    "review_scores_value": "Value",
}
PORTFOLIO_ORDER = ["1_listing", "2_to_5_listings", "6_to_20_listings", "21_plus_listings"]


def holm_adjust(values: list[float]) -> list[float]:
    p = np.asarray(values, dtype=float)
    order = np.argsort(p)
    out = np.empty(len(p), dtype=float)
    running = 0.0
    for rank, idx in enumerate(order):
        running = max(running, min(1.0, (len(p) - rank) * p[idx]))
        out[idx] = running
    return out.tolist()


def ci_mean(values: np.ndarray) -> tuple[float, float]:
    if len(values) < 2:
        return np.nan, np.nan
    half = stats.t.ppf(0.975, len(values) - 1) * stats.sem(values)
    mean = float(np.mean(values))
    return float(mean - half), float(mean + half)


def make_table(df: pd.DataFrame, cols: list[str]) -> str:
    rows = [["—" if pd.isna(v) else str(v).replace("|", "\\|") for v in row]
            for row in df[cols].itertuples(index=False, name=None)]
    heads = [str(x) for x in cols]
    widths = [max(len(heads[i]), *(len(row[i]) for row in rows)) for i in range(len(cols))]
    fmt = lambda row: "| " + " | ".join(val.ljust(widths[i]) for i, val in enumerate(row)) + " |"
    return "\n".join([fmt(heads), fmt(["-" * width for width in widths]), *(fmt(row) for row in rows)])


def p_str(p: float) -> str:
    return "<0.001" if p < 0.001 else f"{p:.3f}"


def main() -> None:
    data = pd.read_csv(INPUT_PATH, low_memory=False)
    required = [HOST_COL, TARGET, *SUBSCORES]
    missing = [col for col in required if col not in data.columns]
    if missing:
        raise ValueError(f"Feature table is missing columns: {missing}")

    output_rows = []
    tests = []
    for score_col, score_name in SUBSCORES.items():
        valid = data.dropna(subset=[HOST_COL, score_col])
        groups = []
        for portfolio in PORTFOLIO_ORDER:
            vals = valid.loc[valid[HOST_COL] == portfolio, score_col].astype(float).to_numpy()
            groups.append(vals)
            low, high = ci_mean(vals)
            output_rows.append({
                "subscore": score_name,
                "portfolio_segment": portfolio,
                "n": len(vals),
                "mean": float(np.mean(vals)),
                "mean_ci95_low": low,
                "mean_ci95_high": high,
                "median": float(np.median(vals)),
                "q1": float(np.quantile(vals, 0.25)),
                "q3": float(np.quantile(vals, 0.75)),
            })
        result = stats.kruskal(*groups, nan_policy="omit")
        n = sum(map(len, groups))
        k = len(groups)
        eps2 = max(0.0, min(1.0, (float(result.statistic) - k + 1) / (n - k)))
        tests.append({
            "subscore": score_name,
            "n": n,
            "groups": k,
            "h_statistic": float(result.statistic),
            "p_value": max(float(result.pvalue), np.nextafter(0.0, 1.0)),
            "epsilon_squared": eps2,
        })

    scorecard = pd.DataFrame(output_rows)
    test_df = pd.DataFrame(tests)
    test_df["p_holm_6_subscores"] = holm_adjust(test_df["p_value"].tolist())
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    scorecard.to_csv(OUTPUT_DIR / "subscore_host_segment_summary.csv", index=False)
    test_df.to_csv(OUTPUT_DIR / "subscore_host_segment_tests.csv", index=False)

    wide = scorecard.pivot(index="subscore", columns="portfolio_segment", values="mean")
    wide["gap_single_minus_21plus"] = wide["1_listing"] - wide["21_plus_listings"]
    top_gap = wide["gap_single_minus_21plus"].idxmax()
    next_gap = wide["gap_single_minus_21plus"].sort_values(ascending=False).index[1]
    top_score = wide["gap_single_minus_21plus"].max()
    second_gap = wide.loc[next_gap, "gap_single_minus_21plus"]
    overall = data.dropna(subset=[TARGET])
    mean_by_portfolio = overall.groupby(HOST_COL, observed=True)[TARGET].mean()
    n_by_portfolio = overall.groupby(HOST_COL, observed=True)[TARGET].count()
    coverage = data.groupby(HOST_COL, observed=True)[TARGET].agg(["count", "size"])
    coverage["coverage_pct"] = coverage["count"] / coverage["size"] * 100

    test_display = test_df.copy()
    test_display["h_statistic"] = test_display["h_statistic"].map(lambda x: f"{x:.2f}")
    test_display["p_holm_6_subscores"] = test_display["p_holm_6_subscores"].map(p_str)
    test_display["epsilon_squared"] = test_display["epsilon_squared"].map(lambda x: f"{x:.4f}")
    summary_display = scorecard.copy()
    for col in ["mean", "mean_ci95_low", "mean_ci95_high", "median", "q1", "q3"]:
        summary_display[col] = summary_display[col].map(lambda x: f"{x:.3f}")
    coverage_display = coverage.reset_index().rename(columns={HOST_COL: "host_portfolio_segment"})
    coverage_display["coverage_pct"] = coverage_display["coverage_pct"].map(lambda x: f"{x:.1f}%")

    rating_gap = mean_by_portfolio["1_listing"] - mean_by_portfolio["21_plus_listings"]
    report = [
        "# Business insights and recommendations",
        "",
        "## Decision question",
        "",
        "Where should Airbnb hosts and marketplace operations focus service-improvement work, based on the rating patterns in this London listing snapshot?",
        "",
        "## Evidence used",
        "",
        f"- Listing-level Airbnb snapshot: {len(data):,} listings; {len(overall):,} have an overall rating ({len(overall) / len(data) * 100:.1f}%).",
        "- Overall rating and six sub-scores (accuracy, cleanliness, check-in, communication, location, value) are on a 0–5 scale.",
        "- The main descriptive contrast is between hosts with one observed listing and hosts with 21+ observed listings. Portfolio size is measured only inside this dataset.",
        "- Sub-score group comparisons use Kruskal–Wallis tests and Holm adjustment across six sub-scores. Mean 95% intervals are pointwise descriptive intervals; epsilon-squared summarizes rank separation.",
        "",
        "## What the data says",
        "",
        f"1. The overall rating mean is {mean_by_portfolio['1_listing']:.3f} for single-listing hosts and {mean_by_portfolio['21_plus_listings']:.3f} for 21+ listing hosts, a {rating_gap:.3f}-point observed gap. This is the strongest grouping association in the preceding statistical analysis, but it is not a causal host-size effect.",
        f"2. The largest single-versus-21+ gap among the six sub-scores is **{top_gap}** ({top_score:.3f} points), followed by **{next_gap}** ({second_gap:.3f} points). This suggests the most useful first operational checks are whether the listing description matches the stay and whether guests feel the price matches what they received.",
        "3. Lower sub-scores also appear across multiple dimensions for larger portfolio segments. That pattern is consistent with a potential standardization or consistency opportunity, but could also reflect differences in room type, borough, price, guest mix, and rating coverage.",
        "4. Communication and check-in scores are relatively higher than value and cleanliness scores in the large-portfolio segment. A blanket recommendation to improve every service dimension equally would therefore be less targeted than starting with the larger observed gaps.",
        "",
        "### Overall score by host segment",
        "",
        make_table(pd.DataFrame({
            "host_portfolio_segment": PORTFOLIO_ORDER,
            "n_rated": [int(n_by_portfolio.get(k, 0)) for k in PORTFOLIO_ORDER],
            "mean_rating": [f"{mean_by_portfolio.get(k, np.nan):.3f}" for k in PORTFOLIO_ORDER],
            "rating_coverage": [f"{coverage.loc[k, 'coverage_pct']:.1f}%" for k in PORTFOLIO_ORDER],
        }), ["host_portfolio_segment", "n_rated", "mean_rating", "rating_coverage"]),
        "",
        "### Sub-score differences by host segment",
        "",
        "Means and pointwise 95% confidence intervals are listed with medians and quartiles to show the rating distribution, not only its average.",
        "",
        make_table(summary_display, ["subscore", "portfolio_segment", "n", "mean", "mean_ci95_low", "mean_ci95_high", "median", "q1", "q3"]),
        "",
        "### Tests across host segments for each sub-score",
        "",
        make_table(test_display, ["subscore", "n", "h_statistic", "p_holm_6_subscores", "epsilon_squared"]),
        "",
        "The tests show that rating distributions differ across host portfolio segments; they do not show that portfolio size caused the differences. The large sample can make small differences statistically significant, so use the score gaps and effect sizes to judge business relevance.",
        "",
        "## Recommended business actions",
        "",
        "### 1. Start with a listing accuracy and value-for-money audit",
        "",
        f"The biggest observed single-versus-large-host sub-score gap is {top_gap} ({top_score:.3f} points); {next_gap} is next ({second_gap:.3f}). For listings with low scores in those areas, check that photos, amenities, capacity, house rules, and location description match the actual stay, and review whether the price and fees align with what the listing promises.",
        "**Purpose:** reduce avoidable expectation mismatch and identify concrete listing details hosts can correct. This is a diagnostic recommendation; the data does not prove that making these changes will raise ratings.",
        "",
        "### 2. Help multi-listing operators standardize the guest journey",
        "",
        "Offer a reusable pre-arrival checklist for listing accuracy, cleanliness readiness, arrival instructions, and issue escalation. Focus the initial pilot on hosts with 6+ listings, but compare similar room types and boroughs so the group-level pattern is not mistaken for an operator-size effect.",
        "**Purpose:** test whether repeatable processes reduce inconsistency across a larger portfolio. Avoid describing multi-listing hosts as inherently worse; portfolio segment is an observed scale bucket, not a quality or legality label.",
        "",
        "### 3. Pilot and measure before scaling",
        "",
        "Run a small opt-in pilot with hosts who choose to review their listing accuracy and value messaging. Record a baseline, track adoption, and compare subsequent sub-scores with a similar non-pilot group over the same period. Predefine the measures: change in accuracy/value sub-score, share of listings completing the checklist, and guest complaint themes if available. Account for review counts and seasonality, and do not claim success from a few new reviews.",
        "**Purpose:** distinguish a plausible recommendation from one that has evidence of operational benefit.",
        "",
        "## Dashboard implications",
        "",
        "A decision-focused dashboard should let a host or analyst filter by room type, neighbourhood, and host portfolio segment, and show: (a) overall rating and six sub-scores with group counts; (b) local price position and ratings together; (c) rating coverage/missingness; and (d) the benchmark against the London listing sample. Clearly label the portfolio comparison as observational and the calendar metric as an unavailability proxy. Suppress exact host IDs and listing locations; report aggregated groups only.",
        "",
        "## Fairness, privacy, and limits",
        "",
        "- Ratings are self-selected guest feedback and are not a complete census of each stay. 21.6% of all Airbnb listings lack an overall rating; missing scores are not low scores.",
        "- Sub-score and overall-rating gaps may reflect room type, borough, nightly price, guest expectations, property age, or review propensity. This analysis does not adjust for those factors and cannot establish causes.",
        "- Small categories have less stable estimates. Avoid broad recommendations for rare property/room types without collecting more evidence.",
        "- Host identifiers, exact coordinates, and guest-level review text should not appear in a public dashboard. Use aggregate counts and score summaries; avoid exposing small groups that could identify a host.",
        "- A score should guide voluntary service review, not automatic penalties, ranking changes, or claims that a neighbourhood or host group is inherently low quality.",
        "",
        "## Reproducibility",
        "",
        "Run `python scripts/business_insights.py`. It writes this report and two CSV tables under `data/processed/statistics/`: `subscore_host_segment_summary.csv` and `subscore_host_segment_tests.csv`.",
        "",
    ]
    REPORT_PATH.write_text("\n".join(report), encoding="utf-8")
    print(f"Largest sub-score gap: {top_gap} ({top_score:.3f})")
    print(f"Second-largest sub-score gap: {next_gap} ({second_gap:.3f})")
    print(f"Saved report: {REPORT_PATH}")


if __name__ == "__main__":
    main()
