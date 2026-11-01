# Ethics, Bias, Fairness, and Data Privacy

## Project context and scope

This report assesses ethical risks in *Decoding the Stay Economy*, a course project comparing Airbnb London listing characteristics and guest ratings with a Booking.com hotel-review dataset. Its purpose is to guide responsible analysis, visualization, recommendations, and a planned machine-learning model. It is not a legal compliance assessment, a finding of discrimination by either platform, or evidence that one platform is inherently fairer or provides better value.

The project analyses observational, third-party datasets. The cleaned Airbnb master/features table has 61,617 listing rows and 48,322 non-missing overall ratings (78.4% coverage); 13,295 listings (21.6%) have no overall rating. The Booking.com source was originally a multi-city review dataset and is filtered for the project; it contains reviewer nationality and written review fields. The sources differ in record grain and period: Airbnb is listing-level and current to its snapshot, while Booking.com reviews are from 2015–2017. Booking.com has no equivalent nightly price field in this dataset. These constraints shape the conclusions that can responsibly be drawn.

## 1. Privacy and responsible data handling

### Data present in the project

The project’s processed data is not automatically anonymous just because it is public or cleaned. Current local files include:

- `airbnb_features.csv`: listing and host IDs, exact latitude/longitude, host response fields, listing attributes, ratings, calendar-derived features, and review aggregates.
- `booking_london_clean.csv`: hotel name/address and coordinates, reviewer nationality, review dates, positive/negative free-text review fields, and review-derived features.
- `comparison_schema.csv`: record/provider identifiers and other row-level fields.

IDs and precise coordinates can identify a property or link records back to people. Review text may contain names, health details, travel plans, or other information reviewers did not intend to disclose in this analysis. Reviewer nationality is not a reliable measure of race or ethnicity, but can function as a proxy and should not be used to profile guests or hosts.

### Safeguards for this course project

