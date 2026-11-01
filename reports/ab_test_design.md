# A/B Test Proposal: Listing Accuracy and Value Messaging Checklist

## Why run this test?

The project’s observational Airbnb analysis found that value ratings differ across host portfolio segments. The reported mean gap between one-listing and 21+ listing hosts is 0.296 points; accuracy is another relatively large sub-score gap (0.248 points). These are associations, not evidence that host portfolio size causes lower ratings or that a checklist will improve them.

A prospective randomized test can answer a useful business question that the current snapshot cannot: **does offering a listing accuracy and value-messaging checklist improve guests’ later perceived-value ratings compared with usual practice?** If effective, the checklist could give hosts a low-cost way to check that photos, amenities, capacity, fees, rules, and location details match the stay and that guests can understand what is included for the price. It does not prescribe a price change.

The Python notebook at [`scripts/ab_test_design.ipynb`](../scripts/ab_test_design.ipynb) provides sample-size scenarios based on historical host-level rating variation, a host-level randomization function for a consented roster, and an analysis template for future outcome data. The current data has no randomized assignment or post-checklist outcomes, so no A/B test result is claimed.

## Proposed experiment

### Hypothesis

Participating hosts offered the checklist will have a greater average increase in guest value ratings during follow-up than participating control hosts who continue usual practice. Rating coverage is a key guardrail because scores are observed only when guests leave reviews.

### Randomization and groups

- **Recruitment:** invite eligible hosts to opt in; do not enroll or rank hosts automatically.
- **Assignment unit:** host. Assigning all participating listings from a host to the same arm reduces spillover between that host’s listings.
- **Treatment:** checklist and brief instructions for reviewing listing accuracy and value information across participating listings.
- **Control:** usual practice during the test; offer the checklist afterward if practical.
- **Balance:** randomize within host portfolio segments (and consider room/borough only if the recruited sample can support those strata). Record the seed and assignment protocol before launch.

### Timing and outcomes

Use a defined pre-period and a comparable follow-up period, provisionally 90 days each. Confirm that duration against recruitment and review volume before launch. Allow for guests to submit reviews after a stay and set a final data-freeze date.

- **Primary outcome:** host-level average change in listing-level value score from pre-period to follow-up, measured on the platform’s 0–5 scale. The notebook gives each host equal weight so hosts with many listings do not dominate the treatment estimate.
- **Coverage guardrail:** share of all randomized hosts with at least one follow-up value rating, plus review counts and listing rating coverage by arm.
- **Secondary outcome:** change in accuracy score, if consistently available in both periods.
- **Do not:** label an unreviewed listing as low value or treat missing follow-up ratings as a zero.

The primary score comparison is conditional on follow-up ratings being observed. If the checklist changes whether guests leave reviews, this can create selection bias. Therefore report coverage by arm and interpret rating effects cautiously when coverage differs.

## Sample size and analysis plan

The notebook calculates approximate hosts required per arm for illustrative differences of 0.10, 0.15, and 0.20 rating points. It uses the historical distribution of host-level rating means for a rough variance estimate, two-sided alpha 0.05, 80% power, equal allocation, and an explicit 20% attrition assumption. These are planning scenarios, **not** a selected business threshold or a substitute for a statistician’s final power analysis. Stakeholders should choose the smallest worthwhile improvement and finalize sample size before assignment or outcome review.

Analyze by original assignment (intention to treat). Aggregate listing outcomes to the host first, compare host-level change between treatment and control using a Welch two-sample comparison, and report the estimate with a 95% confidence interval and p-value. Report the coverage difference with uncertainty as well. Keep all randomized hosts/listings in the coverage denominator. If there are too few participating hosts, few follow-up reviews, or wide confidence intervals, treat the pilot as inconclusive and extend or redesign it rather than claiming success or no effect.

## Prospective data required

Create one row per randomized participating listing in `data/ab_test_listing_outcomes.csv` with:

| Field | Required content |
| --- | --- |
| `host_id` | Private randomization cluster key |
| `listing_id` | Private listing key |
| `arm` | `treatment` or `control` assigned to the host |
| `baseline_value_score` | Pre-period listing mean, if observed |
| `post_value_score` | Follow-up mean of new guest value scores; null if none |
| `post_review_count` | Number of follow-up scores used |

Use the notebook’s validation checks to ensure each host appears in only one arm and scores are on the 0–5 scale. Do not store raw reviewer text or guest identifiers in this analysis file.

## Business insight the experiment could provide

The current project can identify groups and listing profiles associated with lower perceived value, but it cannot tell an operator what action will improve ratings. This experiment tests one low-cost, voluntary action. A positive, sufficiently precise result would support offering the checklist more broadly and measuring adoption. A null or imprecise result would indicate that the checklist may need revision, a longer follow-up, or more participants. Either result helps prevent the business from spending effort on an intervention that has not been evaluated.

The test would not establish why a guest gave a particular rating, prove that all listings benefit, measure objective quality, or justify host penalties or automated pricing. Results should be reported in aggregate, with rating coverage and subgroup checks, and should not be used for punitive decisions.

## Ethics and privacy safeguards

- Participation is voluntary; communicate the purpose, what is collected, and how results are used.
- Keep assignment rosters and row-level host/listing outcomes private and outside public exports.
- Publish only aggregated outcomes; suppress small cells and avoid maps or filters that identify a property.
- Do not treat neighbourhood, host size, missing ratings, or model flags as evidence of poor conduct.
- Review subgroup coverage and treatment access so small or less-reviewed host groups are not overlooked.
- The project snapshot is observational and historical. The A/B test begins only after prospective randomization and new outcomes are collected.

## Files

- Notebook: [`scripts/ab_test_design.ipynb`](../scripts/ab_test_design.ipynb)
- This protocol: `reports/ab_test_design.md`
