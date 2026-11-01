# Airbnb feature engineering: methods and rationale

## Purpose

This step turns the cleaned, one-row-per-listing Airbnb master table into a separate analysis table with features that support practical host and marketplace questions. It does not change the source master file and does not add generated records. The companion notebook is `scripts/feature_engineering.ipynb`; its output is `data/processed/airbnb_features.csv`.

The features are designed to help answer:

1. Is a listing priced above or below comparable listings nearby?
2. How does host operating scale relate to listing outcomes?
3. How does the advertised nightly price compare after accounting for stated guest capacity?
4. What does the calendar say about unavailable dates, with the proxy limitation made explicit?
5. How recently and frequently has a listing received reviews?

These are descriptive and predictive features. They do not establish that changing a feature will cause a business outcome to change.

## Reproduce the feature table

Open the notebook in Jupyter and run its cells in order:

```bash
scripts/feature_engineering.ipynb
```

The notebook reads `data/processed/airbnb_master.csv`, writes `data/processed/airbnb_features.csv`, and leaves the input unchanged. It requires pandas and numpy, which are already used by the cleaning pipeline. The table currently contains 61,617 listing rows. Processed data is git-ignored, so the CSV is a local generated artifact; the script and this explanation are the reproducible project deliverables.

## Features created

### Raw listing enrichment for value-rating modeling

The feature-engineering script now selectively joins the available raw Inside Airbnb `listings.csv` by listing ID before computing the existing features. It retains only derived aggregates below; raw amenity arrays, free-text descriptions, photo URLs, and IDs are not copied into additional model inputs.

| Feature | Calculation | Why it is useful | Limits and interpretation |
|---|---|---|---|
| `amenity_count` | Number of amenities in the raw JSON-like amenity list. | A coarse measure of the breadth of advertised facilities that could shape value expectations. | Amenities may differ greatly in quality; count alone is not service quality. |
| `amenity_wifi`, `amenity_kitchen`, `amenity_washer`, `amenity_air_conditioning`, `amenity_workspace`, `amenity_parking`, `amenity_pool`, `amenity_self_check_in` | Binary indicator that an amenity label contains the corresponding term. | Tests a small set of recognizable facilities without retaining the full amenity text. | Labels may vary across snapshots; absence can mean not listed rather than unavailable. |
| `description_length_chars`, `description_word_count` | Character/word counts after removing HTML tags from the description. | Tests whether the amount of listing detail is associated with guest-perceived value, without using raw description text. | Length is not a measure of accuracy, readability, or truthfulness. |
| `bathroom_privacy` | `shared`, `private`, or `unspecified` parsed from `bathrooms_text`. | Shared/private bathroom access can materially affect guest expectations and value. | Some descriptions do not state bathroom privacy; “unspecified” should not be assumed private. |

The raw listing export was checked: it contains 92,638 rows and has a `last_scraped` date of 2026-06-25. Amenity and description information are populated; `neighborhood_overview`, `host_since`, `license`, host response/acceptance fields, and `instant_bookable` are 100% missing in this particular source file. The export contains `picture_url` (one primary URL), not a listing photo count. The pipeline therefore drops those unusable columns and does not infer photo count or tenure. Exact coordinates exist in the source but are not added as model features. A tube-station dataset was not available to derive defensible nearest-station distances.

| Feature | Calculation | Why it is useful | Limits and interpretation |
|---|---|---|---|
| `local_room_type_price_median_gbp` | Median listing price within `neighbourhood_cleansed` × `room_type`. The listing's own price is included in the group median. | Gives a local reference price for host benchmarking and lets analysis compare similar room types in the same neighbourhood. | It is a market snapshot, not a recommended or optimal price. Extreme values were already trimmed during cleaning. |
| `local_room_type_listing_count` | Number of non-missing prices in the same neighbourhood × room-type group. | Shows the amount of evidence behind each benchmark. | Listings are not independent market transactions; a large count does not prove a representative sample. |
| `price_vs_local_median_pct` | `(listing price / local median − 1) × 100`. | Expresses the price gap as a comparable percentage rather than a pound difference, making neighbourhoods with different price levels easier to compare. | The benchmark is contemporaneous and includes the listing itself. It describes relative position, not customer value or causal price effects. |
| `price_position_vs_local_market` | Below median: less than −10%; near median: −10% to under +10%; above median: +10% or higher. | Creates readable segments for dashboard filters and host comparisons. | The 10% bands are a clear analysis convention, not an industry standard. Rows with fewer than 20 listings in their group are labelled `insufficient_local_sample`. |
| `host_listing_count` | Count of listings with the same `host_id` in the cleaned Airbnb master table. | Supports the business question about individual hosts versus larger operators and allows comparisons by operating scale. | It counts listings in this dataset snapshot, not all properties a host may manage elsewhere. The host ID itself should not be published. |
| `host_portfolio_segment` | 1 listing; 2–5; 6–20; or 21+ listings. | Buckets make host-scale comparisons easier to interpret and chart than dozens of exact counts. | These thresholds are chosen for presentation and should be shown in the report; they are not regulatory definitions of a professional host. |
| `listed_price_per_guest_gbp` | Nightly listing price divided by `accommodates`, when stated capacity is greater than zero. | Gives guests and hosts a simple capacity-adjusted price benchmark. | This assumes the full stated capacity is used and ignores fixed fees, occupancy, and differences in room layout. It is not a per-person quote. |
| `calendar_unavailability_rate_proxy` | The cleaned calendar's `pct_days_booked`, clipped to the 0–1 range. In the cleaning script it is calculated as `1 − mean(is_available)`. | Makes the calendar signal available for descriptive comparisons of listings with more or fewer unavailable dates. | Unavailable dates may be booked, blocked by hosts, or otherwise unavailable. Call this an **unavailability proxy**, not confirmed occupancy, bookings, or demand. Do not use as a model feature to predict itself or as proof of demand. |
| `calendar_unavailability_band_proxy` | Lower: under 25%; mid: 25% to under 50%; higher: 50% or more. | Supports a simple comparison of listing and price profiles across proxy bands. | The cutoffs are convenient descriptive bins; they do not represent proven demand tiers. |
| `days_since_latest_observed_review` | Latest valid `last_review` date in this dataset snapshot minus the listing's `last_review` date. | Identifies listings whose review activity is older relative to other listings in this same snapshot, useful for host follow-up analysis. | It is not days since the data download or today. The reference is the latest review date present in the data; unrated listings remain missing. |
| `review_activity_band` | `reviews_per_month`: low under 0.25; moderate 0.25 to under 1; high 1 or more. | Creates interpretable review-activity groups for dashboard summaries. | Review volume is only an imperfect proxy for booking activity because not every guest leaves a review and listing exposure differs. The bins are project conventions. |

