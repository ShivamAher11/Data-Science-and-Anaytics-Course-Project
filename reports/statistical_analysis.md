# Statistical analysis: Airbnb listing characteristics and ratings

## Purpose and business question

This analysis tests whether Airbnb listing ratings vary across room types, host portfolio sizes, relative local price positions, and London neighbourhoods. The business use is to help hosts and marketplace analysts identify where satisfaction patterns differ and where further operational investigation may be useful. These are observational associations, not causal effects or guarantees about future ratings.

## Dataset and analytical sample

- Source: `data/processed/airbnb_features.csv` (61,617 listings; one row per listing).
- Ratings observed: 48,322 (78.4%); no rating: 13,295 (21.6%).
- Rating scale: 0–5. Analyses use listings with a non-missing `review_scores_rating`.
- Local price-position test excludes 148 rated listings whose neighbourhood × room-type benchmark group had fewer than 20 listings.
- Neighbourhood omnibus test includes neighbourhoods with at least 100 rated listings; 33 neighbourhoods meet this threshold.

## Methods

- **Primary tests:** Kruskal–Wallis rank tests compare rating distributions across each feature’s groups. This non-parametric test is appropriate for bounded, heavily clustered rating scores and does not require normally distributed scores. It tests whether at least one group distribution differs; it does not identify which groups differ.
- **Effect size:** epsilon-squared from the Kruskal–Wallis statistic estimates the share of rank variation associated with group membership. Values near zero indicate small separation. Large sample sizes can produce small p-values for small effects, so effect size and group summaries matter.
- **Follow-up comparisons:** pairwise two-sided Mann–Whitney U tests are reported for room type and host portfolio groups. Their p-values use Holm adjustment within each family. Rank-biserial effect is positive when the first listed group tends to have higher ratings; values near zero indicate little rank separation.
- **Multiple testing:** the four primary omnibus p-values are Holm-adjusted together. The family-wise significance threshold is 0.05. Pairwise tests are secondary and should be interpreted only after their omnibus test.
- **Confidence intervals:** group mean ratings include pointwise 95% t intervals. These describe uncertainty around each group mean and are not simultaneous intervals across all groups. Medians and interquartile ranges are included because scores are skewed and tightly clustered near the top of the scale.
- **Neighbourhood threshold:** neighbourhoods with fewer than 100 rated listings are omitted from the borough omnibus test to avoid a result driven by very small cells. All eligible neighbourhoods remain in the summary table.

## Primary test results

| feature                        | groups | n_rated | h_statistic | p_value | p_holm_4_tests | epsilon_squared |
| ------------------------------ | ------ | ------- | ----------- | ------- | -------------- | --------------- |
| room_type                      | 4      | 48322   | 75.11       | <0.001  | <0.001         | 0.0015          |
| host_portfolio_segment         | 4      | 48322   | 4500.70     | <0.001  | <0.001         | 0.0931          |
| price_position_vs_local_market | 3      | 48174   | 703.32      | <0.001  | <0.001         | 0.0146          |
| neighbourhood_cleansed         | 33     | 48322   | 1334.09     | <0.001  | <0.001         | 0.0270          |

### What the results suggest

- All four omnibus comparisons remain statistically significant after Holm adjustment (all adjusted p-values <0.001), but effect sizes range from epsilon-squared 0.0015 for room type to 0.0931 for host portfolio segment. Room type’s overall association is very small despite statistical significance.
- Listings from single-listing hosts have mean rating 4.786 (n=17,411), compared with 4.494 for hosts with 21+ observed listings (n=8,343); this is the strongest of the tested grouping associations. It is a descriptive gap, not evidence that portfolio size causes rating differences.
- Listings priced at least 10% above their local room-type median average 4.709, versus 4.633 for listings at least 10% below it. The 0.076-point difference is small on the 0–5 scale and does not show that higher prices improve satisfaction.
- The highest and lowest neighbourhood means among eligible boroughs are Richmond upon Thames (4.812, n=681) and Barking and Dagenham (4.551, n=341). These borough comparisons may reflect differences in listing mix and guest expectations; they are not quality labels for neighbourhoods.
- Room-type follow-ups involving Hotel room (67 rated listings) or Shared room (110) are based on small groups and should be treated as tentative. Entire home/apt and Private room have similar medians (4.81 and 4.84).

