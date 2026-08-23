# NFL Draft and Special-Teams Research

This is the central navigation page for the project. Shared source data live in [`data/`](data/), reusable Python code lives in [`src/`](src/), and each research question has its own folder under [`analyses/`](analyses/).

The primary study is documented in the professional report [NFL Special-Teams Draft Value and Realized Career Outcomes](analyses/01_special_teams_value_over_time/README_SPECIAL_TEAMS_DRAFT_VALUE_AND_REALIZED_OUTCOMES.md).

## Questions and results

| # | Research question | Main result | Analysis folder |
|---:|---|---|---|
| 1 | Has NFL special-teams draft value changed over time? | Special teams fell from 2.75% of picks in the 1980s to 1.61% in the 2010s. The annual decline is modest but statistically significant (p = 0.0148). | [`01_special_teams_value_over_time`](analyses/01_special_teams_value_over_time/) |
| 2 | Do early specialist selections outperform later selections? | Early-round K/P averaged 141 games and 18.7 wAV; round 6+ selections averaged 65.6 games and 8.6 wAV. Round-group differences are statistically significant. | [`02_early_vs_late_selections`](analyses/02_early_vs_late_selections/) |
| 3 | How efficiently do drafted specialists convert draft capital into outcomes? | Expected outcomes are modeled from pick number and position; player residuals measure performance above or below pick-based expectation without unstable ratios. | [`03_draft_capital_efficiency`](analyses/03_draft_capital_efficiency/) |
| 4 | Has drafted-specialist efficiency changed over time? | Pick-adjusted outcomes are negative in the 1980s–1990s and positive in the 2000s–early 2010s, suggesting improved selectivity but not proving it. | [`04_efficiency_over_time`](analyses/04_efficiency_over_time/) |
| 5 | How should drafted-specialist success be defined? | Success is reported under six transparent definitions, including any NFL game, 48+ games, 80+ games, positive wAV, Pro Bowl, and All-Pro. | [`05_success_definitions`](analyses/05_success_definitions/) |
| 6 | Do drafted K/P outperform comparable undrafted specialists in their first three seasons? | Drafted specialists receive roughly 10–11 more early-career games and last longer, but core accuracy and punting advantages are small and statistically uncertain. | [`06_drafted_vs_undrafted`](analyses/06_drafted_vs_undrafted/) |

## Recommended reading order

1. Start with [Question 1](analyses/01_special_teams_value_over_time/) for the historical league-wide picture.
2. Read [Questions 2–5](analyses/02_early_vs_late_selections/) for drafted-only value and success analyses.
3. Finish with [Question 6](analyses/06_drafted_vs_undrafted/) for the drafted-versus-undrafted extension.

## Shared data

| Dataset | Purpose |
|---|---|
| [`data/raw/draft_picks.csv`](data/raw/draft_picks.csv) | nflverse draft selections and career outcomes |
| [`data/raw/draft_values.csv`](data/raw/draft_values.csv) | Stuart, Johnson, Hill, OTC, and PFF pick-value charts |
| [`data/processed/draft_picks_enriched.csv`](data/processed/draft_picks_enriched.csv) | Joined draft data with decade and special-teams indicators |

Question 6 has additional cached player, kicking, punting, and contract data inside [`specialist_analysis/data/raw/`](specialist_analysis/data/raw/).

## Reproduce the analyses

```bash
source .venv/bin/activate
pip install -r requirements.txt

# Question 1
python src/analyze.py

# Questions 2–5
python src/specialist_value_analysis.py

# Question 6
python specialist_analysis/analyze.py

# All project tests
pytest -q
pytest -q specialist_analysis/test_analysis.py
```

## Project map

```text
NFL/
├── README.md                         # This navigation page
├── analyses/
│   ├── 01_special_teams_value_over_time/
│   ├── 02_early_vs_late_selections/
│   ├── 03_draft_capital_efficiency/
│   ├── 04_efficiency_over_time/
│   ├── 05_success_definitions/
│   └── 06_drafted_vs_undrafted/
├── data/                             # Shared draft data
├── src/                              # Shared analysis code for Questions 1–5
├── specialist_analysis/              # Question 6 code and cached data
└── tests/                            # Tests for Questions 1–5
```

## Interpretation warning

These are observational analyses. Statistical associations do not prove that draft position or draft status causes better performance. Weighted Approximate Value is also an incomplete measure of kicker and punter contributions, so the project reports games, specialist-specific performance, and multiple success definitions alongside AV.

## License and data attribution

Project code is released under the [MIT License](LICENSE). The included NFL datasets retain their original source terms and attribution; principal sources are nflverse and Pro Football Reference, as documented within each analysis README.
