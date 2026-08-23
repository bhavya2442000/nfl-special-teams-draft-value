"""Drafted-specialist value analysis using only the existing local data."""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import statsmodels.formula.api as smf
from scipy.stats import chi2_contingency, kruskal

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "processed" / "draft_picks_enriched.csv"
ANALYSES = ROOT / "analyses"
Q2 = ANALYSES / "02_early_vs_late_selections"
Q3 = ANALYSES / "03_draft_capital_efficiency"
Q4 = ANALYSES / "04_efficiency_over_time"
Q5 = ANALYSES / "05_success_definitions"
Q2_FIG, Q2_TAB = Q2 / "figures", Q2 / "tables"
Q3_TAB = Q3 / "tables"
Q4_FIG, Q4_TAB = Q4 / "figures", Q4 / "tables"
Q5_FIG, Q5_TAB = Q5 / "figures", Q5 / "tables"


def load_specialists() -> pd.DataFrame:
    """Load mature drafted K/P cohorts and construct analysis variables."""
    if not DATA.exists():
        raise FileNotFoundError("Run `python src/analyze.py` before this analysis.")
    df = pd.read_csv(DATA)
    df = df[
        df["is_special_teams"].eq(True)
        & df["category"].isin(["K", "P"])
        & df["season"].between(1980, 2015)
    ].copy()
    df["position_name"] = df["category"].map({"K": "Kicker", "P": "Punter"})
    # nflverse notes that absent PFR IDs normally indicate the player never
    # appeared in an NFL game. Preserve those draft investments as zero outcomes.
    no_nfl_appearance = df["pfr_player_id"].isna() & df["games"].isna()
    df.loc[no_nfl_appearance, ["games", "w_av"]] = 0
    # Pre-1993 drafts had more than seven rounds, so "late" must include 8+.
    df["round_group"] = pd.cut(
        df["round"], bins=[0, 3, 5, np.inf],
        labels=["Early (1–3)", "Middle (4–5)", "Late (6+)"]
    )
    df["played_one_game"] = df["games"].fillna(0).ge(1)
    df["games_48"] = df["games"].fillna(0).ge(48)
    df["games_80"] = df["games"].fillna(0).ge(80)
    df["positive_wav"] = df["w_av"].fillna(0).gt(0)
    df["pro_bowl"] = df["probowls"].fillna(0).gt(0)
    df["all_pro"] = df["allpro"].fillna(0).gt(0)
    # Available years is a longevity proxy, not seasons actually played.
    df["career_span"] = np.where(df["to"].notna(), df["to"] - df["season"] + 1, 0)
    return df


def round_group_summary(df: pd.DataFrame) -> pd.DataFrame:
    summary = (
        df.groupby(["round_group", "position_name"], observed=True)
        .agg(
            players=("pick", "size"),
            median_pick=("pick", "median"),
            mean_games=("games", "mean"),
            median_games=("games", "median"),
            mean_w_av=("w_av", "mean"),
            median_w_av=("w_av", "median"),
            mean_career_span=("career_span", "mean"),
            rate_48_games=("games_48", "mean"),
            rate_80_games=("games_80", "mean"),
            pro_bowl_rate=("pro_bowl", "mean"),
            all_pro_rate=("all_pro", "mean"),
        )
        .reset_index()
    )
    summary.to_csv(Q2_TAB / "round_group_outcomes.csv", index=False)
    return summary


