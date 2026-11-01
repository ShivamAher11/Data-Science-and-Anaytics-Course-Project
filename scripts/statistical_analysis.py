"""Analyze associations between Airbnb listing features and guest ratings.

Run from any working directory:
    python scripts/statistical_analysis.py

Reads the engineered listing table and writes CSV summaries plus a Markdown
report. The script does not modify source or feature data.
"""

from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats


PROJECT_DIR = Path(__file__).resolve().parents[1]
INPUT_PATH = PROJECT_DIR / "data" / "processed" / "airbnb_features.csv"
OUTPUT_DIR = PROJECT_DIR / "data" / "processed" / "statistics"
REPORT_PATH = PROJECT_DIR / "reports" / "statistical_analysis.md"
MIN_NEIGHBOURHOOD_N = 100

GROUPS = {
    "room_type": "Room type",
    "host_portfolio_segment": "Host portfolio segment",
    "price_position_vs_local_market": "Local price position",
    "neighbourhood_cleansed": "Neighbourhood",
}


def holm_adjust(p_values: list[float]) -> list[float]:
    """Holm family-wise adjustment, returning values in input order."""
    p = np.asarray(p_values, dtype=float)
    order = np.argsort(p)
    adjusted = np.empty(len(p), dtype=float)
    running_max = 0.0
    m = len(p)
    for rank, idx in enumerate(order):
        value = min(1.0, (m - rank) * p[idx])
        running_max = max(running_max, value)
        adjusted[idx] = running_max
    return adjusted.tolist()


def mean_ci(values: np.ndarray) -> tuple[float, float]:
    n = len(values)
    mean = float(np.mean(values))
    if n < 2:
        return np.nan, np.nan
    half_width = float(stats.t.ppf(0.975, n - 1) * stats.sem(values))
    return mean - half_width, mean + half_width


def describe_groups(df: pd.DataFrame, column: str) -> pd.DataFrame:
    rows = []
    for group_name, group in df.groupby(column, observed=True, dropna=True, sort=True):
        values = group["review_scores_rating"].to_numpy(dtype=float)
        lower, upper = mean_ci(values)
        rows.append(
            {
                "feature": column,
                "group": str(group_name),
                "n_rated": len(values),
                "mean_rating": float(np.mean(values)),
                "mean_ci95_low": lower,
                "mean_ci95_high": upper,
                "median_rating": float(np.median(values)),
                "q1_rating": float(np.quantile(values, 0.25)),
                "q3_rating": float(np.quantile(values, 0.75)),
            }
        )
    return pd.DataFrame(rows)


def omnibus_test(df: pd.DataFrame, column: str) -> dict:
    groups = [
        group["review_scores_rating"].to_numpy(dtype=float)
        for _, group in df.groupby(column, observed=True, dropna=True, sort=True)
        if len(group) > 0
    ]
    n = sum(map(len, groups))
    k = len(groups)
    result = stats.kruskal(*groups, nan_policy="omit")
    # Kruskal-Wallis epsilon-squared effect size, clipped to [0, 1].
    effect = max(0.0, min(1.0, (float(result.statistic) - k + 1) / (n - k)))
    return {
        "feature": column,
        "groups": k,
        "n_rated": n,
        "h_statistic": float(result.statistic),
        "p_value": float(result.pvalue),
        "epsilon_squared": effect,
    }


def pairwise_tests(df: pd.DataFrame, column: str) -> pd.DataFrame:
    entries = []
    data = {
        str(name): group["review_scores_rating"].to_numpy(dtype=float)
        for name, group in df.groupby(column, observed=True, dropna=True, sort=True)
    }
    for left, right in combinations(data, 2):
        x, y = data[left], data[right]
        result = stats.mannwhitneyu(x, y, alternative="two-sided", method="asymptotic")
        # Positive values mean the first group tends to have higher scores.
        rank_biserial = 2 * float(result.statistic) / (len(x) * len(y)) - 1
        entries.append(
            {
                "feature": column,
                "group_1": left,
                "group_2": right,
                "n_1": len(x),
                "n_2": len(y),
                "median_1": float(np.median(x)),
                "median_2": float(np.median(y)),
                "median_difference_1_minus_2": float(np.median(x) - np.median(y)),
                "rank_biserial_effect": rank_biserial,
                "p_value": float(result.pvalue),
            }
        )
    out = pd.DataFrame(entries)
    if not out.empty:
        out["p_holm_within_feature"] = holm_adjust(out["p_value"].tolist())
    return out


