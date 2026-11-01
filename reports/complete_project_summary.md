# Decoding the Stay Economy
## Complete Course Project Summary

**Project type:** Exploratory data analysis, statistical analysis, business recommendations, and machine learning  
**Primary study area:** Airbnb listings in London  
**Supporting comparison:** London Booking.com hotel reviews  
**Main decision question:** Which listing and host profiles show weaker guest-perceived value, and where should hosts or marketplace operators investigate service and value messaging?

---

## Executive summary

This project studies short-stay accommodation data to find useful patterns in listing prices, listing characteristics, guest ratings, and host portfolio size. The Airbnb analysis uses one row per listing. Booking.com reviews are a secondary source for limited platform context; because the datasets have different grains, time periods, and available fields, they do not support a clean price or overall-quality contest between platforms.

The analysis found a descriptive association between host portfolio segment and ratings. Single-listing hosts had a mean overall score of 4.786/5, compared with 4.494/5 for hosts with 21 or more listings in this dataset snapshot. The largest sub-score gap was perceived value (4.713 versus 4.416); accuracy was next (4.806 versus 4.558). These are observational gaps and do not establish that portfolio size caused lower ratings.

Two supervised learning experiments were completed around Airbnb's guest value score:

1. **Regression:** estimate a listing's 0–5 value rating from listing and host characteristics. Results are weak: the tuned Random Forest achieved MAE 0.2946 and R² 0.0778 on a host-held-out test set, only a small improvement over the median baseline.
2. **Classification:** flag listings whose value score falls at or below the training-set 25th percentile. In repeated host-grouped validation, average precision was 0.4633 ± 0.0218, ROC-AUC 0.7106 ± 0.0084, and the top 10% of risk scores had 1.97× the low-value rate of the validation population.

The classifier shows a repeatable ranking signal across host groups, but it is not reliable enough to judge individual listings or hosts. The practical recommendation is to guide aggregate investigation and a voluntary pilot around listing accuracy and value messaging, then evaluate changes using later data.

---

## 1. Problem formulation

### Business problem and analytical question

Hosts and short-stay operators need to understand which parts of the guest experience may warrant review. A broad average rating does not show whether guests are particularly dissatisfied with value, listing accuracy, cleanliness, communication, or check-in.

> **Can listing and host characteristics help identify profiles associated with lower guest-perceived value, so operators can prioritize a voluntary review of listing accuracy, amenities, and value messaging?**

The prediction target is review_scores_value, a guest-provided score from 0 to 5. For the business-focused classifier, “low value” is defined relative to training data: a score at or below that training fold's 25th percentile. This is a triage label for this project, not an industry quality standard.

The model can help identify aggregate patterns and prioritize which profiles to investigate. It does not measure objective property quality or safety, prove why a guest assigned a score, recommend an optimal nightly price, or justify automatically ranking, penalizing, delisting, or changing visibility for a host or listing.

---

## 2. Data collection

### Sources