Read the adjusted p-value together with epsilon-squared: a statistically detectable difference may still be too small to matter operationally.

## Rating summaries by group

### Room type

| group           | n_rated | mean_rating | mean_ci95_low | mean_ci95_high | median_rating | q1_rating | q3_rating |
| --------------- | ------- | ----------- | ------------- | -------------- | ------------- | --------- | --------- |
| Entire home/apt | 33046   | 4.676       | 4.671         | 4.682          | 4.81          | 4.58      | 5.00      |
| Private room    | 15099   | 4.660       | 4.651         | 4.668          | 4.84          | 4.57      | 4.99      |
| Shared room     | 110     | 4.424       | 4.298         | 4.550          | 4.58          | 4.18      | 4.88      |
| Hotel room      | 67      | 4.326       | 4.160         | 4.492          | 4.50          | 4.19      | 4.75      |

### Host portfolio segment

| group            | n_rated | mean_rating | mean_ci95_low | mean_ci95_high | median_rating | q1_rating | q3_rating |
| ---------------- | ------- | ----------- | ------------- | -------------- | ------------- | --------- | --------- |
| 1_listing        | 17411   | 4.786       | 4.779         | 4.792          | 4.91          | 4.75      | 5.00      |
| 2_to_5_listings  | 12955   | 4.695       | 4.686         | 4.703          | 4.83          | 4.62      | 4.99      |
| 6_to_20_listings | 9613    | 4.581       | 4.570         | 4.592          | 4.71          | 4.47      | 4.91      |
| 21_plus_listings | 8343    | 4.494       | 4.481         | 4.506          | 4.64          | 4.33      | 4.86      |

### Local price position

| group              | n_rated | mean_rating | mean_ci95_low | mean_ci95_high | median_rating | q1_rating | q3_rating |
| ------------------ | ------- | ----------- | ------------- | -------------- | ------------- | --------- | --------- |
| above_local_median | 19477   | 4.709       | 4.702         | 4.716          | 4.87          | 4.65      | 5.00      |
| near_local_median  | 8220    | 4.675       | 4.664         | 4.686          | 4.82          | 4.59      | 5.00      |
| below_local_median | 20477   | 4.633       | 4.626         | 4.640          | 4.77          | 4.51      | 4.95      |

### Neighbourhood (all eligible groups)

