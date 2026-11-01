# Business insights and recommendations

## Decision question

Where should Airbnb hosts and marketplace operations focus service-improvement work, based on the rating patterns in this London listing snapshot?

## Evidence used

- Listing-level Airbnb snapshot: 61,617 listings; 48,322 have an overall rating (78.4%).
- Overall rating and six sub-scores (accuracy, cleanliness, check-in, communication, location, value) are on a 0–5 scale.
- The main descriptive contrast is between hosts with one observed listing and hosts with 21+ observed listings. Portfolio size is measured only inside this dataset.
- Sub-score group comparisons use Kruskal–Wallis tests and Holm adjustment across six sub-scores. Mean 95% intervals are pointwise descriptive intervals; epsilon-squared summarizes rank separation.

## What the data says

1. The overall rating mean is 4.786 for single-listing hosts and 4.494 for 21+ listing hosts, a 0.292-point observed gap. This is the strongest grouping association in the preceding statistical analysis, but it is not a causal host-size effect.
2. The largest single-versus-21+ gap among the six sub-scores is **Value** (0.296 points), followed by **Accuracy** (0.248 points). This suggests the most useful first operational checks are whether the listing description matches the stay and whether guests feel the price matches what they received.
3. Lower sub-scores also appear across multiple dimensions for larger portfolio segments. That pattern is consistent with a potential standardization or consistency opportunity, but could also reflect differences in room type, borough, price, guest mix, and rating coverage.
4. Communication and check-in scores are relatively higher than value and cleanliness scores in the large-portfolio segment. A blanket recommendation to improve every service dimension equally would therefore be less targeted than starting with the larger observed gaps.

### Overall score by host segment

| host_portfolio_segment | n_rated | mean_rating | rating_coverage |
| ---------------------- | ------- | ----------- | --------------- |
| 1_listing              | 17411   | 4.786       | 76.6%           |
| 2_to_5_listings        | 12955   | 4.695       | 81.0%           |
| 6_to_20_listings       | 9613    | 4.581       | 80.9%           |
| 21_plus_listings       | 8343    | 4.494       | 75.9%           |

### Sub-score differences by host segment

Means and pointwise 95% confidence intervals are listed with medians and quartiles to show the rating distribution, not only its average.

| subscore      | portfolio_segment | n     | mean  | mean_ci95_low | mean_ci95_high | median | q1    | q3    |
| ------------- | ----------------- | ----- | ----- | ------------- | -------------- | ------ | ----- | ----- |
| Accuracy      | 1_listing         | 17410 | 4.806 | 4.800         | 4.812          | 4.930  | 4.790 | 5.000 |
| Accuracy      | 2_to_5_listings   | 12954 | 4.724 | 4.716         | 4.732          | 4.860  | 4.670 | 5.000 |
| Accuracy      | 6_to_20_listings  | 9613  | 4.628 | 4.617         | 4.638          | 4.760  | 4.530 | 4.930 |
| Accuracy      | 21_plus_listings  | 8343  | 4.558 | 4.546         | 4.571          | 4.710  | 4.450 | 4.900 |
| Cleanliness   | 1_listing         | 17410 | 4.733 | 4.727         | 4.740          | 4.880  | 4.670 | 5.000 |
| Cleanliness   | 2_to_5_listings   | 12954 | 4.668 | 4.659         | 4.676          | 4.810  | 4.570 | 4.980 |
| Cleanliness   | 6_to_20_listings  | 9613  | 4.598 | 4.588         | 4.609          | 4.740  | 4.500 | 4.930 |
| Cleanliness   | 21_plus_listings  | 8343  | 4.539 | 4.527         | 4.552          | 4.690  | 4.390 | 4.910 |
| Check-in      | 1_listing         | 17409 | 4.847 | 4.841         | 4.852          | 4.960  | 4.840 | 5.000 |
| Check-in      | 2_to_5_listings   | 12953 | 4.797 | 4.790         | 4.804          | 4.920  | 4.790 | 5.000 |
| Check-in      | 6_to_20_listings  | 9613  | 4.730 | 4.721         | 4.739          | 4.870  | 4.670 | 5.000 |
| Check-in      | 21_plus_listings  | 8343  | 4.686 | 4.676         | 4.697          | 4.830  | 4.620 | 5.000 |
| Communication | 1_listing         | 17410 | 4.876 | 4.870         | 4.881          | 4.990  | 4.890 | 5.000 |
| Communication | 2_to_5_listings   | 12954 | 4.820 | 4.813         | 4.828          | 4.940  | 4.810 | 5.000 |
| Communication | 6_to_20_listings  | 9613  | 4.741 | 4.731         | 4.750          | 4.880  | 4.700 | 5.000 |
| Communication | 21_plus_listings  | 8343  | 4.676 | 4.664         | 4.687          | 4.840  | 4.620 | 5.000 |
| Location      | 1_listing         | 17410 | 4.781 | 4.776         | 4.786          | 4.880  | 4.710 | 5.000 |
| Location      | 2_to_5_listings   | 12953 | 4.728 | 4.721         | 4.735          | 4.830  | 4.660 | 4.970 |
| Location      | 6_to_20_listings  | 9612  | 4.703 | 4.695         | 4.712          | 4.820  | 4.600 | 5.000 |
| Location      | 21_plus_listings  | 8343  | 4.680 | 4.671         | 4.690          | 4.810  | 4.570 | 5.000 |
| Value         | 1_listing         | 17410 | 4.713 | 4.706         | 4.719          | 4.820  | 4.660 | 4.960 |
| Value         | 2_to_5_listings   | 12953 | 4.630 | 4.622         | 4.639          | 4.750  | 4.540 | 4.900 |
| Value         | 6_to_20_listings  | 9613  | 4.514 | 4.503         | 4.524          | 4.630  | 4.400 | 4.810 |
| Value         | 21_plus_listings  | 8343  | 4.416 | 4.403         | 4.429          | 4.550  | 4.270 | 4.750 |

