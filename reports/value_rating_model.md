# Airbnb Guest-Perceived Value Rating Model

## Purpose and business question

This project tests whether listing characteristics can estimate a listing’s guest-perceived value score (`review_scores_value`, 0–5). The practical purpose is to learn whether pre-review listing information can flag broad profiles for a closer, voluntary review of price/value messaging, listing descriptions, and amenities.

The model is an exploratory diagnostic. It does not measure objective quality, show that a characteristic causes a rating, recommend an individual listing’s price, or justify ranking/penalizing hosts. The EDA found a descriptive mean value-score gap across host segments (4.713 for single-listing hosts and 4.416 for the 21+ observed-listing segment); this motivated the target, but the segment itself is not used as a model input.

## Reproduction

From the project root, run:

```bash
python scripts/value_rating_model.py
```

The script reads `data/processed/airbnb_features.csv`. It writes the trained Random Forest artifact, metrics, subgroup errors, permutation importance, and split summary under the git-ignored `data/processed/modeling/` folder. It uses pandas, numpy, scikit-learn, and joblib.

## Steps performed and reasons

### 1. Select the target and analytical population

- **Target:** `review_scores_value`, the guest’s 0–5 value-for-money score. This is more directly tied to the project’s existing value-rating insight than overall rating.
- **Rows:** listings with a valid target in the allowed 0–5 range. Missing target scores are unknown outcomes and are excluded; they are not set to zero.
- **Current data:** 61,617 listing rows; 48,319 have a usable value score and 13,298 do not. The target-specific count differs slightly from the overall-rating coverage because some listings have one score field missing while another is present.

### 2. Choose input features

The first model uses a narrow set of listing characteristics plausibly available without looking at guest review outcomes:

| Input | Reason for inclusion |
|---|---|
| `neighbourhood_cleansed` | Captures broad location-market context without exact coordinates. It may proxy for socioeconomic differences, so subgroup performance is checked and it must not be used to stigmatize areas. |
| `property_type`, `room_type` | Represents accommodation format and lets the model account for broad differences in what guests book. |
| `accommodates` | Captures stated capacity, which may shape both expectations and the perceived value of a stay. |
| `bathrooms`, `bedrooms`, `beds` | Describes accommodation size/amenities relevant to guest expectations. Missing values are imputed using training data only. |
| `price` | Tests whether listed nightly price contains a signal about perceived value. It cannot support a causal claim or optimal-price recommendation. |
| `listed_price_per_guest_gbp` | Adds a capacity-adjusted price view already engineered per listing. It tests whether the advertised price relative to stated guest capacity contains additional signal; it is not an actual per-person quote. |
| `host_listing_count` | Captures observed host portfolio scale, which prior analysis associated with value-rating differences. It is not an identity: host IDs are used only for splitting. The count is limited to this dataset snapshot and should not be treated as a complete inventory. |
| `amenity_count` and selected amenity flags | Derived from raw amenity labels; tests whether the breadth or presence of facilities relates to guest value scores without passing raw amenity text to the model. Absence may mean “not listed,” not “not provided.” |
| `description_length_chars`, `description_word_count` | Summarize description detail without retaining or vectorizing raw free text. Length is not a measure of accuracy. |
| `bathroom_privacy` | Parsed shared/private/unspecified status from `bathrooms_text`, since bathroom sharing affects guest expectations. |
| `minimum_nights`, `maximum_nights` | Represents booking constraints that can affect which guests choose a listing and the context in which value is judged. |

Four candidate source fields—`host_response_rate`, `host_acceptance_rate`, `host_response_time`, and `instant_bookable`—are 100% missing in this snapshot and were excluded rather than imputed into fabricated information. `bathrooms` is 10.4% missing, `bedrooms` 22.0%, and `beds` 6.7%; numeric missingness is median-imputed within each training fit. Categorical missingness is filled with the training-set most-frequent category. Unseen categories in the holdout are ignored by the encoder.

### 3. Exclude leakage and sensitive identifiers