| group                  | n_rated | mean_rating | mean_ci95_low | mean_ci95_high | median_rating | q1_rating | q3_rating |
| ---------------------- | ------- | ----------- | ------------- | -------------- | ------------- | --------- | --------- |
| Richmond upon Thames   | 681     | 4.812       | 4.787         | 4.837          | 4.92          | 4.78      | 5.00      |
| Wandsworth             | 2271    | 4.780       | 4.763         | 4.796          | 4.91          | 4.73      | 5.00      |
| Kingston upon Thames   | 366     | 4.768       | 4.728         | 4.809          | 4.89          | 4.73      | 5.00      |
| Merton                 | 774     | 4.765       | 4.734         | 4.796          | 4.92          | 4.70      | 5.00      |
| Bromley                | 489     | 4.761       | 4.723         | 4.798          | 4.90          | 4.71      | 5.00      |
| Hackney                | 2449    | 4.749       | 4.734         | 4.765          | 4.88          | 4.67      | 5.00      |
| Sutton                 | 266     | 4.746       | 4.697         | 4.794          | 4.88          | 4.67      | 5.00      |
| Waltham Forest         | 913     | 4.740       | 4.711         | 4.769          | 4.89          | 4.67      | 5.00      |
| Lewisham               | 1180    | 4.720       | 4.692         | 4.748          | 4.88          | 4.67      | 5.00      |
| Haringey               | 1232    | 4.717       | 4.689         | 4.745          | 4.87          | 4.67      | 5.00      |
| Lambeth                | 2392    | 4.715       | 4.696         | 4.734          | 4.85          | 4.63      | 5.00      |
| Hounslow               | 738     | 4.705       | 4.669         | 4.742          | 4.86          | 4.67      | 5.00      |
| Bexley                 | 355     | 4.703       | 4.658         | 4.748          | 4.85          | 4.60      | 5.00      |
| Enfield                | 506     | 4.696       | 4.654         | 4.738          | 4.85          | 4.60      | 5.00      |
| Southwark              | 2580    | 4.691       | 4.673         | 4.709          | 4.82          | 4.60      | 4.98      |
| Hammersmith and Fulham | 2173    | 4.686       | 4.666         | 4.706          | 4.82          | 4.60      | 5.00      |
| Harrow                 | 379     | 4.681       | 4.628         | 4.734          | 4.83          | 4.58      | 5.00      |
| Islington              | 2281    | 4.677       | 4.658         | 4.696          | 4.80          | 4.58      | 4.95      |
| Kensington and Chelsea | 3506    | 4.671       | 4.656         | 4.687          | 4.80          | 4.57      | 4.96      |
| Greenwich              | 949     | 4.664       | 4.623         | 4.705          | 4.86          | 4.65      | 5.00      |
| Brent                  | 1657    | 4.663       | 4.637         | 4.688          | 4.84          | 4.58      | 5.00      |
| Ealing                 | 1277    | 4.659       | 4.630         | 4.688          | 4.83          | 4.54      | 5.00      |
| Tower Hamlets          | 3221    | 4.640       | 4.622         | 4.659          | 4.79          | 4.51      | 4.96      |
| Barnet                 | 1314    | 4.640       | 4.607         | 4.673          | 4.80          | 4.57      | 5.00      |
| Newham                 | 1285    | 4.626       | 4.589         | 4.662          | 4.81          | 4.57      | 5.00      |
| Westminster            | 6376    | 4.608       | 4.595         | 4.621          | 4.75          | 4.50      | 4.93      |
| Camden                 | 3728    | 4.598       | 4.581         | 4.614          | 4.73          | 4.47      | 4.92      |
| Croydon                | 944     | 4.591       | 4.547         | 4.635          | 4.83          | 4.50      | 5.00      |
| Redbridge              | 534     | 4.586       | 4.526         | 4.645          | 4.82          | 4.50      | 5.00      |
| City of London         | 333     | 4.581       | 4.529         | 4.634          | 4.68          | 4.46      | 4.89      |
| Hillingdon             | 562     | 4.565       | 4.515         | 4.615          | 4.75          | 4.39      | 5.00      |
| Havering               | 270     | 4.562       | 4.466         | 4.658          | 4.84          | 4.52      | 5.00      |
| Barking and Dagenham   | 341     | 4.551       | 4.473         | 4.630          | 4.78          | 4.50      | 5.00      |

## Pairwise follow-up: Room type

Positive rank-biserial effect means group 1 tends to have higher ratings than group 2. Holm-adjusted p-values control family-wise error within this set of pairwise comparisons.

| group_1         | group_2      | n_1   | n_2   | median_1 | median_2 | median_difference_1_minus_2 | rank_biserial_effect | p_holm_within_feature |
| --------------- | ------------ | ----- | ----- | -------- | -------- | --------------------------- | -------------------- | --------------------- |
| Entire home/apt | Hotel room   | 33046 | 67    | 4.81     | 4.50     | +0.31                       | +0.448               | <0.001                |
| Hotel room      | Private room | 67    | 15099 | 4.50     | 4.84     | -0.34                       | -0.440               | <0.001                |
| Entire home/apt | Shared room  | 33046 | 110   | 4.81     | 4.58     | +0.23                       | +0.310               | <0.001                |
| Private room    | Shared room  | 15099 | 110   | 4.84     | 4.58     | +0.26                       | +0.306               | <0.001                |
| Entire home/apt | Private room | 33046 | 15099 | 4.81     | 4.84     | -0.03                       | -0.009               | 0.194                 |
| Hotel room      | Shared room  | 67    | 110   | 4.50     | 4.58     | -0.08                       | -0.107               | 0.233                 |

## Pairwise follow-up: Host portfolio segment

Positive rank-biserial effect means group 1 tends to have higher ratings than group 2. Holm-adjusted p-values control family-wise error within this set of pairwise comparisons.