- **Inside Airbnb — London:** listings.csv, calendar.csv, and reviews.csv from [Inside Airbnb](https://insideairbnb.com/get-the-data/). They provide listing attributes, host/listing information, calendar availability, and guest review information. The data is periodically refreshed.
- **Booking.com hotel reviews:** multi-city dataset from [Kaggle](https://www.kaggle.com/datasets/jiashenliu/515k-hotel-reviews-data-in-europe), filtered to London using hotel address. It includes review scores and written review fields from 2015–2017.

### Scale, grain, and limitations

- Raw Inside Airbnb listings: 92,638 rows and 90 columns in the inspected file.
- Clean Airbnb listing table: 61,617 listings, one row per listing.
- Airbnb overall ratings: 48,322 listings with a score (78.4%); 13,295 (21.6%) have no overall rating.
- Booking.com: 515,738 rows across six cities; 262,301 London rows before duplicate removal and 262,298 after.
- Combined comparison schema: 323,915 rows—61,617 Airbnb listing records and 262,298 Booking.com review records.

Airbnb is listing-level while Booking.com is review-level. Booking.com has no equivalent nightly price or guest capacity in this dataset, and its review period predates the Airbnb snapshot. Platform comparison is therefore limited to compatible review signals and must be qualified. Neither source is a randomized sample of stays.

---

## 3. Data cleaning and preprocessing

The workflow is implemented in scripts/clean_and_align_full_script.ipynb; the cleaning log is reports/cleaning.txt.

### Airbnb

- Selected useful fields from the 90-column source.
- Price was missing for 32.8% of raw listing rows; rows without price were dropped.
- Kept nightly prices from £30 to £2,008, removing 623 rows outside this analysis range.
- Found no duplicate listing IDs among retained listings.
- Final cleaned Airbnb table: **61,617 rows**.
- Preserved the 0–5 score scale and left missing ratings missing. No rating is unknown, not zero or low.

### Booking.com and schema alignment

- Filtered the six-city source to London.
- Extracted trip type where possible; 3.5% remained missing.
- Removed three exact duplicate rows; final London table: **262,298 rows**.
- Aggregated Airbnb calendar and review data to listing grain before joining to create the Airbnb master table. A shared comparison schema is created where fields can be aligned.

### Missing fields and calendar interpretation

Host tenure, licence, neighbourhood overview, response/acceptance fields, and instant_bookable were entirely missing in the available listing snapshot. The source has one primary picture URL, not a photo count. These fields were not fabricated. Numeric feature missingness is handled by training-fitted imputation in model pipelines.

Calendar unavailability may mean a booking, a host block, or another reason. It is an **unavailability proxy**, not verified occupancy, booked nights, demand, or proof of legal compliance.

---

## 4. Exploratory Data Analysis (EDA)

EDA is in scripts/eda_visualization.ipynb. The notebook explains chart choices and includes statistical checks for selected comparisons.

### Charts and purpose

- **Price by room type — boxplot:** compares median, interquartile spread, and variation while reducing the visual effect of extreme values.
- **Median price by borough — horizontal ranked bar chart:** makes borough price comparisons readable.
- **Guest-perceived value by host portfolio segment — boxplot:** shows score spread and group sizes behind the main business insight.
- **Price versus overall rating — scatter plot:** exploratory price context; it uses overall rating rather than the ML target and cannot show a causal price effect.
- **Price by room type and median price by borough:** describe market context for the listings.
- **Calendar unavailability proxy — histogram:** shows unavailable dates, which may include bookings, host blocks, or other reasons.
- **Cross-platform summary table:** retained as limited context; different record grains and periods prevent a direct platform-quality comparison.

### Main EDA pattern

| Host listings in snapshot | Mean overall rating | Rated listings |
|---|---:|---:|
| 1 | 4.786 / 5 | 17,411 |
| 2–5 | 4.695 / 5 | 12,955 |
| 6–20 | 4.581 / 5 | 9,613 |
| 21+ | 4.494 / 5 | 8,343 |

The value sub-score gap between single-listing and 21+ hosts was 0.296 points (4.713 versus 4.416); accuracy was next at 0.248 (4.806 versus 4.558). These findings motivated follow-up of guest expectations, listing accuracy, amenities, and value messaging. They do not establish causality.

Scores are bounded and concentrated near 5, so distributions, medians, counts, and sub-scores are more informative than a single average. Small categories, especially hotel and shared room types, should not be confidently ranked.

---

## 5. Feature engineering

Feature engineering is implemented in scripts/feature_engineering.ipynb. Full calculations and reasons are in reports/feature_engineering.md. Output: data/processed/airbnb_features.csv, 61,617 one-listing rows.

| Feature | Purpose | Limitation |
|---|---|---|
| host_listing_count and host_portfolio_segment | Compare observed host portfolio scale. | Counts only listings in this snapshot; not a quality or legality label. |
| local_room_type_price_median_gbp, price_vs_local_median_pct, price_position_vs_local_market | Describe price relative to same-neighbourhood, same-room-type listings. | Snapshot benchmark includes the listing itself; not an optimal price. |
| listed_price_per_guest_gbp | Capacity-adjusted advertised nightly price. | Assumes full capacity; excludes fees and actual guest count. |
| calendar_unavailability_rate_proxy and band | Summarize unavailable dates for descriptive context. | Does not distinguish bookings from host blocks. |
| days_since_latest_observed_review and review_activity_band | Context about observed review recency/activity. | Not a full booking history; excluded from model predictors to avoid outcome leakage. |
| amenity_count and selected amenity flags | Measure breadth/presence of advertised facilities without raw amenity text. | “Not listed” may not mean “not present”; quality is not measured. |
| description_length_chars and description_word_count | Test whether amount of listing detail is associated with value score without using free text. | Length is not truth, clarity, or quality. |
| bathroom_privacy | Capture shared/private/unspecified bathroom information that shapes expectations. | Unspecified is not assumed private. |

Model features also include listing attributes such as neighbourhood, room/property type, price, capacity, bedrooms, beds, bathrooms, minimum/maximum nights, and host listing count. Raw free text, IDs, exact coordinates, and review-derived fields are excluded.

---

## 6. Statistical analysis

Implemented in scripts/statistical_analysis.ipynb and reported in reports/statistical_analysis.md.

### Method

Kruskal–Wallis tests compare rating distributions across room types, host portfolio segments, local price-position groups, and neighbourhoods. Holm adjustment controls multiple comparisons across the four primary tests. Epsilon-squared summarizes rank separation. Mann–Whitney U tests with Holm correction provide pairwise follow-up for room type and host segment. The report includes means, pointwise 95% confidence intervals, medians, quartiles, and rating coverage.

### Primary results

| Grouping | Groups | Rated listings | Epsilon-squared | Interpretation |
|---|---:|---:|---:|---|
| Room type | 4 | 48,322 | 0.0015 | Statistically detectable, very small association. |
| Host portfolio segment | 4 | 48,322 | 0.0931 | Largest tested association. |
| Price position vs local market | 3 | 48,174 | 0.0146 | Small association; not causal evidence. |
| Neighbourhood | 33 | 48,322 | 0.0270 | Small association; not a neighbourhood quality label. |

All four omnibus tests had Holm-adjusted p-values below 0.001. Listings at least 10% above their local room-type median averaged 4.709, versus 4.633 for listings at least 10% below it, a small 0.076-point difference. Richmond upon Thames had the highest eligible borough mean (4.812); Barking and Dagenham the lowest (4.551). These patterns may reflect listing and guest mix, among other factors.

For host-segment sub-scores, epsilon-squared was 0.0884 for value, 0.0785 for accuracy, 0.0722 for communication, 0.0466 for check-in, 0.0369 for cleanliness, and 0.0108 for location. Statistical significance is interpreted with effect size and score gap, not by p-value alone.

### Limits

The analysis is observational and cross-sectional. It excludes listings without ratings; coverage varies by segment. The contemporaneous local price benchmark includes each listing in its group. Host and neighbourhood patterns may be confounded by price, room type, guest mix, condition, and review propensity.

---

## 7. Visualization and dashboard creation

The EDA notebook contains completed exploratory charts. The host-segment chart is saved as reports/value_rating_by_host_segment.png.

A Power BI dashboard **has not been built as a .pbix file**. A detailed guide is available at reports/powerbi_dashboard_guide.md, including preparation, DAX measures, page design, interactions, and privacy practices.

Planned pages:

1. **Executive overview:** listing count, rated count, rating coverage, overall rating, host and room-type comparisons, local price position.
2. **Guest experience:** overall/value ratings, rating gaps, neighbourhood values, and the six sub-scores.
3. **Price and availability context:** price relative to local median alongside ratings and the calendar unavailability proxy.

Show sample counts and coverage, suppress or combine small groups, and use aggregated data. All price and rating relationships are descriptive.

---

## 8. Business insights and recommendations

Evidence and recommendations are in reports/business_insights_recommendations.md.

1. **Audit listing accuracy and value messaging.** Check that amenities, capacity, photos, house rules, fees, and descriptions match the actual experience and expectations.
2. **Offer a voluntary process checklist to multi-listing operators.** Review listing consistency, cleaning readiness, arrival instructions, and issue escalation. Compare like-for-like areas and room types; do not assume portfolio size caused the rating gap.
3. **Pilot and measure before scaling.** Set a baseline and follow-up period, compare participating listings with a suitable comparison group, and track value/accuracy ratings, checklist completion, and complaint themes if available.
4. **Use the classifier only to prioritize aggregate review.** Do not set an individual listing's price, suppress its visibility, or penalize a host based on the model.

The model’s exact-score predictions are weak. The classifier offers a more useful relative ranking for deciding what to investigate, but it still misses most lower-quartile listings.

---

## 9. Ethics, bias, fairness, and data privacy

Full discussion is in reports/ethics_bias_fairness_privacy.md.

### Privacy and data minimization

Local data can include IDs, exact coordinates, hotel address/name, reviewer nationality, and raw review text. Public availability does not remove contextual privacy risks.

- Keep row-level files local and access restricted.
- Remove IDs, exact coordinates, addresses, reviewer fields, and free text from shared dashboard/export tables.
- Share aggregate summaries; suppress or combine small cells (for example, fewer than 20–30 records).
- Follow source policies and attribution requirements.
- Do not publish row-level predictions or screenshots that reveal a listing or person.

### Bias and fairness

Ratings are subjective and self-selected. About 21.6% of Airbnb listings have no overall score, and unrated listings are excluded from score analyses and supervised modeling. Results may not generalize to new or unrated listings. Missing scores are not low scores.

Host portfolio size and neighbourhood may correlate with room type, price, property condition, guest mix, and other unobserved factors. Protected characteristics are not adequately available, so this project cannot establish fairness across protected groups. Do not infer protected attributes from names, nationality, or location.

The model uses host-grouped splits, training-only preprocessing, excludes IDs and exact coordinates, and audits subgroup errors. These safeguards reduce leakage and memorization but do not prove fairness. Neighbourhood can proxy for socioeconomic differences. Keep the model advisory, explain uncertainty, and require meaningful human review for any real operational follow-up.

---

## 10. Machine-learning model: purpose and workflow

Detailed methods and results are in reports/value_rating_model.md. Two experiments were completed; the classifier is the main business-aligned result.

### 10.1 Regression: estimate the value score

**Target:** guest-perceived value rating, 0–5.  
**Purpose:** test whether listing and host attributes can estimate an exact value score for listings with an observed rating.

Mean and median baselines, Ridge regression, default Random Forest, and tuned Random Forest were compared. The tuned forest used depth 24 and minimum leaf size 5, chosen using grouped cross-validation within training data. Imputation, categorical encoding, and Ridge scaling were fitted in training pipelines. The test split kept hosts entirely on one side.

| Model | MAE ↓ | RMSE ↓ | R² ↑ |
|---|---:|---:|---:|
| Median baseline | 0.2954 | 0.5242 | -0.0724 |
| Mean baseline | 0.3123 | 0.5063 | -0.0002 |
| Default Random Forest | 0.2962 | 0.4880 | 0.0705 |
| Tuned Random Forest | **0.2946** | **0.4861** | **0.0778** |
| Ridge regression | 0.3009 | 0.4962 | 0.0390 |

The tuned forest improves only slightly over the median baseline on MAE. R² 0.0778 means only a small share of score variation is explained. Exact value-score prediction is weak and is not a dependable individual score.

### 10.2 Classification: prioritize lower-quartile value ratings

**Business question:** can we prioritize unseen-host listings more likely to fall in the low end of value scores, for voluntary follow-up?

**Label:** value score at or below the 25th percentile learned from the relevant training partition. The earlier holdout threshold was 4.50. Ties mean the holdout prevalence was 28.1%, not exactly 25%. Repeated folds learn their own training threshold.

**Inputs:** property and room type, neighbourhood, price, stated capacity, bedrooms/beds/bathrooms, minimum/maximum nights, host listing count, amenity count and selected amenity flags, description length, bathroom privacy, and local price position calculated using training data only. Small neighborhood-room groups use the training global median.

**Exclusions:** IDs and exact coordinates; target and other review scores; review-derived features and text; calendar activity; full-sample price benchmarks; and unavailable fields. Host IDs are used only to group splits, never as predictors.

**Evaluation design:** an 80/20 GroupShuffleSplit by host gave 38,315 training listings from 19,567 hosts and 10,004 test listings from 4,892 different hosts, with zero host overlap. A Random Forest classifier was compared with logistic regression and a prevalence baseline. Repeated evaluation used five host-grouped folds under three shuffles (15 folds). Every fold learned its threshold and local price benchmark from training rows only.

Metrics: PR-AUC/average precision measures ranking of low-value listings; ROC-AUC measures ranking separation; top-decile precision and recall assess a review queue; lift compares its low-value rate with prevalence; Brier score measures probability error.

**Single holdout results:**

| Model | PR-AUC | ROC-AUC | Precision top 10% | Recall top 10% | Lift | Brier |
|---|---:|---:|---:|---:|---:|---:|
| Prevalence baseline | 0.2813 | 0.5000 | 0.2813 | 0.1000 | 1.00× | 0.2022 |
| Logistic regression | 0.4383 | 0.6870 | 0.5055 | 0.1798 | 1.80× | 0.2294 |
| Random Forest classifier | **0.4489** | **0.7016** | 0.4925 | 0.1752 | **1.75×** | **0.1936** |

**Repeated host-grouped validation, mean ± standard deviation across 15 folds:**

| Metric | Mean ± SD |
|---|---:|
| Low-value prevalence | 0.2744 ± 0.0069 |
| PR-AUC / average precision | **0.4633 ± 0.0218** |
| ROC-AUC | **0.7106 ± 0.0084** |
| Precision in top 10% risk | **0.5400 ± 0.0351** |
| Recall in top 10% risk | 0.1969 ± 0.0121 |
| Lift in top 10% risk | **1.9681× ± 0.1211** |
| Brier score | 0.1866 ± 0.0030 |

In repeated host-held-out folds, about 54% of listings in the top 10% predicted risk met the fold-specific low-value definition, around 1.97 times the roughly 27% validation prevalence. That top 10% captures only about 19.7% of all low-value listings, so most are missed. This supports coarse aggregate prioritization, not individual verdicts.

### Strengths and limitations

Host grouping reduces leakage from a host’s multiple listings; training-only preprocessing and local benchmarks reduce leakage; simple baselines and repeated validation are reported. However, labels are subjective and selective, scores are clustered near 5 with many ties, the model has moderate ranking performance, and repeated folds reuse one snapshot. There is no future-time validation. These metrics do not prove fairness, causality, or future business impact.

---

## 11. Reproducibility and project files

### Main notebooks and reports

- Cleaning/alignment: scripts/clean_and_align_full_script.ipynb
- EDA notebook: scripts/eda_visualization.ipynb
- Feature engineering: scripts/feature_engineering.ipynb
- Statistical analysis: scripts/statistical_analysis.ipynb
- Business analysis: scripts/business_insights.ipynb
- Value regression: scripts/value_rating_model.ipynb
- Low-value classification and repeated grouped validation: scripts/value_rating_low_value_classifier.ipynb
- Feature rationale: reports/feature_engineering.md
- Statistical results: reports/statistical_analysis.md
- Business recommendations: reports/business_insights_recommendations.md
- Ethics/privacy: reports/ethics_bias_fairness_privacy.md
- Power BI instructions: reports/powerbi_dashboard_guide.md
- Model methods/results: reports/value_rating_model.md
- Cleaning log: reports/cleaning.txt

### Reproduction sequence

1. Place source datasets in local raw-data locations described in README.md.
2. Open scripts/clean_and_align_full_script.ipynb in Jupyter and run all cells.
3. Open scripts/feature_engineering.ipynb in Jupyter and run all cells.
4. Open scripts/statistical_analysis.ipynb and scripts/business_insights.ipynb in Jupyter and run all cells.
5. Open scripts/value_rating_model.ipynb for regression and scripts/value_rating_low_value_classifier.ipynb for classification and repeated validation; run all cells.
6. Use reports/powerbi_dashboard_guide.md to build the Power BI report from processed features.

Processed data and model artifacts are local generated files and git-ignored. Raw data is not bundled; refreshed data can change row counts and results.

---

## Final conclusion

The project turns rating exploration into an actionable but cautious question: where should hosts investigate guest expectations and perceived value? EDA and statistical analysis show differences in value and accuracy ratings across observed host portfolio segments. Exact value-score prediction remains weak; the lower-quartile classifier offers a repeatable but imperfect way to prioritize aggregate follow-up. The evidence supports a voluntary listing-accuracy/value-messaging pilot measured on later outcomes, not automatic individual decisions.

The central lesson is to connect each analytical step to an operational use while keeping claims proportional to evidence: describe associations as associations, show missingness and sample sizes, validate future performance, and protect guest and host privacy.