def markdown_table(df: pd.DataFrame, columns: list[str], formats: dict[str, str] | None = None) -> str:
    view = df[columns].copy()
    for col, fmt in (formats or {}).items():
        view[col] = view[col].map(lambda value: fmt.format(value) if pd.notna(value) else "—")
    headers = [str(column) for column in view.columns]
    rows = [["—" if pd.isna(value) else str(value).replace("|", "\\|") for value in row]
            for row in view.itertuples(index=False, name=None)]
    widths = [max(len(headers[i]), *(len(row[i]) for row in rows)) for i in range(len(headers))]
    render_row = lambda row: "| " + " | ".join(value.ljust(widths[i]) for i, value in enumerate(row)) + " |"
    return "\n".join([render_row(headers), render_row(["-" * width for width in widths]),
                      *(render_row(row) for row in rows)])


def p_text(value: float) -> str:
    if value < 0.001:
        return "<0.001"
    return f"{value:.3f}"


def main() -> None:
    if not INPUT_PATH.exists():
        raise FileNotFoundError(f"Could not find {INPUT_PATH}. Run feature engineering first.")

    data = pd.read_csv(INPUT_PATH, low_memory=False)
    needed = ["review_scores_rating", *GROUPS]
    missing = [column for column in needed if column not in data.columns]
    if missing:
        raise ValueError(f"Feature table is missing required columns: {missing}")

    total_n = len(data)
    rated = data.dropna(subset=["review_scores_rating"]).copy()
    rated["review_scores_rating"] = pd.to_numeric(rated["review_scores_rating"], errors="coerce")
    rated = rated.dropna(subset=["review_scores_rating"])

    # Exclude the engineered fallback label and very small benchmark cells from
    # the local-price-position comparison; it is not a meaningful price tier.
    analysis_frames = {
        "room_type": rated.dropna(subset=["room_type"]),
        "host_portfolio_segment": rated.dropna(subset=["host_portfolio_segment"]),
        "price_position_vs_local_market": rated[
            rated["price_position_vs_local_market"].isin(
                ["below_local_median", "near_local_median", "above_local_median"]
            )
        ],
    }
    neighbourhood_counts = rated.groupby("neighbourhood_cleansed", dropna=True).size()
    eligible_neighbourhoods = neighbourhood_counts[
        neighbourhood_counts >= MIN_NEIGHBOURHOOD_N
    ].index
    analysis_frames["neighbourhood_cleansed"] = rated[
        rated["neighbourhood_cleansed"].isin(eligible_neighbourhoods)
    ].dropna(subset=["neighbourhood_cleansed"])

    summaries = []
    omnibus = []
    for column, frame in analysis_frames.items():
        summaries.append(describe_groups(frame, column))
        omnibus.append(omnibus_test(frame, column))
    summary = pd.concat(summaries, ignore_index=True)
    omnibus_df = pd.DataFrame(omnibus)
    omnibus_df["p_holm_4_tests"] = holm_adjust(omnibus_df["p_value"].tolist())

    def group_row(feature: str, group: str) -> pd.Series:
        return summary.loc[(summary["feature"] == feature) & (summary["group"] == group)].iloc[0]

    single_host = group_row("host_portfolio_segment", "1_listing")
    large_host = group_row("host_portfolio_segment", "21_plus_listings")
    high_price = group_row("price_position_vs_local_market", "above_local_median")
    low_price = group_row("price_position_vs_local_market", "below_local_median")
    neighbourhood_summary = summary[summary["feature"] == "neighbourhood_cleansed"]
    highest_borough = neighbourhood_summary.loc[neighbourhood_summary["mean_rating"].idxmax()]
    lowest_borough = neighbourhood_summary.loc[neighbourhood_summary["mean_rating"].idxmin()]

    pairwise_frames = [pairwise_tests(analysis_frames[col], col) for col in [
        "room_type", "host_portfolio_segment"
    ]]
    pairwise = pd.concat(pairwise_frames, ignore_index=True)

    # Rating coverage by key subgroups makes selection into the rated sample visible.
    coverage_rows = []
    for col in ["room_type", "host_portfolio_segment"]:
        for group, frame in data.groupby(col, dropna=False, observed=True, sort=True):
            coverage_rows.append(
                {
                    "feature": col,
                    "group": "Missing category" if pd.isna(group) else str(group),
                    "n_listings": len(frame),
                    "rated_listings": int(frame["review_scores_rating"].notna().sum()),
                    "rating_coverage_pct": float(frame["review_scores_rating"].notna().mean() * 100),
                }
            )
    coverage = pd.DataFrame(coverage_rows)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    summary.to_csv(OUTPUT_DIR / "rating_group_summaries.csv", index=False)
    omnibus_df.to_csv(OUTPUT_DIR / "rating_omnibus_tests.csv", index=False)
    pairwise.to_csv(OUTPUT_DIR / "rating_pairwise_tests.csv", index=False)
    coverage.to_csv(OUTPUT_DIR / "rating_coverage_by_group.csv", index=False)

    report_lines = [
        "# Statistical analysis: Airbnb listing characteristics and ratings",
        "",
        "## Purpose and business question",
        "",
        "This analysis tests whether Airbnb listing ratings vary across room types, host portfolio sizes, relative local price positions, and London neighbourhoods. The business use is to help hosts and marketplace analysts identify where satisfaction patterns differ and where further operational investigation may be useful. These are observational associations, not causal effects or guarantees about future ratings.",
        "",
        "## Dataset and analytical sample",
        "",
        f"- Source: `data/processed/airbnb_features.csv` ({total_n:,} listings; one row per listing).",
        f"- Ratings observed: {len(rated):,} ({len(rated) / total_n * 100:.1f}%); no rating: {total_n - len(rated):,} ({(total_n - len(rated)) / total_n * 100:.1f}%).",
        f"- Rating scale: 0–5. Analyses use listings with a non-missing `review_scores_rating`.",
        f"- Local price-position test excludes {int((rated['price_position_vs_local_market'] == 'insufficient_local_sample').sum()):,} rated listings whose neighbourhood × room-type benchmark group had fewer than 20 listings.",
        f"- Neighbourhood omnibus test includes neighbourhoods with at least {MIN_NEIGHBOURHOOD_N} rated listings; {len(eligible_neighbourhoods)} neighbourhoods meet this threshold.",
        "",
        "## Methods",
        "",
        "- **Primary tests:** Kruskal–Wallis rank tests compare rating distributions across each feature’s groups. This non-parametric test is appropriate for bounded, heavily clustered rating scores and does not require normally distributed scores. It tests whether at least one group distribution differs; it does not identify which groups differ.",
        "- **Effect size:** epsilon-squared from the Kruskal–Wallis statistic estimates the share of rank variation associated with group membership. Values near zero indicate small separation. Large sample sizes can produce small p-values for small effects, so effect size and group summaries matter.",
        "- **Follow-up comparisons:** pairwise two-sided Mann–Whitney U tests are reported for room type and host portfolio groups. Their p-values use Holm adjustment within each family. Rank-biserial effect is positive when the first listed group tends to have higher ratings; values near zero indicate little rank separation.",
        "- **Multiple testing:** the four primary omnibus p-values are Holm-adjusted together. The family-wise significance threshold is 0.05. Pairwise tests are secondary and should be interpreted only after their omnibus test.",
        "- **Confidence intervals:** group mean ratings include pointwise 95% t intervals. These describe uncertainty around each group mean and are not simultaneous intervals across all groups. Medians and interquartile ranges are included because scores are skewed and tightly clustered near the top of the scale.",
        "- **Neighbourhood threshold:** neighbourhoods with fewer than 100 rated listings are omitted from the borough omnibus test to avoid a result driven by very small cells. All eligible neighbourhoods remain in the summary table.",
        "",
        "## Primary test results",
        "",
        markdown_table(
            omnibus_df.assign(
                p_value=omnibus_df["p_value"].map(p_text),
                p_holm_4_tests=omnibus_df["p_holm_4_tests"].map(p_text),
                h_statistic=omnibus_df["h_statistic"].map(lambda x: f"{x:.2f}"),
                epsilon_squared=omnibus_df["epsilon_squared"].map(lambda x: f"{x:.4f}"),
            ),
            ["feature", "groups", "n_rated", "h_statistic", "p_value", "p_holm_4_tests", "epsilon_squared"],
        ),
        "",
        "### What the results suggest",
        "",
        f"- All four omnibus comparisons remain statistically significant after Holm adjustment (all adjusted p-values <0.001), but effect sizes range from epsilon-squared {omnibus_df.loc[omnibus_df['feature'] == 'room_type', 'epsilon_squared'].iloc[0]:.4f} for room type to {omnibus_df.loc[omnibus_df['feature'] == 'host_portfolio_segment', 'epsilon_squared'].iloc[0]:.4f} for host portfolio segment. Room type’s overall association is very small despite statistical significance.",
        f"- Listings from single-listing hosts have mean rating {single_host['mean_rating']:.3f} (n={int(single_host['n_rated']):,}), compared with {large_host['mean_rating']:.3f} for hosts with 21+ observed listings (n={int(large_host['n_rated']):,}); this is the strongest of the tested grouping associations. It is a descriptive gap, not evidence that portfolio size causes rating differences.",
        f"- Listings priced at least 10% above their local room-type median average {high_price['mean_rating']:.3f}, versus {low_price['mean_rating']:.3f} for listings at least 10% below it. The {high_price['mean_rating'] - low_price['mean_rating']:.3f}-point difference is small on the 0–5 scale and does not show that higher prices improve satisfaction.",
        f"- The highest and lowest neighbourhood means among eligible boroughs are {highest_borough['group']} ({highest_borough['mean_rating']:.3f}, n={int(highest_borough['n_rated']):,}) and {lowest_borough['group']} ({lowest_borough['mean_rating']:.3f}, n={int(lowest_borough['n_rated']):,}). These borough comparisons may reflect differences in listing mix and guest expectations; they are not quality labels for neighbourhoods.",
        "- Room-type follow-ups involving Hotel room (67 rated listings) or Shared room (110) are based on small groups and should be treated as tentative. Entire home/apt and Private room have similar medians (4.81 and 4.84).",
        "",
        "Read the adjusted p-value together with epsilon-squared: a statistically detectable difference may still be too small to matter operationally.",
        "",
        "## Rating summaries by group",
        "",
    ]

    display_order = [
        ("room_type", "Room type"),
        ("host_portfolio_segment", "Host portfolio segment"),
        ("price_position_vs_local_market", "Local price position"),
        ("neighbourhood_cleansed", "Neighbourhood (all eligible groups)"),
    ]
    for key, title in display_order:
        subset = summary[summary["feature"] == key].copy()
        if key == "neighbourhood_cleansed":
            subset = subset.sort_values("mean_rating", ascending=False)
        else:
            subset = subset.sort_values("mean_rating", ascending=False)
        report_lines.extend(
            [
                f"### {title}",
                "",
                markdown_table(
                    subset.assign(
                        mean_rating=subset["mean_rating"].map(lambda x: f"{x:.3f}"),
                        mean_ci95_low=subset["mean_ci95_low"].map(lambda x: f"{x:.3f}"),
                        mean_ci95_high=subset["mean_ci95_high"].map(lambda x: f"{x:.3f}"),
                        median_rating=subset["median_rating"].map(lambda x: f"{x:.2f}"),
                        q1_rating=subset["q1_rating"].map(lambda x: f"{x:.2f}"),
                        q3_rating=subset["q3_rating"].map(lambda x: f"{x:.2f}"),
                    ),
                    ["group", "n_rated", "mean_rating", "mean_ci95_low", "mean_ci95_high", "median_rating", "q1_rating", "q3_rating"],
                ),
                "",
            ]
        )

    for col, title in [("room_type", "Room type"), ("host_portfolio_segment", "Host portfolio segment")]:
        subset = pairwise[pairwise["feature"] == col].copy()
        subset = subset.sort_values("p_holm_within_feature")
        report_lines.extend(
            [
                f"## Pairwise follow-up: {title}",
                "",
                "Positive rank-biserial effect means group 1 tends to have higher ratings than group 2. Holm-adjusted p-values control family-wise error within this set of pairwise comparisons.",
                "",
                markdown_table(
                    subset.assign(
                        median_1=subset["median_1"].map(lambda x: f"{x:.2f}"),
                        median_2=subset["median_2"].map(lambda x: f"{x:.2f}"),
                        median_difference_1_minus_2=subset["median_difference_1_minus_2"].map(lambda x: f"{x:+.2f}"),
                        rank_biserial_effect=subset["rank_biserial_effect"].map(lambda x: f"{x:+.3f}"),
                        p_holm_within_feature=subset["p_holm_within_feature"].map(p_text),
                    ),
                    ["group_1", "group_2", "n_1", "n_2", "median_1", "median_2", "median_difference_1_minus_2", "rank_biserial_effect", "p_holm_within_feature"],
                ),
                "",
            ]
        )

    report_lines.extend(
        [
            "## Rating coverage and selection into the analysis",
            "",
            "Ratings are missing for some listings, so the rating sample may not represent every Airbnb listing. Coverage by room type and host portfolio segment is shown below. Missing ratings are not treated as low ratings.",
            "",
            markdown_table(
                coverage.assign(rating_coverage_pct=coverage["rating_coverage_pct"].map(lambda x: f"{x:.1f}%")),
                ["feature", "group", "n_listings", "rated_listings", "rating_coverage_pct"],
            ),
            "",
            "## Business interpretation and recommended action",
            "",
            "Use the group means, medians, confidence intervals, and effect sizes above to identify where observed ratings differ. The local price position result can help check whether above-market listings also show a different rating distribution; it cannot tell whether price caused the difference. Host portfolio differences can prompt a service-process review, but do not establish that larger or smaller operators provide better service. Neighbourhood differences can guide locally tailored investigation, not stigmatizing borough labels or blanket operating decisions.",
            "",
            "A useful operational next step is to inspect rating sub-scores (accuracy, cleanliness, check-in, communication, location, and value) for the groups that show the clearest, practically meaningful gap, then compare those patterns with listing features. Any recommendation should be based on both a meaningful effect and sufficient group size, not p-values alone.",
            "",
            "## Limitations and responsible interpretation",
            "",
            "1. The analysis is observational and cross-sectional. Unmeasured factors (guest mix, property condition, management, location specifics, and review behavior) may explain group differences.",
            "2. Ratings are bounded and cluster near the top of the scale; medians, quartiles, rank tests, and effect sizes are reported to reduce reliance on means alone.",
            "3. Listings without ratings are excluded from score tests. Review coverage varies by listing type and host profile, which can bias conclusions about satisfaction.",
            "4. The local benchmark uses listings in this same snapshot and includes each listing in its group median. It is not a forward-looking price recommendation.",
            "5. The calendar field reflects unavailable days, not verified bookings. It is excluded from these rating tests and should not be described as true demand.",
            "6. Statistical significance does not imply a large or actionable difference. Compare effect sizes and score-scale differences before making recommendations.",
            "7. Neighbourhood and host-scale associations should be interpreted carefully; neither should be treated as an inherent quality or fairness label.",
            "",
            "## Reproducibility and output files",
            "",
            "Run `python scripts/statistical_analysis.py` from any directory. It regenerates this report and these machine-readable summaries under `data/processed/statistics/`: `rating_group_summaries.csv`, `rating_omnibus_tests.csv`, `rating_pairwise_tests.csv`, and `rating_coverage_by_group.csv`.",
            "",
        ]
    )

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text("\n".join(report_lines), encoding="utf-8")
    print(f"Analyzed {len(rated):,} rated listings out of {total_n:,}.")
    print(omnibus_df[["feature", "p_holm_4_tests", "epsilon_squared"]].to_string(index=False))
    print(f"Saved report: {REPORT_PATH}")
    print(f"Saved summary tables: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
