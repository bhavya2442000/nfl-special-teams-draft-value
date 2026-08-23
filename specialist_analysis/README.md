# Drafted vs. Undrafted NFL Kickers and Punters

## Research question

> Do drafted kickers and punters produce better first-three-season performance and career longevity than comparable undrafted specialists, and does that advantage justify the draft capital used to acquire them?

## Bottom line

Drafted specialists received substantially more early-career playing time and generally lasted longer, but they were not clearly better at their core jobs once they played. After adjusting for rookie year, drafted kickers had only a 2.2 percentage-point field-goal advantage (p = 0.388) and a 1.9-point field-goal-percentage-over-expected advantage (p = 0.397). Drafted punters had a 0.33-yard net-punting advantage (p = 0.415). None is statistically distinguishable from zero in this sample.

The robust differences concern opportunity and survival. Drafted kickers played an adjusted 11.2 more games in their first three seasons (p < 0.001); drafted punters played 10.5 more (p < 0.001). Among mature 1999–2015 cohorts, drafted kickers lasted an adjusted 2.25 more seasons, though the estimate is imprecise (p = 0.073). Drafted punters lasted 4.11 more seasons (p < 0.001).

That is evidence that draft status predicts who gets and keeps an NFL job. It is not clean evidence that using a pick causes better performance. Teams may draft the best prospects, and drafted players may receive more chances because the club has already invested in them. On the available outcomes, the analysis does **not** establish that the on-field accuracy or punting gain alone justifies sacrificing a pick.

## Sample and approach

The analysis uses 317 specialists whose nflverse position is kicker or punter and whose recorded rookie season is 1999–2022:

| Position | Drafted | Undrafted | Total |
|---|---:|---:|---:|
| Kicker | 46 | 120 | 166 |
| Punter | 49 | 102 | 151 |
| **Total** | **95** | **222** | **317** |

An undrafted player is one with no `draft_pick` in the nflverse player registry. First-three-season outcomes cover the rookie season and the next two calendar seasons, including zero-opportunity players in the cohort counts. Performance means necessarily describe players who recorded the relevant attempt; sample sizes for every statistic are stored alongside the means in the summary table.

The principal comparison is an OLS regression with HC3 robust standard errors:

```text
outcome = drafted indicator + centered rookie year + error
```

This adjusts for a linear era trend but is not a causal design. It does not fully make drafted and undrafted players comparable on college performance, scouting grade, age, or team situation because those covariates are not available in the source data.

### Kicker outcomes

Regular-season nflverse kicking summaries supply field-goal attempts and makes, distance bins, extra points, and games. Field-goal percentage over expected (FGOE) is estimated at the attempt level with a logistic model containing distance, distance squared, and season fixed effects. Player FGOE is actual makes minus predicted makes, divided by modeled attempts.

### Punter outcomes

Punts are extracted from nflverse play-by-play. Excluding blocked punts and records without distance, reconstructed net yards are:

```text
punt distance − return yards − 20 × touchback
```

The analysis also measures inside-the-20 rate, touchback rate, return yards allowed per punt, games, and attempts. Public nflverse play-by-play does not contain hang time, so hang time is explicitly unavailable rather than imputed.

### Longevity, compensation, and draft capital

Career longevity is evaluated only for 1999–2015 rookie cohorts, providing every player eight seasons of potential follow-up. `last_season − rookie_season + 1` measures career span; it is not an exact count of seasons with a regular-season appearance.

The first Over The Cap contract observed no later than one season after the rookie year is used as an exploratory rookie-cost proxy. Coverage is incomplete (144 of 317 players), especially for undrafted players, so compensation results should not be treated as a definitive surplus-value test.

Draft capital uses the Stuart value already stored in the parent project. The 46 drafted kickers had a median pick of 171.5 and used 120.8 Stuart points in total. The 49 punters had a median pick of 179 and used 96.7 points.

## Descriptive results

| Outcome | Drafted K | Undrafted K | Drafted P | Undrafted P |
|---|---:|---:|---:|---:|
| Field-goal percentage | 76.8% | 75.1% | — | — |
| FGOE per attempt | −3.5 pp | −5.6 pp | — | — |
| Extra-point percentage | 96.9% | 90.5% | — | — |
| Net yards per punt | — | — | 37.83 | 37.70 |
| Punts inside 20 | — | — | 31.4% | 30.2% |
| Touchback rate | — | — | 8.0% | 8.2% |
| Return yards allowed per punt | — | — | 4.14 | 4.21 |
| First-three-season games | 31.3 | 19.9 | 39.2 | 29.0 |
| Mature-cohort career span | 8.2 | 5.9 | 9.1 | 5.0 |
| Reached an eight-year career span | 48.5% | 38.0% | 58.8% | 28.6% |

Distance-specific kicker accuracy is in `drafted_vs_undrafted_summary.csv`. These unweighted player means can be volatile for specialists with few attempts; the attempt-level FGOE model is the more defensible accuracy comparison.

## Interpretation

The findings support three conclusions:

1. Draft status strongly predicts opportunity. Drafted specialists play roughly ten to eleven additional games during the first three seasons.
2. Drafted punters have much greater observed longevity. The kicker longevity result points in the same direction but is not precise at the conventional 5% level.
3. Core performance differences are small and uncertain. The sample cannot reject no drafted advantage in field-goal accuracy, FGOE, net punting, inside-the-20 rate, touchback rate, or return prevention.

The most plausible reading is that teams use picks to secure prospects they believe are more likely to hold a roster spot, not that drafted specialists deliver a large, directly observable per-attempt performance premium. Because draft status also affects patience and opportunity, the longevity advantage combines talent selection with organizational investment.

## Limitations

- The player registry includes offseason/practice-squad players who may never record an NFL attempt. This is useful for avoiding survivorship bias in opportunity counts, but performance comparisons condition on playing.
- Era adjustment is linear and cannot control for prospect quality or team-specific selection.
- Punter net yards are reconstructed from play-by-play and may differ slightly from official statistical treatments.
- Career span can include gaps and is not a season-by-season games count.
- Contract coverage is too incomplete for a definitive rookie compensation or dollar-surplus calculation.
- Hang time is unavailable.
- Hypothesis tests are not corrected for multiple comparisons; emphasis belongs on effect sizes and confidence intervals.

## Reproduction

From the parent `NFL` directory:

```bash
source .venv/bin/activate
python specialist_analysis/analyze.py
pytest -q specialist_analysis/test_analysis.py
```

The first run downloads public nflverse source snapshots and streams each play-by-play season. It caches only the required raw tables and filtered punt plays. Later runs use the cache.

## Files

```text
specialist_analysis/
├── analyze.py
├── requirements.txt
├── test_analysis.py
├── data/raw/
│   ├── players.csv
│   ├── kicking_season.csv
│   ├── historical_contracts.csv.gz
│   └── punting_plays.csv
└── outputs/
    ├── figures/first_three_season_games.png
    └── tables/
        ├── cohort_adjusted_regressions.csv
        ├── draft_capital_used.csv
        ├── drafted_vs_undrafted_summary.csv
        ├── key_results.json
        └── player_level_first_three_seasons.csv
```

## Sources

- [nflverse players release](https://github.com/nflverse/nflverse-data/releases/tag/players)
- [nflverse player-stat releases](https://github.com/nflverse/nflverse-data/releases/tag/player_stats)
- [nflverse play-by-play releases](https://github.com/nflverse/nflverse-data/releases/tag/pbp)
- [nflverse contracts loader and documentation](https://github.com/nflverse/nflreadpy/blob/main/src/nflreadpy/load_contracts.py)