- Excluded `id`, `listing_id`, `host_id`, latitude, and longitude. `host_id` is used only to keep each host’s listings together during splitting; it is never a model feature.
- Excluded overall rating and all other review sub-scores. They are outcomes or direct rating signals, not legitimate predictors of the value score.
- Excluded review counts, review timing/activity, sentiment/text aggregates, and review-derived features. They can reveal the outcome period or encode later guest response.
- Excluded availability, calendar unavailability, occupancy, and revenue fields because they describe the same or later snapshot period and are imperfect proxies.
- Excluded full-sample local price benchmarks and price-position features because they were calculated across the full dataset. A future version could calculate such features within each training fold only.
- Excluded `host_portfolio_segment` as a model input; it is retained only to audit group errors. Added the numeric `host_listing_count` as a potentially useful pre-review profile feature; its snapshot and coverage limitations are noted above.
- Excluded `host_is_superhost` because eligibility may depend on review outcomes, creating a potential target-derived signal.

### 4. Split by host to test generalization

The valid rows are split once using `GroupShuffleSplit`: 80% of rows for training and 20% for holdout, grouped by host ID with fixed random seed 42. The training set has 38,315 listings from 19,567 hosts; the holdout has 10,004 listings from 4,892 different hosts. Host overlap is zero. This avoids an overly optimistic score caused by the same host’s listings appearing in both sets.

This is a single snapshot, not a time-based validation. It tests performance for different hosts in this dataset period, not future seasons or future market conditions.

### 5. Preprocess inside model pipelines

All imputation, encoding, and scaling (for Ridge) are fit on training rows only through scikit-learn pipelines. Nominal categories use one-hot encoding with rare categories grouped (minimum frequency 10). The Random Forest does not require numeric standardization; Ridge does. These steps prevent test data from influencing fitted preprocessing and allow the model to handle categories not seen during training.

### 6. Train and compare models

- **Mean baseline:** predicts the training target mean for every holdout listing. This sets a minimum usefulness bar.
- **Ridge regression:** regularized linear reference model; it tests whether simpler, more transparent relationships perform as well as the tree model.
- **Random Forest regression:** the main nonlinear candidate. It can model interactions without requiring straight-line relationships. A small search tries `max_depth` 24 or unlimited and `min_samples_leaf` 1 or 5, with 150 trees and 70% of features considered per split.

No model settings were tuned against the final holdout. The Random Forest settings were selected with 3-fold `GroupKFold` cross-validation using only the training hosts and MAE as the selection metric. A separate host-group holdout is used once for final comparison. This permits a modestly more flexible model while controlling the main overfitting risk.

### 7. Evaluate performance

Metrics are computed on the host-held-out sample:

- **MAE:** average absolute error in rating points; lower is better.
- **RMSE:** gives larger misses more weight; lower is better.
- **R²:** fraction of variation explained relative to predicting the test mean; higher is better, and near zero means little explanatory predictive power.

### 8. Audit subgroup errors and feature reliance

Random Forest holdout errors are summarized by room type, host portfolio segment, and neighbourhood. Groups with fewer than 30 holdout rows are omitted from the subgroup file. Mean error is prediction minus actual; positive values mean overprediction. These are performance checks, not tests of legal fairness or proof of discrimination.

Permutation importance is calculated on a fixed, at-most-1,000-row holdout sample with three repeats. It reports how much the Random Forest’s MAE worsens when one raw input column is shuffled. Importance is predictive reliance, not causal effect; correlated inputs can share or mask importance.

## Results

### Holdout metrics

| Model | Train rows | Holdout rows | MAE | RMSE | R² |
|---|---:|---:|---:|---:|---:|
| Median baseline | 38,315 | 10,004 | **0.2954** | 0.5242 | -0.0724 |
| Mean baseline | 38,315 | 10,004 | 0.3123 | 0.5063 | -0.0002 |
| Default Random Forest | 38,315 | 10,004 | 0.2962 | 0.4880 | 0.0705 |
| Tuned Random Forest | 38,315 | 10,004 | **0.2946** | **0.4861** | **0.0778** |
| Ridge regression | 38,315 | 10,004 | 0.3009 | 0.4962 | 0.0390 |

