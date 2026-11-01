# Power BI Dashboard Creation Guide

## 1. Purpose and business question

Build a dashboard that helps a London short-stay operator answer:

> Which listing and host segments have weaker guest satisfaction or perceived value, and where should the operator investigate pricing, communication, or service practices?

The dashboard is descriptive. Segment differences and price-rating relationships are associations; they do not prove that a listing characteristic caused a rating.

## 2. Prepare and load the data

1. In Power BI Desktop, choose **Get data > Text/CSV** and load `data/processed/airbnb_features.csv` from this project.
2. Confirm the table is at listing grain: each row should describe one listing, without duplicate listing records.
3. In Power Query, remove direct identifiers (listing ID, host ID/name, reviewer fields, exact address, latitude, longitude, and free-text fields) before loading the report model. Keep the neighbourhood grouping field for aggregate comparisons.
4. Set numeric types for price, capacity, rating scores, local room-type median price, price-position percentage, review counts, and calendar proxy. Set categories such as neighbourhood, room type, property type, and host segment to text. Keep missing rating scores null; do not replace them with zero.
5. Check the number of rows, missing ratings, duplicate rows, and any implausible prices or scores. Record the final row count and refresh date in a report note.

## 3. Add core measures

Create these from **Modeling > New measure**. Adjust field names only if they differ in the loaded table. If `has_rating` is stored as 0/1 instead of TRUE/FALSE, use `= 1` in its filter.

```DAX
Listings =
COUNTROWS ( 'airbnb_features' )

Rated Listings =
CALCULATE (
    [Listings],
    'airbnb_features'[has_rating] = TRUE ()
)

Rating Coverage =
DIVIDE ( [Rated Listings], [Listings] )

Average Overall Rating =
AVERAGE ( 'airbnb_features'[review_scores_rating] )

Average Value Rating =
AVERAGE ( 'airbnb_features'[review_scores_value] )

Overall vs Value Gap =
[Average Overall Rating] - [Average Value Rating]

Median Nightly Price GBP =
MEDIAN ( 'airbnb_features'[price] )

Average Price Position vs Local Median =
AVERAGE ( 'airbnb_features'[price_vs_local_median_pct] )

Average Calendar Unavailability Proxy =
AVERAGE ( 'airbnb_features'[calendar_unavailability_rate_proxy] )
```

Format `Rating Coverage` as a percentage, prices as GBP, and rating measures using the source score scale. Calendar proxy measures must retain “proxy” in their names and labels.

## 4. Create report pages

### Page 1 — Executive overview

Purpose: give an operator a quick view of the size and quality of the listing sample and reveal which broad segments merit a closer look.

- Add four card visuals: **Listings**, **Rated Listings**, **Rating Coverage**, and **Average Overall Rating**.
- Add a clustered bar chart: average overall rating by `host_portfolio_segment`. Include listing count in tooltips so a small group is not mistaken for a stable result.
- Add a column chart: average overall rating by `room_type`.
- Add a bar chart: average `price_vs_local_median_pct` by room type. Explain that positive values mean above the local room-type median, not better quality.
- Add slicers for `neighbourhood_cleansed`, `room_type`, and `property_type`.
- Add a text note with the data snapshot date and a warning that comparisons are descriptive.

### Page 2 — Guest experience

Purpose: show whether overall satisfaction and perceived value diverge, helping prioritize practical service investigations.

- Add a matrix with `host_portfolio_segment` as rows and `room_type` as columns. Values: average overall rating, average value rating, the overall-vs-value gap, and listing count.
- Add a bar chart of average value rating by neighbourhood. Sort ascending. Apply a minimum listing-count filter (for example, 30) and show the count in tooltips.
- Add a clustered column chart for the available rating sub-scores (accuracy, cleanliness, check-in, communication, location, and value) by host segment. Use averages, with listing counts in tooltips.
- Add a note that ratings exist only for listings with reviews, and that reviewer mix and review volume can differ among groups.

### Page 3 — Price and availability context

Purpose: explore whether above-market pricing and observed calendar unavailability co-occur with satisfaction patterns; identify areas for follow-up, not automatic pricing decisions.

- Add a scatter chart with `price_vs_local_median_pct` on X, `review_scores_rating` on Y, and `room_type` as legend. Filter out listings without a rating. Use neighbourhood for tooltip context. Avoid interpreting the chart as causal evidence.
- Add a bar chart of average `calendar_unavailability_rate_proxy` by room type or host segment.
- Optionally add `calendar_unavailability_band_proxy` as a slicer.
- Label this metric as a calendar-derived unavailability proxy. It may include bookings, owner blocks, and other reasons; do not call it occupancy or booked nights.

## 5. Layout, interaction, and quality checks

- Use a clear title on each page and consistent rating/price formats.
- Keep the most important cards and comparisons near the top; avoid crowded visuals and unnecessary 3D or pie charts.
- Ensure slicers filter the intended visuals; test **Edit interactions** where needed.
- Show counts or rating coverage near averages. Suppress or flag thin groups rather than ranking them confidently.
- Check that totals, averages, and filters respond plausibly. Compare a few displayed values with the source data or prior EDA.
- Add report tooltips or footnotes defining the local price-position measure and availability proxy.
- Save the `.pbix` in the project folder and note the data snapshot date. For refreshes, rerun the upstream cleaning and feature-engineering steps, then refresh the Power BI source.

## 6. How to turn comparisons into useful action

Use the dashboard to identify a segment or neighbourhood with a consistent lower value rating or an overall/value gap. Then investigate plausible operational explanations such as cleaning fees, amenity information, check-in instructions, or expectation-setting. Treat these as hypotheses to validate with operational context or additional data. Recommend a targeted review or pilot and monitor the relevant ratings after the change; do not claim the chart alone proves the cause.

## 7. Ethics, fairness, and privacy

- Do not publish host/listing identities, exact locations, reviewer details, or review text. Share aggregate views and keep report access limited to people who need it.
- Neighbourhood can act as a proxy for socioeconomic differences. Use it for market context and fair service planning, not to deny service, penalize an individual host, or make individual eligibility decisions.
- Reviews are selective and subjective. Averages may vary with review count, reviewer composition, time, and whether a listing received any review. Display coverage and counts, and do not treat missing ratings as poor performance.
- Avoid automated host ranking or enforcement from this dashboard. Check sample size, recency, measurement limitations, and potential group impacts before acting.
- Follow the source dataset's licence and attribution requirements when sharing the report.
