# Question 6: Do Drafted Specialists Outperform Comparable Undrafted Specialists?

## Answer

Drafted kickers and punters received substantially more playing time in their first three seasons and generally lasted longer, but their core job-performance advantages were small and statistically uncertain after adjusting for rookie year.

- Drafted kickers: 11.2 additional first-three-season games (p < 0.001)
- Drafted punters: 10.5 additional first-three-season games (p < 0.001)
- Kicker adjusted field-goal advantage: 2.2 percentage points (p = 0.388)
- Punter adjusted net-punting advantage: 0.33 yards (p = 0.415)

The evidence supports an opportunity and survival advantage, not a clear per-attempt performance premium or definitive justification of draft capital.

## Analysis location

This question was developed as a self-contained analysis by the other agent. Its code, cached source data, detailed report, and outputs remain together in [`specialist_analysis/`](../../specialist_analysis/).

- [Detailed report and methodology](../../specialist_analysis/README.md)
- [Regression results](../../specialist_analysis/outputs/tables/cohort_adjusted_regressions.csv)
- [Drafted-versus-undrafted summary](../../specialist_analysis/outputs/tables/drafted_vs_undrafted_summary.csv)
- [Player-level data](../../specialist_analysis/outputs/tables/player_level_first_three_seasons.csv)
- [Draft-capital summary](../../specialist_analysis/outputs/tables/draft_capital_used.csv)

Run with `python specialist_analysis/analyze.py`.