After adding host count, price-per-guest, amenity indicators/count, description length, and bathroom privacy, the tuned Random Forest improves to holdout MAE 0.2946, RMSE 0.4861, and R² 0.0778. It narrowly beats the median baseline’s MAE of 0.2954 and performs better on RMSE/R². The MAE improvement over the median baseline is only about 0.0008 points, while R² indicates the model explains about 7.8% of rating variation. This is a useful improvement for the coursework experiment, but remains limited for individual decisions.

### Random Forest errors by host segment

| Host portfolio segment | Holdout rows | MAE | Mean error (predicted − actual) |
|---|---:|---:|---:|
| 1 listing | 3,482 | 0.227 | -0.015 |
| 2–5 listings | 2,535 | 0.270 | -0.016 |
| 6–20 listings | 2,084 | 0.349 | +0.012 |
| 21+ listings | 1,903 | 0.391 | +0.001 |

The model’s errors differ by host segment: it tends to underpredict for single-listing hosts and overpredict for the 21+ segment. This makes individual predictions especially inappropriate as a basis for decisions and is a reason to treat host-size patterns cautiously. It is an error pattern in this sample, not proof of unfair treatment or its cause.

### Random Forest permutation importance

The tuned model parameters were maximum depth 24 and minimum leaf size 5, selected from the training-only grouped search (cross-validation MAE 0.2972). The largest mean MAE increases when a feature is shuffled were host listing count (+0.0340), amenity count (+0.0126), accommodates (+0.0064), price (+0.0062), and beds (+0.0052). These are predictive reliance measures, not evidence that changing those attributes will improve ratings.

## Business-focused classification experiment

Because the business question is about which profiles merit a closer review, a separate classification experiment flags value ratings at or below the **training-set 25th percentile**. In this split the learned threshold is 4.50. Ties at 4.50 make the test low-value prevalence 28.1%, rather than exactly 25%. This is a relative triage definition for this dataset, not a universal standard for an acceptable stay.

The same host-held-out split is used (zero host overlap). The local price-position feature is calculated using neighbourhood × room-type medians from the training partition only; groups with fewer than 20 training rows fall back to the training global median. The classification model is evaluated on the held-out hosts, not tuned against that test set.

| Classifier | PR-AUC / average precision ↑ | ROC-AUC ↑ | Precision in top 10% risk | Recall in top 10% | Lift in top 10% | Brier ↓ |
|---|---:|---:|---:|---:|---:|---:|
| Prevalence baseline (no ranking) | 0.2813 | 0.5000 | 0.2813 | 0.1000 | 1.00 | 0.2022 |
| Logistic regression | 0.4383 | 0.6870 | 0.5055 | 0.1798 | 1.80 | 0.2294 |
| Random Forest classifier | **0.4489** | **0.7016** | 0.4925 | 0.1752 | **1.75** | **0.1936** |

This is a more decision-aligned result than exact-score regression: selecting the 10% highest-risk listings identifies a group with a 49.3% low-value rate, versus 28.1% overall (1.75× lift). It captures about 17.5% of all low-value test listings, so most low-value cases are still missed. Logistic regression has slightly higher precision/recall in that top 10%, while the Random Forest has better PR-AUC, ROC-AUC, and Brier score.

### Repeated host-grouped validation

To check stability, the fixed Random Forest classifier was evaluated with 5-fold `GroupKFold` repeated using three different group shuffles (15 folds total). Each fold recalculates its target’s lower-quartile threshold and local price benchmarks from that fold’s training data only. Reported values are mean ± standard deviation across folds:

| Metric | Mean | SD |
|---|---:|---:|
| PR-AUC / average precision | 0.4633 | 0.0218 |
| ROC-AUC | 0.7106 | 0.0084 |
| Precision in top 10% risk | 0.5400 | 0.0351 |
| Recall in top 10% risk | 0.1969 | 0.0121 |
| Lift in top 10% risk | 1.9681× | 0.1211 |
| Brier score | 0.1866 | 0.0030 |