1. **Keep row-level files private.** Do not commit them to a public repository, email them, or include them in screenshots or presentations. The project README already notes that processed data is git-ignored; preserve that protection.
2. **Minimize fields for each task.** For analysis or reporting, create a separate table that drops direct IDs, exact coordinates, hotel address/name, reviewer nationality, raw review text, and fields not needed for the stated question. Keep the original local source files only as long as needed for reproducibility and according to their source terms.
3. **Publish aggregates.** Use neighbourhood/room/host-segment summaries and counts, not listing-level extracts. Suppress or combine small cells (for example, fewer than 20–30 records) where a group could expose an individual property. This is a practical disclosure reduction measure, not a guarantee of anonymisation.
4. **Secure access and storage.** Keep working files in a restricted project folder, avoid public cloud sharing, and remove temporary exports when no longer required. Do not put credentials or personal data in notebooks, logs, or source control.
5. **Treat public availability as limited context.** A publicly visible listing or review is still about a person or property. Public access does not, by itself, settle whether every reuse is fair, compatible with the original context, or permitted by source terms. Check Inside Airbnb’s [data policies](https://beta.insideairbnb.com/data-policies/) and the relevant dataset/platform terms before redistributing files.

The ICO’s current UK GDPR principles describe lawful, fair, and transparent use, purpose limitation, data minimisation, accuracy, storage limitation, security, and accountability. Its principles guidance notes that it is under review following changes introduced by the Data (Use and Access) Act, so anyone applying this work to a real service should check current guidance and obtain appropriate privacy/legal advice. See the [ICO guide to the data protection principles](https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/data-protection-principles/a-guide-to-the-data-protection-principles/).

### Privacy risks from dashboard and model use

- A dashboard with small neighbourhood × room-type × host-segment cells can make a single listing identifiable even when names are hidden. Aggregate, suppress small groups, and avoid drill-through to row-level listings.
- Maps at exact coordinate level can reveal a home’s location. Use broad neighbourhoods rather than point maps.
- Host portfolio counts, response rates, or detailed score profiles can become an informal host ranking. Do not make the report searchable by host or use it to expose individual operators.
- A model trained on per-listing records may memorize identifying patterns, especially if IDs or coordinates are retained. Exclude IDs, exact coordinates, review text, nationality, and direct identifiers from model inputs; assess re-identification risk before sharing model outputs.
- If this ever moves from coursework to profiling people or making decisions about access, ranking, penalties, or services, conduct a formal privacy and impact review before deployment. ICO guidance says a DPIA is required for processing likely to create high risk to people’s rights; examples include systematic and extensive profiling with significant effects. See the [ICO DPIA guidance](https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/accountability-and-governance/data-protection-impact-assessments-dpias/when-do-we-need-to-do-a-dpia/).

## 2. Bias and limitations in the data

### Selection into having a rating

Only 78.4% of Airbnb listings in the current feature table have an overall rating. The statistical report also shows rating coverage varies by group: for example, 76.6% for single-listing hosts and 75.9% for hosts with 21+ listings, and 62.0% for the small hotel-room category. Ratings therefore describe listings with observed reviews, not every listing or every stay. Guests who choose to leave reviews may differ from those who do not, and platform review processes can influence which feedback is visible.

**Implication:** do not turn missing ratings into zero or label unrated listings as poor. Show rating coverage and group counts beside rating comparisons. The future model will predict ratings only for the reviewed subset unless a separate, well-defined rating-availability model is developed; its results may not generalize to unrated or new listings.

### Confounding and non-causal comparisons

The statistical report finds differences across host portfolio segments, room types, local price position, and neighbourhood. For example, average overall ratings are 4.786 for listings from hosts with one observed listing and 4.494 for the 21+ listing segment. The host-size association has the largest effect size among the tests reported, but portfolio groups can also differ in room mix, location, prices, property condition, management, and guest expectations. The analysis does not isolate the effect of host scale.

Similarly, listings priced above their local room-type median have somewhat higher observed mean ratings than listings below it. The local benchmark includes the listing itself and price position is not randomly assigned. This cannot show that raising a price improves satisfaction, nor that paying more gives a guest better value.

**Implication:** describe results as associations in this snapshot. Use the business recommendation as a testable hypothesis (for example, audit listing accuracy and value messaging), then evaluate a voluntary pilot with a comparison group and account for time and listing mix.

### Rating and text measurement bias

Scores cluster near the high end of a bounded 0–5 scale. Small numeric gaps can be statistically significant in a large sample without being important to guests. Ratings are subjective, may reflect expectations and reviewer mix, and can be influenced by self-selection. The project’s keyword sentiment score is a lightweight proxy, not a validated measure of sentiment; it may miss sarcasm, negation, context, slang, or language variation. Booking.com review text and Airbnb review aggregates were collected and processed differently.

**Implication:** keep score distributions, medians, effect sizes, uncertainty, sample sizes, and limitations visible. Do not treat a sentiment proxy or star rating as an objective measure of property quality or host conduct.

### Platform and time-period comparability

The datasets are not a controlled, like-for-like platform comparison: Airbnb rows represent listings; Booking.com rows represent reviews. The Booking.com records are from 2015–2017 while Airbnb reflects a later listing snapshot. The Booking.com dataset has no nightly price field, and property capacity has no equivalent. Scores were mapped to a shared 0–10 comparison scale, but scale conversion does not remove differences in platform definitions, review populations, periods, or aggregation.

**Implication:** do not conclude that Airbnb or Booking.com delivers better value or quality overall from these records. Restrict comparisons to fields with defensible definitions, state the period/grain mismatch, and present the comparison as exploratory context rather than a platform league table.

### Geographic and group-proxy bias

Neighbourhood is useful for market context but can proxy for income, housing conditions, demographics, and unequal access to services. A lower borough mean may reflect listing mix, guest expectations, review patterns, or sample size rather than neighbourhood residents or hosts being inherently worse. Reviewer nationality in the Booking.com file can also proxy for cultural or demographic differences in review behavior; nationality should not be treated as ethnicity or a direct explanation of score differences.

**Implication:** use neighbourhood and nationality carefully, report adequate cell sizes, and never infer personal attributes that are absent from the data. Do not use these features to deny service, label a host as risky, or make individual enforcement decisions.

## 3. Fairness safeguards for the planned ML model

The recommended learning task is **predicting overall Airbnb review rating for listings that have an observed rating**, as a diagnostic aid for identifying listing profiles associated with lower predicted scores. It is not a model of intrinsic quality, guest safety, or causal impact.

### Model design safeguards

- Define the target and intended use before training. Keep the prediction in a research/triage context; do not rank, penalize, price, or delist individual hosts from it.
- Prevent leakage: exclude overall rating and every review sub-score, review count/activity/recency, review text/sentiment, calendar-derived unavailability and occupancy/revenue estimates, and any field created from the target or future outcomes. The feature-engineering report lists additional leakage controls.
- Exclude direct IDs and exact coordinates. Do not use reviewer nationality or raw text. Evaluate whether neighbourhood and host-response variables add legitimate predictive value or create group disparities; compare performance with and without them.
- Split train/test data by host where feasible so listings from the same host do not appear in both sets and inflate performance. Fit imputation, encoding, and other preprocessing using training data only.
- Compare against a simple baseline. Report MAE and RMSE (and R² as a secondary statistic) on a held-out set. Since the score is bounded and concentrated near the top, also inspect error distributions and residuals.
- Report group sample sizes and error summaries by room type, neighbourhood, and host portfolio segment. Check whether one group is systematically over- or under-predicted. Do not treat equal group means or a single parity number as proof of fairness.
- If an output would affect a person, provide a clear explanation, a route to challenge incorrect data or reasoning, meaningful human review, and ongoing monitoring. The ICO’s [AI fairness guidance](https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/artificial-intelligence/guidance-on-ai-and-data-protection/how-do-we-ensure-fairness-in-ai/) emphasizes that data protection fairness includes how people are affected and how transparent and proportionate the use is.

The set of protected characteristics is not fully observed in these project data. Therefore, the project cannot establish that the model is non-discriminatory across race, disability, or other protected groups. Do not infer protected characteristics from names, locations, or nationality to fill that gap. State this as a limitation and avoid real-world individual decisions.

## 4. London regulation and responsible interpretation

The project status report mentions the London short-let night limit. Current general guidance says that, without planning permission, a London home may generally be used for short-term letting for up to 90 nights per calendar year subject to stated conditions. The project’s calendar feature is calculated from dates marked unavailable; it cannot distinguish confirmed bookings from host blocks or other unavailable dates. It is therefore not evidence that a property exceeded a legal night limit.

Do not label hosts or properties as non-compliant from the calendar proxy, listing snapshot, or an ML prediction. Rules and property-specific conditions can vary; the [Mayor of London’s short-term letting guidance](https://www.london.gov.uk/programmes-strategies/housing-and-land/buying-and-owning-home/guidance-short-term-and-holiday-lets-london) is general information and directs people to their local authority for property-specific matters.

## 5. Practical project recommendations

1. Keep the full processed files local; prepare a minimized analysis/export table before sharing any artifact.
2. In every dashboard or report, show the date, sample size, rating coverage, and whether a value is directly observed or a proxy.
3. Aggregate results and suppress small cells; remove exact locations, IDs, reviewer nationality, hotel address/name, and review text from public-facing outputs.
4. Describe host-segment and neighbourhood differences as observational. Offer a voluntary service-improvement pilot focused on listing accuracy and value messaging, then measure outcomes before recommending scale-up.
5. Treat the future model as exploratory. Document exclusions, split design, metrics, subgroup errors, and the fact that unrated listings and protected groups are not fully represented.
6. Keep platform comparisons narrow and qualified. The data supports some comparison of review signals, but not a clean claim about which platform offers better prices or value.

## Conclusion

The main ethical risk is overclaiming from incomplete and non-comparable data: ratings are missing for about one in five Airbnb listings; review scores are subjective; group differences are confounded; and availability is only an unavailability proxy. The main privacy risk is that local row-level files retain direct identifiers, exact locations, reviewer nationality, addresses, and review text. Restrict access, minimize fields, aggregate outputs, and keep the planned model advisory and non-punitive. These controls make the project more useful by preserving insight while reducing the chance that hosts, guests, or neighbourhoods are unfairly exposed or judged.

## Sources and reference date

Guidance links were checked on 1 November 2026. Rules and regulator guidance can change; re-check before any real deployment.

- Information Commissioner's Office, [A guide to the data protection principles](https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/data-protection-principles/a-guide-to-the-data-protection-principles/).
- Information Commissioner's Office, [When do we need to do a DPIA?](https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/accountability-and-governance/data-protection-impact-assessments-dpias/when-do-we-need-to-do-a-dpia/).
- Information Commissioner's Office, [How do we ensure fairness in AI?](https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/artificial-intelligence/guidance-on-ai-and-data-protection/how-do-we-ensure-fairness-in-ai/).
- Mayor of London, [Guidance on short-term and holiday lets in London](https://www.london.gov.uk/programmes-strategies/housing-and-land/buying-and-owning-home/guidance-short-term-and-holiday-lets-london).
- Inside Airbnb, [Data policies](https://beta.insideairbnb.com/data-policies/).