### Tests across host segments for each sub-score

| subscore      | n     | h_statistic | p_holm_6_subscores | epsilon_squared |
| ------------- | ----- | ----------- | ------------------ | --------------- |
| Accuracy      | 48320 | 3797.09     | <0.001             | 0.0785          |
| Cleanliness   | 48320 | 1785.33     | <0.001             | 0.0369          |
| Check-in      | 48318 | 2255.90     | <0.001             | 0.0466          |
| Communication | 48320 | 3491.89     | <0.001             | 0.0722          |
| Location      | 48318 | 524.50      | <0.001             | 0.0108          |
| Value         | 48319 | 4276.30     | <0.001             | 0.0884          |

The tests show that rating distributions differ across host portfolio segments; they do not show that portfolio size caused the differences. The large sample can make small differences statistically significant, so use the score gaps and effect sizes to judge business relevance.

## Recommended business actions

### 1. Start with a listing accuracy and value-for-money audit

The biggest observed single-versus-large-host sub-score gap is Value (0.296 points); Accuracy is next (0.248). For listings with low scores in those areas, check that photos, amenities, capacity, house rules, and location description match the actual stay, and review whether the price and fees align with what the listing promises.
**Purpose:** reduce avoidable expectation mismatch and identify concrete listing details hosts can correct. This is a diagnostic recommendation; the data does not prove that making these changes will raise ratings.

### 2. Help multi-listing operators standardize the guest journey

Offer a reusable pre-arrival checklist for listing accuracy, cleanliness readiness, arrival instructions, and issue escalation. Focus the initial pilot on hosts with 6+ listings, but compare similar room types and boroughs so the group-level pattern is not mistaken for an operator-size effect.
**Purpose:** test whether repeatable processes reduce inconsistency across a larger portfolio. Avoid describing multi-listing hosts as inherently worse; portfolio segment is an observed scale bucket, not a quality or legality label.

### 3. Pilot and measure before scaling

Run a small opt-in pilot with hosts who choose to review their listing accuracy and value messaging. Record a baseline, track adoption, and compare subsequent sub-scores with a similar non-pilot group over the same period. Predefine the measures: change in accuracy/value sub-score, share of listings completing the checklist, and guest complaint themes if available. Account for review counts and seasonality, and do not claim success from a few new reviews.
**Purpose:** distinguish a plausible recommendation from one that has evidence of operational benefit.

## Dashboard implications

A decision-focused dashboard should let a host or analyst filter by room type, neighbourhood, and host portfolio segment, and show: (a) overall rating and six sub-scores with group counts; (b) local price position and ratings together; (c) rating coverage/missingness; and (d) the benchmark against the London listing sample. Clearly label the portfolio comparison as observational and the calendar metric as an unavailability proxy. Suppress exact host IDs and listing locations; report aggregated groups only.

## Fairness, privacy, and limits

- Ratings are self-selected guest feedback and are not a complete census of each stay. 21.6% of all Airbnb listings lack an overall rating; missing scores are not low scores.
- Sub-score and overall-rating gaps may reflect room type, borough, nightly price, guest expectations, property age, or review propensity. This analysis does not adjust for those factors and cannot establish causes.
- Small categories have less stable estimates. Avoid broad recommendations for rare property/room types without collecting more evidence.
- Host identifiers, exact coordinates, and guest-level review text should not appear in a public dashboard. Use aggregate counts and score summaries; avoid exposing small groups that could identify a host.
- A score should guide voluntary service review, not automatic penalties, ranking changes, or claims that a neighbourhood or host group is inherently low quality.

## Reproducibility

Run `python scripts/business_insights.py`. It writes this report and two CSV tables under `data/processed/statistics/`: `subscore_host_segment_summary.csv` and `subscore_host_segment_tests.csv`.