The run created the table for all **61,617** listings. All had calendar proxy values in the current snapshot. **48,322** had a valid last-review date; the remaining rows have missing recency because no last-review date was recorded. **207** listings fall into local benchmark groups smaller than the minimum of 20 and receive the insufficient-sample label instead of a price position.

## Feature choices for later work

### Statistical analysis and dashboard

Use the local price features to compare price position across neighbourhoods and room types, and host portfolio features to compare operating scale. Use capacity-adjusted price as a complementary view, not a replacement for nightly price. For calendar analysis, keep the proxy wording visible in chart titles and captions. Show counts with group summaries, especially when comparing small neighbourhood or host groups.

Do not interpret a higher review rate or a higher unavailability proxy as proof of greater demand. These fields can guide follow-up questions, but the source data cannot distinguish confirmed bookings from host-blocked dates.

### Recommended ML target and leakage controls

The planned model can predict `review_scores_rating` (0–5) for listings that have a rating, using listing and host characteristics to identify profiles associated with higher or lower satisfaction. This is a prediction/triage aid for understanding patterns, not a causal quality score. About 21.6% of listings have no ratings, so training data represents reviewed listings and may not generalize to new or unrated listings.

For that model, candidate inputs include room type, property type, neighbourhood, price, accommodates, bedrooms, beds, bathrooms, minimum/maximum nights, host superhost status, response time/rate, acceptance rate, and instant-bookable status where available. Treat neighbourhood and host response fields as possible sources of group disparities and inspect model errors across relevant groups.

Exclude the target and any information derived from reviews or later outcomes from model inputs: `review_scores_rating`, all `review_scores_*` sub-scores, `number_of_reviews`, `number_of_reviews_ltm`, `reviews_per_month`, `first_review`, `last_review`, `review_text_count`, `avg_sentiment_score`, `avg_comment_length`, `most_recent_review_date`, `days_since_latest_observed_review`, `review_activity_band`, `estimated_occupancy_l365d`, and `estimated_revenue_l365d`. Also exclude `calendar_unavailability_rate_proxy` and `calendar_unavailability_band_proxy` from this satisfaction model: they reflect the same listing snapshot period and could encode later booking activity. Exclude identifiers (`id`, `listing_id`, `host_id`) and raw coordinates; they can encourage memorization or expose sensitive location/identity information. Keep engineered price-relative-to-market features out of the first model too, since they are calculated using the full sample and would need training-fold-only benchmark calculation to avoid information leakage in a rigorous evaluation.

Fit preprocessing and any imputation using training data only. Use a held-out split, compare against a simple baseline, and report error metrics and errors by neighbourhood/room type. A strong score does not show that the model is fair or that a host action will improve ratings.

## Data privacy and fairness notes

- The feature output retains source columns for convenient analysis, including IDs and coordinates. Keep it local and restrict dashboard views to aggregated groups; do not expose host IDs, exact listing coordinates, or reviewer-level information.
- Neighbourhood pricing features can reflect housing supply, regulation, tourism patterns, and unequal access to resources. Do not present a neighbourhood as inherently better or worse based on these values.
- Multi-listing host segments describe observed listing counts in this dataset only. Avoid turning them into labels of legality or host intent.
- Ratings are supplied by a self-selected subset of guests. They can reflect expectations, cultural differences, and response rates as well as the stay itself. Missing ratings should not be treated as low ratings.

## Known limitations

1. The source is a cross-sectional listing snapshot; it does not provide a randomized or causal design.
2. Calendar availability does not separate booked dates from host-blocked dates.
3. The relative price benchmark includes each listing in its own group and can move with dataset composition.
4. Review activity and review recency describe recorded reviews, not complete booking history.
5. The Booking.com data remains separate from this Airbnb feature table because it is review-level, from a different period, and lacks equivalent price/capacity fields.
