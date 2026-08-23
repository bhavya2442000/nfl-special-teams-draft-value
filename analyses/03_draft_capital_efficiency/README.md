# Question 3: How Efficiently Do Specialists Convert Draft Capital Into Outcomes?

## Answer

The analysis estimates expected `log(1 + wAV)` and `log(1 + career games)` from overall pick, squared pick, and specialist position. The difference between actual and expected performance is the player's pick-adjusted surplus.

This residual approach is preferable to `AV / pick value`, because several pick-value charts approach zero for late selections and create unstable ratios. It measures performance surplus, not financial surplus.

## Files

- [`tables/specialists_with_surplus.csv`](tables/specialists_with_surplus.csv): player-level expected-performance residuals
- [`tables/wav_surplus_model.txt`](tables/wav_surplus_model.txt): wAV expectation model
- [`tables/games_surplus_model.txt`](tables/games_surplus_model.txt): games expectation model

Run with `python src/specialist_value_analysis.py`.