| group_1          | group_2          | n_1   | n_2   | median_1 | median_2 | median_difference_1_minus_2 | rank_biserial_effect | p_holm_within_feature |
| ---------------- | ---------------- | ----- | ----- | -------- | -------- | --------------------------- | -------------------- | --------------------- |
| 1_listing        | 21_plus_listings | 17411 | 8343  | 4.91     | 4.64     | +0.27                       | +0.439               | <0.001                |
| 1_listing        | 6_to_20_listings | 17411 | 9613  | 4.91     | 4.71     | +0.20                       | +0.356               | <0.001                |
| 21_plus_listings | 2_to_5_listings  | 8343  | 12955 | 4.64     | 4.83     | -0.19                       | -0.287               | <0.001                |
| 1_listing        | 2_to_5_listings  | 17411 | 12955 | 4.91     | 4.83     | +0.08                       | +0.186               | <0.001                |
| 2_to_5_listings  | 6_to_20_listings | 12955 | 9613  | 4.83     | 4.71     | +0.12                       | +0.187               | <0.001                |
| 21_plus_listings | 6_to_20_listings | 8343  | 9613  | 4.64     | 4.71     | -0.07                       | -0.110               | <0.001                |

## Rating coverage and selection into the analysis

Ratings are missing for some listings, so the rating sample may not represent every Airbnb listing. Coverage by room type and host portfolio segment is shown below. Missing ratings are not treated as low ratings.

| feature                | group            | n_listings | rated_listings | rating_coverage_pct |
| ---------------------- | ---------------- | ---------- | -------------- | ------------------- |
| room_type              | Entire home/apt  | 41732      | 33046          | 79.2%               |
| room_type              | Hotel room       | 108        | 67             | 62.0%               |
| room_type              | Private room     | 19637      | 15099          | 76.9%               |
| room_type              | Shared room      | 140        | 110            | 78.6%               |
| host_portfolio_segment | 1_listing        | 22738      | 17411          | 76.6%               |
| host_portfolio_segment | 21_plus_listings | 10987      | 8343           | 75.9%               |
| host_portfolio_segment | 2_to_5_listings  | 16003      | 12955          | 81.0%               |
| host_portfolio_segment | 6_to_20_listings | 11889      | 9613           | 80.9%               |

## Business interpretation and recommended action

Use the group means, medians, confidence intervals, and effect sizes above to identify where observed ratings differ. The local price position result can help check whether above-market listings also show a different rating distribution; it cannot tell whether price caused the difference. Host portfolio differences can prompt a service-process review, but do not establish that larger or smaller operators provide better service. Neighbourhood differences can guide locally tailored investigation, not stigmatizing borough labels or blanket operating decisions.

A useful operational next step is to inspect rating sub-scores (accuracy, cleanliness, check-in, communication, location, and value) for the groups that show the clearest, practically meaningful gap, then compare those patterns with listing features. Any recommendation should be based on both a meaningful effect and sufficient group size, not p-values alone.

## Limitations and responsible interpretation

1. The analysis is observational and cross-sectional. Unmeasured factors (guest mix, property condition, management, location specifics, and review behavior) may explain group differences.
2. Ratings are bounded and cluster near the top of the scale; medians, quartiles, rank tests, and effect sizes are reported to reduce reliance on means alone.
3. Listings without ratings are excluded from score tests. Review coverage varies by listing type and host profile, which can bias conclusions about satisfaction.
4. The local benchmark uses listings in this same snapshot and includes each listing in its group median. It is not a forward-looking price recommendation.
5. The calendar field reflects unavailable days, not verified bookings. It is excluded from these rating tests and should not be described as true demand.
6. Statistical significance does not imply a large or actionable difference. Compare effect sizes and score-scale differences before making recommendations.
7. Neighbourhood and host-scale associations should be interpreted carefully; neither should be treated as an inherent quality or fairness label.

## Reproducibility and output files

Open `scripts/statistical_analysis.ipynb` in Jupyter and run its cells in order. It regenerates this report and these machine-readable summaries under `data/processed/statistics/`: `rating_group_summaries.csv`, `rating_omnibus_tests.csv`, `rating_pairwise_tests.csv`, and `rating_coverage_by_group.csv`.