The prevalence baseline for PR-AUC is approximately 0.2744, so mean PR-AUC 0.4633 and mean top-decile lift near 1.97 indicate repeatable ranking signal across host-held-out folds. The spread is moderate, not negligible. These folds reuse the project snapshot and do not replace a future-time test on a new data refresh. The classifier is moderately useful for prioritizing an aggregate or voluntary review queue; it is not accurate enough to label or penalize individual hosts/listings.

## Review of proposed additional fields

The cleaning pipeline’s `keep_cols` selection discarded amenities, description text, and bathroom-text details. The raw listing export was found and is now selectively joined during feature engineering; the model uses amenity count/selected flags, description length, and bathroom privacy while discarding raw text and URLs. The raw file confirms host tenure, licence, neighbourhood overview, response fields, instant-bookable, and a photo count are unavailable or absent in this snapshot (it has one primary `picture_url`, not a full photo count). Do not impute these columns as if observed.

The current table includes neighbourhood but not exact coordinates in the model. Centrality and transit-distance features would require a trustworthy London centre definition and a licensed/appropriate tube-station dataset; they are not added from guesses. Fold-specific local median pricing would be a reasonable next experiment, provided each fold computes its benchmarks from training rows only.

## Business interpretation and recommendation

The useful result is not a dependable per-listing prediction. The features in this snapshot add little predictive information about guest-perceived value for hosts not seen in training. Price, capacity, property type, and bedrooms contain the most signal in the Random Forest, but that signal is weak. A sensible business use is to motivate aggregate investigation of how expectations, listing descriptions, amenities, and price messaging differ across listing profiles, followed by a voluntary pilot measured with future data.

Do not recommend price changes from this model. Do not rank, penalize, or delist hosts. If a pilot is run, define the intervention and outcome in advance, collect a later time period, and compare outcomes with an appropriate control or matched group.

## Limitations and responsible use

1. Only listings with observed value ratings are modeled; rating availability is selective and may exclude new or less-reviewed listings.
2. Ratings are subjective, self-selected, and concentrated toward the high end. The target is guest-perceived value, not objective property quality.
3. The cross-sectional snapshot supports association/prediction only, not causality or future-time performance.
4. The host-group split is stronger than a random row split, but a single split can still vary with its random seed. Use grouped cross-validation and a fresh test period before drawing stronger conclusions.
5. Host response/acceptance and instant-book fields were unusable because they were fully missing; the model lacks potentially relevant operational information.
6. Neighbourhood can proxy for socioeconomic conditions. Group error checks do not establish fairness across protected characteristics, which are not adequately represented here.
7. Permutation importance is not causal, and correlated features can change each other’s apparent importance.
8. Do not export row-level predictions with identifiers. The saved model and outputs are git-ignored local course artifacts; publish only aggregate results and keep source data private.

## Output files

- `data/processed/modeling/value_rating_random_forest.joblib` — fitted Random Forest pipeline.
- `data/processed/modeling/value_rating_model_metrics.csv` — baseline/Ridge/Random Forest holdout comparison.
- `data/processed/modeling/value_rating_subgroup_errors.csv` — aggregate Random Forest holdout errors by group.
- `data/processed/modeling/value_rating_permutation_importance.csv` — Random Forest feature reliance summary.
- `data/processed/modeling/value_rating_split_summary.json` — split sizes, features, exclusions, and fixed settings.
- `scripts/value_rating_low_value_classifier.py` — business-aligned lower-quartile classification experiment with training-only local price context.
- `data/processed/modeling/low_value_classifier_metrics.csv` and `low_value_classifier_subgroups.csv` — holdout ranking and subgroup summaries.
- `data/processed/modeling/low_value_repeated_group_cv.csv` and `low_value_repeated_group_cv_summary.csv` — 15-fold repeated host-group validation results.
