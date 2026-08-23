# Question 1: Has Special-Teams Draft Value Changed Over Time?

For the complete professional research narrative—including data selection, cleaning, EDA, models, results, and limitations—see [NFL Special-Teams Draft Value and Realized Career Outcomes](README_SPECIAL_TEAMS_DRAFT_VALUE_AND_REALIZED_OUTCOMES.md).

## Answer

NFL teams use a smaller share of picks on specialists than in the 1980s. Special teams represented 2.75% of picks in the 1980s, 1.61% in the 2010s, and 1.87% in the partial 2020–2025 period. The fitted annual decline is −0.0217 percentage points (p = 0.0148).

Among mature 1980–2015 cohorts, specialists were drafted later but played more games. Controlling for pick and decade, special-teams status is positively associated with `log(1 + wAV)`. This is consistent with selective drafting, not proof of causal value.

## Sample and method

- 12,670 selections from 1980–2025
- 253 special-teamers
- Career comparisons stop at the 2015 cohort
- Annual time trend plus robust OLS outcome model

## Files

- [`tables/key_results.json`](tables/key_results.json): headline estimates
- [`tables/yearly_special_teams_drafting.csv`](tables/yearly_special_teams_drafting.csv): yearly counts and shares
- [`tables/decade_special_teams_drafting.csv`](tables/decade_special_teams_drafting.csv): decade summary
- [`tables/outcomes_through_2015_cohorts.csv`](tables/outcomes_through_2015_cohorts.csv): mature-cohort outcomes
- [`tables/regression_log_weighted_av.csv`](tables/regression_log_weighted_av.csv): model coefficients
- [`figures/`](figures/): generated charts

Run with `python src/analyze.py` from the project root.
