# Real A/B Test: Clear Value Messaging on a Fictional Listing

## What this test can answer

The project’s Airbnb analysis found observational differences in guest value and accuracy ratings. Those patterns do not show that wording causes better ratings. A simple randomized survey experiment can test a narrower, actionable question:

> Does presenting the same listing facts as a clear “what is included for the total price” summary change prospective guests’ perceived value compared with a plain paragraph?

This is a **real A/B experiment** once consenting people are randomly assigned to see one version and provide responses. It tests listing presentation with survey participants. It does not test an actual Airbnb host intervention or actual booking/review outcomes.

## The two versions

Use the same facts in both versions. Do not show both to one person.

**A — Control (plain presentation)**

> One-bedroom apartment in Stratford for two guests. Wi-Fi, kitchen, and washing machine. Stratford station is a 15-minute walk away. £120 total per night, including cleaning and service fees.

**B — Treatment (clear value summary)**

> £120 total per night, including cleaning and service fees. Your stay includes the entire one-bedroom apartment for two guests, Wi-Fi, kitchen, and washing machine. Stratford station is a 15-minute walk away.

The treatment changes the order and emphasis, not the price or property facts. That isolates whether clear presentation of inclusions affects perceived value.

## How to carry it out

1. Recruit up to 100 consenting adults (for example, classmates). Explain the short survey and collect no names or emails.
2. Open [`scripts/ab_test_design.ipynb`](../scripts/ab_test_design.ipynb) and run the setup and assignment cells once. They create `data/ab_test_randomization_schedule.csv` with balanced anonymous participant codes. The `data/` folder is Git-ignored; keep the schedule private and do not regenerate it after recruitment starts.
3. Give each participant the next unused code and show only the A or B version assigned to that code. In a paper survey, use the assigned card; online, use the corresponding A/B form or link.
4. Ask all participants the same questions: perceived value (primary, 1–5), booking consideration (secondary, 1–5), and whether they correctly recall the £120 all-in nightly price.
5. Enter each response in `data/ab_test_survey_responses.csv` using `participant_code`, `perceived_value`, `booking_intent`, and `price_check_correct`.
6. Run the notebook’s analysis cell. It joins responses to the pre-generated assignment, checks the data, compares the average ratings, and reports a confidence interval, Welch test, Mann–Whitney sensitivity test, response rates, and price recall by condition.

The notebook includes an explicitly synthetic dataset for a complete analysis walkthrough. If the real response CSV exists, real responses take precedence; otherwise the synthetic results are labeled and kept separate from real data. Synthetic findings are not evidence about people or Airbnb guests.

## Sample-size context

A target of 100 people gives approximately 50 per arm. Assuming an outcome standard deviation near 1 point on the 1–5 scale, that is enough for roughly 80% power only for a relatively large difference of about 0.56 points at a two-sided 5% significance level. This is approximate; small effects may be missed. If fewer people participate, call it an exploratory pilot and focus on the estimated difference and confidence interval rather than a binary “success/failure.”

## Why it is useful to the business

If version B earns higher perceived-value ratings and price recall remains strong, the result suggests that **clearer communication of what the total price includes may help prospective guests understand value**. A host or marketplace could test this style of presentation more broadly. If there is little or uncertain difference, the business avoids assuming that a wording change will help. Either result provides more useful evidence than simply comparing existing host groups.

## Limits and safeguards

- Random assignment supports a causal claim only about the wording shown to these respondents.
- Participants are a convenience sample, not a representative sample of Airbnb guests.
- Perceived value and stated booking interest are not actual purchases, stays, or guest ratings.
- Keep assignment and response files private. Publish aggregate results only.
- Do not use the test to rank or penalize hosts, infer service quality, or justify price increases.


## Synthetic demonstration (not real participant evidence)

The notebook can generate 100 artificial responses on a separate synthetic assignment schedule and run the same analysis pipeline. The demonstration inserts an assumed +0.50 latent shift in perceived value, +0.25 in booking intent, and higher assumed price-recall probability in version B. These assumptions are visible in the notebook code; the generated response CSV and assignment schedule are separate from the real-study files. Do not cite the synthetic estimates as a measured business effect.


## Completed synthetic A/B analysis (for learning only)

The notebook generated 100 synthetic respondents on a separate balanced random assignment (50 per arm, seed 2027) and ran the planned comparison. Synthetic outcomes were generated from declared assumptions: perceived-value latent mean 3.0 in A and 3.5 in B, booking-intent latent mean 3.0 in A and 3.25 in B, standard deviation 1.0, scores rounded/clipped to 1–5, and price recall probabilities of 70% in A and 85% in B. These assumed effects were deliberately inserted; they are not observations from people.

| Synthetic result | A control | B treatment | B minus A / test result |
| --- | ---: | ---: | --- |
| Participants | 50 | 50 | 100 total |
| Mean perceived value (1–5) | 2.82 | 3.34 | +0.52; 95% CI 0.106 to 0.934; Welch p=0.0143; Mann–Whitney p=0.0141 |
| Mean booking intent (1–5) | 3.00 | 3.56 | +0.56; 95% CI 0.175 to 0.945; Welch p=0.0048; Mann–Whitney p=0.0104 |
| Correct all-in price recall | 70% | 78% | +8 percentage points (descriptive) |

This confirms that the notebook can generate randomized arms, analyze the survey outcomes, and report uncertainty. The apparent positive effects are an expected consequence of the synthetic values chosen in the generator. They are **not a business finding** and must not be presented as evidence that clearer wording improves real guests’ value ratings. The synthetic files are `data/ab_test_randomization_schedule_synthetic.csv` and `data/ab_test_survey_responses_synthetic.csv`; they are separate from the actual participant schedule and real response path.

## Current status

The real experiment is not complete until participants are recruited, assigned, shown a version, and their actual responses are entered. A separate synthetic demonstration can be run now for learning, but it is not a real experiment result.