def estimate_surplus(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Estimate pick-adjusted outcome residuals rather than unstable ratios."""
    model_df = df[df["w_av"].notna() & df["games"].notna()].copy()
    model_df["log_w_av"] = np.log1p(model_df["w_av"].clip(lower=0))
    model_df["log_games"] = np.log1p(model_df["games"].clip(lower=0))
    model_df["pick100"] = model_df["pick"] / 100

    # Do not include decade fixed effects: doing so would force mean residuals
    # by decade toward zero and prevent an over-time efficiency comparison.
    wav_model = smf.ols(
        "log_w_av ~ pick100 + I(pick100 ** 2) + C(position_name)", data=model_df
    ).fit(cov_type="HC3")
    games_model = smf.ols(
        "log_games ~ pick100 + I(pick100 ** 2) + C(position_name)", data=model_df
    ).fit(cov_type="HC3")
    model_df["wav_surplus"] = wav_model.resid
    model_df["games_surplus"] = games_model.resid
    model_df.to_csv(Q3_TAB / "specialists_with_surplus.csv", index=False)

    summary = (
        model_df.groupby(["decade_label", "position_name"], as_index=False)
        .agg(
            players=("pick", "size"),
            mean_wav_surplus=("wav_surplus", "mean"),
            median_wav_surplus=("wav_surplus", "median"),
            mean_games_surplus=("games_surplus", "mean"),
            median_games_surplus=("games_surplus", "median"),
        )
    )
    summary.to_csv(Q4_TAB / "surplus_by_decade.csv", index=False)
    clean_wav = "\n".join(line.rstrip() for line in wav_model.summary().as_text().splitlines()) + "\n"
    clean_games = "\n".join(line.rstrip() for line in games_model.summary().as_text().splitlines()) + "\n"
    (Q3_TAB / "wav_surplus_model.txt").write_text(clean_wav)
    (Q3_TAB / "games_surplus_model.txt").write_text(clean_games)
    return model_df, summary


def success_rates(df: pd.DataFrame) -> pd.DataFrame:
    measures = ["played_one_game", "games_48", "games_80", "positive_wav", "pro_bowl", "all_pro"]
    long = df.melt(
        id_vars=["round_group", "position_name"], value_vars=measures,
        var_name="success_definition", value_name="success",
    )
    rates = (
        long.groupby(["round_group", "position_name", "success_definition"], observed=True)
        .agg(players=("success", "size"), successes=("success", "sum"), rate=("success", "mean"))
        .reset_index()
    )
    rates.to_csv(Q5_TAB / "success_rates.csv", index=False)
    return rates


def statistical_tests(df: pd.DataFrame) -> dict:
    groups_games = [x["games"].dropna() for _, x in df.groupby("round_group", observed=True)]
    groups_wav = [x["w_av"].dropna() for _, x in df.groupby("round_group", observed=True)]
    kg = kruskal(*groups_games)
    kw = kruskal(*groups_wav)
    contingency = pd.crosstab(df["round_group"], df["games_48"])
    chi = chi2_contingency(contingency)
    return {
        "sample_n": int(len(df)),
        "kickers": int(df["category"].eq("K").sum()),
        "punters": int(df["category"].eq("P").sum()),
        "games_by_round_kruskal_h": float(kg.statistic),
        "games_by_round_p_value": float(kg.pvalue),
        "wav_by_round_kruskal_h": float(kw.statistic),
        "wav_by_round_p_value": float(kw.pvalue),
        "games_48_by_round_chi_square": float(chi.statistic),
        "games_48_by_round_p_value": float(chi.pvalue),
    }


def make_figures(summary: pd.DataFrame, surplus: pd.DataFrame, rates: pd.DataFrame) -> None:
    sns.set_theme(style="whitegrid", context="talk")
    order = ["Early (1–3)", "Middle (4–5)", "Late (6+)"]

    fig, axes = plt.subplots(1, 2, figsize=(15, 6))
    sns.barplot(data=summary, x="round_group", y="mean_games", hue="position_name", order=order, ax=axes[0])
    axes[0].set(xlabel="Draft investment", ylabel="Mean career games", title="Career games by draft-round group")
    sns.barplot(data=summary, x="round_group", y="mean_w_av", hue="position_name", order=order, ax=axes[1])
    axes[1].set(xlabel="Draft investment", ylabel="Mean weighted AV", title="Weighted AV by draft-round group")
    for ax in axes: ax.tick_params(axis="x", rotation=15)
    fig.tight_layout(); fig.savefig(Q2_FIG / "round_group_outcomes.png", dpi=200); plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(15, 6))
    sns.pointplot(data=surplus, x="decade_label", y="wav_surplus", hue="position_name", errorbar=("ci", 95), ax=axes[0])
    axes[0].axhline(0, color="black", lw=1); axes[0].set(title="Pick-adjusted weighted-AV surplus", xlabel="Draft decade", ylabel="Mean residual")
    sns.pointplot(data=surplus, x="decade_label", y="games_surplus", hue="position_name", errorbar=("ci", 95), ax=axes[1])
    axes[1].axhline(0, color="black", lw=1); axes[1].set(title="Pick-adjusted games surplus", xlabel="Draft decade", ylabel="Mean residual")
    fig.tight_layout(); fig.savefig(Q4_FIG / "surplus_over_time.png", dpi=200); plt.close(fig)

    focus = rates[rates["success_definition"].isin(["games_48", "games_80", "pro_bowl"])]
    fig, ax = plt.subplots(figsize=(12, 7))
    sns.barplot(data=focus, x="round_group", y="rate", hue="success_definition", order=order, ax=ax)
    ax.set(xlabel="Draft investment", ylabel="Success rate", title="Alternative definitions of drafted-specialist success")
    ax.tick_params(axis="x", rotation=15)
    fig.tight_layout(); fig.savefig(Q5_FIG / "success_definitions.png", dpi=200); plt.close(fig)


def main() -> None:
    for path in (Q2_FIG, Q2_TAB, Q3_TAB, Q4_FIG, Q4_TAB, Q5_FIG, Q5_TAB):
        path.mkdir(parents=True, exist_ok=True)
    df = load_specialists()
    summary = round_group_summary(df)
    surplus, _ = estimate_surplus(df)
    rates = success_rates(df)
    tests = statistical_tests(df)
    (Q2_TAB / "statistical_tests.json").write_text(json.dumps(tests, indent=2))
    make_figures(summary, surplus, rates)
    print(json.dumps(tests, indent=2))


if __name__ == "__main__":
    main()
