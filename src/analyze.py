"""Reproducible analysis of special-teams player value in NFL drafts."""
from __future__ import annotations

from pathlib import Path
import json

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import statsmodels.formula.api as smf
from scipy.stats import linregress

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"
ANALYSIS = ROOT / "analyses" / "01_special_teams_value_over_time"
FIGURES = ANALYSIS / "figures"
TABLES = ANALYSIS / "tables"

DRAFT_URL = "https://github.com/nflverse/nflverse-data/releases/download/draft_picks/draft_picks.csv"
VALUES_URL = "https://raw.githubusercontent.com/nflverse/nfldata/master/data/draft_values.csv"
ST_CATEGORIES = {"K", "P", "LS", "KR", "ST"}


def ensure_directories() -> None:
    for path in (RAW, PROCESSED, FIGURES, TABLES):
        path.mkdir(parents=True, exist_ok=True)


def download_data(refresh: bool = False) -> None:
    """Download source CSVs only when absent unless refresh is requested."""
    ensure_directories()
    for url, name in ((DRAFT_URL, "draft_picks.csv"), (VALUES_URL, "draft_values.csv")):
        target = RAW / name
        if refresh or not target.exists():
            pd.read_csv(url).to_csv(target, index=False)


def load_and_clean() -> pd.DataFrame:
    picks = pd.read_csv(RAW / "draft_picks.csv")
    values = pd.read_csv(RAW / "draft_values.csv")
    required = {"season", "pick", "round", "team", "side", "category", "position",
                "w_av", "car_av", "games", "probowls", "allpro"}
    missing = required.difference(picks.columns)
    if missing:
        raise ValueError(f"Draft data missing required columns: {sorted(missing)}")
    df = picks.merge(values, on="pick", how="left", validate="many_to_one")
    df = df[df["season"].between(1980, 2025)].copy()  # 2026 outcomes do not yet exist.
    df["is_special_teams"] = (df["side"].eq("S") | df["category"].isin(ST_CATEGORIES))
    df["decade"] = (df["season"] // 10 * 10).astype(int)
    df["decade_label"] = df["decade"].astype(str) + "s"
    df["drafted"] = 1
    df["st_category"] = np.where(df["is_special_teams"], df["category"].fillna("ST"), "Non-ST")
    # Comparisons involving accumulated outcomes are capped at 2015 to provide
    # every cohort at least ten possible NFL seasons. This reduces right-censoring.
    df["outcome_eligible"] = df["season"] <= 2015
    df.to_csv(PROCESSED / "draft_picks_enriched.csv", index=False)
    return df


def frequency_tables(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    yearly = (df.groupby("season", as_index=False)
              .agg(all_picks=("drafted", "size"), st_picks=("is_special_teams", "sum")))
    yearly["st_share_pct"] = 100 * yearly["st_picks"] / yearly["all_picks"]
    yearly.to_csv(TABLES / "yearly_special_teams_drafting.csv", index=False)

    by_decade = (df.groupby("decade_label", as_index=False)
                 .agg(all_picks=("drafted", "size"), st_picks=("is_special_teams", "sum"),
                      mean_pick=("pick", lambda x: df.loc[x.index[df.loc[x.index, "is_special_teams"]], "pick"].mean())))
    by_decade["st_share_pct"] = 100 * by_decade["st_picks"] / by_decade["all_picks"]
    by_decade.to_csv(TABLES / "decade_special_teams_drafting.csv", index=False)
    return yearly, by_decade


def outcome_table(df: pd.DataFrame) -> pd.DataFrame:
    eligible = df[df["outcome_eligible"]].copy()
    eligible["group"] = np.where(eligible["is_special_teams"], "Special teams", "Other positions")
    outcome = (eligible.groupby("group", as_index=False)
               .agg(players=("pick", "size"), median_pick=("pick", "median"),
                    mean_w_av=("w_av", "mean"), median_w_av=("w_av", "median"),
                    mean_games=("games", "mean"),
                    probowl_rate=("probowls", lambda x: (x.fillna(0) > 0).mean()),
                    allpro_rate=("allpro", lambda x: (x.fillna(0) > 0).mean())))
    outcome.to_csv(TABLES / "outcomes_through_2015_cohorts.csv", index=False)
    return outcome


def models(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    eligible = df[df["outcome_eligible"] & df["w_av"].notna()].copy()
    eligible["log_w_av"] = np.log1p(eligible["w_av"].clip(lower=0))
    eligible["pick100"] = eligible["pick"] / 100
    model = smf.ols(
        "log_w_av ~ pick100 + is_special_teams + C(decade_label)", data=eligible
    ).fit(cov_type="HC3")
    coef = pd.DataFrame({
        "term": model.params.index,
        "estimate": model.params.values,
        "std_error": model.bse.values,
        "p_value": model.pvalues.values,
        "ci_low": model.conf_int()[0].values,
        "ci_high": model.conf_int()[1].values,
    })
    coef.to_csv(TABLES / "regression_log_weighted_av.csv", index=False)

    yearly = pd.read_csv(TABLES / "yearly_special_teams_drafting.csv")
    trend = linregress(yearly["season"], yearly["st_share_pct"])
    diagnostics = {
        "analysis_year_min": int(df.season.min()),
        "analysis_year_max": int(df.season.max()),
        "total_picks": int(len(df)),
        "special_teams_picks": int(df.is_special_teams.sum()),
        "special_teams_share_pct": float(100 * df.is_special_teams.mean()),
        "trend_percentage_points_per_year": float(trend.slope),
        "trend_p_value": float(trend.pvalue),
        "trend_r_squared": float(trend.rvalue ** 2),
        "outcome_cohort_max": 2015,
        "regression_n": int(model.nobs),
        "regression_r_squared": float(model.rsquared),
    }
    st_row = coef.loc[coef.term.eq("is_special_teams[T.True]")]
    if not st_row.empty:
        diagnostics["st_log_wav_coefficient"] = float(st_row.iloc[0].estimate)
        diagnostics["st_log_wav_p_value"] = float(st_row.iloc[0].p_value)
    clean_summary = "\n".join(line.rstrip() for line in model.summary().as_text().splitlines()) + "\n"
    (TABLES / "model_summary.txt").write_text(clean_summary)
    (TABLES / "key_results.json").write_text(json.dumps(diagnostics, indent=2))
    return coef, diagnostics


def figures(df: pd.DataFrame, yearly: pd.DataFrame) -> None:
    sns.set_theme(style="whitegrid", context="talk")
    fig, ax = plt.subplots(figsize=(11, 6))
    sns.regplot(data=yearly, x="season", y="st_share_pct", ax=ax,
                scatter_kws={"s": 45, "alpha": .75}, line_kws={"color": "#c1121f"})
    ax.set(title="Special-teams share of NFL draft picks, 1980–2025",
           xlabel="Draft year", ylabel="Special-teams picks (% of all picks)")
    fig.tight_layout(); fig.savefig(FIGURES / "special_teams_share_over_time.png", dpi=200); plt.close(fig)

    st = df[df["is_special_teams"]].copy()
    categories = st["category"].value_counts().index
    fig, ax = plt.subplots(figsize=(11, 6))
    sns.boxplot(data=st, x="decade_label", y="pick", hue="category", hue_order=categories, ax=ax)
    ax.invert_yaxis()
    ax.set(title="Where special-teams players were selected", xlabel="Draft decade",
           ylabel="Overall pick (earlier picks appear higher)")
    ax.legend(title="Position", bbox_to_anchor=(1.02, 1), loc="upper left")
    fig.tight_layout(); fig.savefig(FIGURES / "special_teams_pick_by_decade.png", dpi=200); plt.close(fig)

    eligible = df[df["outcome_eligible"]].copy()
    eligible["group"] = np.where(eligible["is_special_teams"], "Special teams", "Other positions")
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.scatterplot(data=eligible.sample(min(3500, len(eligible)), random_state=51),
                    x="pick", y="w_av", hue="group", alpha=.45, s=35, ax=ax)
    ax.set(yscale="symlog", title="Weighted AV versus draft position (1980–2015 cohorts)",
           xlabel="Overall pick", ylabel="Weighted career AV (symlog scale)")
    fig.tight_layout(); fig.savefig(FIGURES / "weighted_av_vs_pick.png", dpi=200); plt.close(fig)


def main() -> None:
    ensure_directories(); download_data(); df = load_and_clean()
    yearly, _ = frequency_tables(df); outcome_table(df); _, diagnostics = models(df); figures(df, yearly)
    print(json.dumps(diagnostics, indent=2))


if __name__ == "__main__":
    main()
