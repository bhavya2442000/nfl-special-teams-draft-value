"""Drafted versus undrafted NFL kicker and punter analysis."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import tempfile

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
import statsmodels.api as sm

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "data" / "raw"
OUT = ROOT / "outputs"
TABLES = OUT / "tables"
FIGURES = OUT / "figures"
PLAYERS_URL = "https://github.com/nflverse/nflverse-data/releases/download/players/players.csv"
KICKING_URL = "https://github.com/nflverse/nflverse-data/releases/download/player_stats/player_stats_kicking_season.csv"
CONTRACTS_URL = "https://github.com/nflverse/nflverse-data/releases/download/contracts/historical_contracts.csv.gz"
PBP_URL = "https://github.com/nflverse/nflverse-data/releases/download/pbp/play_by_play_{year}.csv.gz"
COHORT_MIN, COHORT_MAX = 1999, 2022


def setup() -> None:
    for p in (RAW, TABLES, FIGURES):
        p.mkdir(parents=True, exist_ok=True)


def download(url: str, filename: str) -> pd.DataFrame:
    target = RAW / filename
    if not target.exists():
        subprocess.run(["curl", "-L", "--fail", "--silent", "--show-error", url,
                        "-o", str(target)], check=True)
    return pd.read_csv(target)


def load_players() -> pd.DataFrame:
    p = download(PLAYERS_URL, "players.csv")
    p = p[p["position"].isin(["K", "P"]) & p["rookie_season"].between(COHORT_MIN, COHORT_MAX)].copy()
    p["rookie_season"] = p["rookie_season"].astype(int)
    p["drafted"] = p["draft_pick"].notna()
    p["draft_status"] = np.where(p["drafted"], "Drafted", "Undrafted")
    p["career_seasons"] = p["last_season"] - p["rookie_season"] + 1
    p["eight_year_player"] = p["career_seasons"] >= 8
    return p


def kicker_data(players: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    stats = download(KICKING_URL, "kicking_season.csv")
    stats = stats[(stats.season_type == "REG") & stats.player_id.isin(players.gsis_id)].copy()
    stats = stats.merge(players[["gsis_id", "rookie_season"]], left_on="player_id", right_on="gsis_id")
    stats = stats[stats.season.between(stats.rookie_season, stats.rookie_season + 2)]

    attempts = []
    for _, r in stats.iterrows():
        for result, col in ((1, "fg_made_list"), (0, "fg_missed_list"), (0, "fg_blocked_list")):
            if pd.isna(r[col]):
                continue
            for value in str(r[col]).split(";"):
                try:
                    attempts.append((r.player_id, int(r.season), result, float(value)))
                except ValueError:
                    pass
    att = pd.DataFrame(attempts, columns=["player_id", "season", "made", "distance"])
    att = att[att.distance.between(15, 70)].copy()
    fit = smf.glm("made ~ distance + I(distance ** 2) + C(season)", data=att,
                  family=sm.families.Binomial()).fit()
    att["expected_make"] = fit.predict(att)
    att["fgoe"] = att.made - att.expected_make
    fgoe = att.groupby("player_id", as_index=False).agg(
        modeled_fg_att=("made", "size"), fgoe_makes=("fgoe", "sum"))

    sums = stats.groupby("player_id", as_index=False).agg(
        games=("games", "sum"), fg_made=("fg_made", "sum"), fg_att=("fg_att", "sum"),
        pat_made=("pat_made", "sum"), pat_att=("pat_att", "sum"),
        fg_made_0_19=("fg_made_0_19", "sum"), fg_made_20_29=("fg_made_20_29", "sum"),
        fg_made_30_39=("fg_made_30_39", "sum"), fg_made_40_49=("fg_made_40_49", "sum"),
        fg_made_50_59=("fg_made_50_59", "sum"), fg_made_60_plus=("fg_made_60_", "sum"),
        fg_missed_0_19=("fg_missed_0_19", "sum"), fg_missed_20_29=("fg_missed_20_29", "sum"),
        fg_missed_30_39=("fg_missed_30_39", "sum"), fg_missed_40_49=("fg_missed_40_49", "sum"),
        fg_missed_50_59=("fg_missed_50_59", "sum"), fg_missed_60_plus=("fg_missed_60_", "sum"))
    sums = sums.merge(fgoe, on="player_id", how="left")
    sums["fg_pct"] = sums.fg_made / sums.fg_att
    sums["pat_pct"] = sums.pat_made / sums.pat_att
    sums["fgoe_per_attempt"] = sums.fgoe_makes / sums.modeled_fg_att
    for label, made, missed in [
        ("0_29", ["fg_made_0_19", "fg_made_20_29"], ["fg_missed_0_19", "fg_missed_20_29"]),
        ("30_39", ["fg_made_30_39"], ["fg_missed_30_39"]),
        ("40_49", ["fg_made_40_49"], ["fg_missed_40_49"]),
        ("50_plus", ["fg_made_50_59", "fg_made_60_plus"], ["fg_missed_50_59", "fg_missed_60_plus"])]:
        m, x = sums[made].sum(axis=1), sums[missed].sum(axis=1)
        sums[f"fg_pct_{label}"] = m / (m + x)
    return sums, att


def punter_data(players: pd.DataFrame) -> pd.DataFrame:
    cached = RAW / "punting_plays.csv"
    if cached.exists():
        punts = pd.read_csv(cached)
    else:
        ids = set(players.loc[players.position.eq("P"), "gsis_id"].dropna())
        use = ["game_id", "season", "punter_player_id", "punt_attempt", "punt_blocked",
               "kick_distance", "return_yards", "touchback", "punt_inside_twenty"]
        parts = []
        for year in range(COHORT_MIN, COHORT_MAX + 3):
            with tempfile.TemporaryDirectory() as tmp:
                source = Path(tmp) / f"pbp_{year}.csv.gz"
                subprocess.run(["curl", "-L", "--fail", "--silent", "--show-error",
                                PBP_URL.format(year=year), "-o", str(source)], check=True)
                for chunk in pd.read_csv(source, usecols=use, chunksize=100_000, low_memory=False):
                    x = chunk[(chunk.punt_attempt == 1) & chunk.punter_player_id.isin(ids)].copy()
                    if len(x): parts.append(x)
        punts = pd.concat(parts, ignore_index=True)
        punts.to_csv(cached, index=False)
    punts = punts.merge(players[["gsis_id", "rookie_season"]], left_on="punter_player_id", right_on="gsis_id")
    punts = punts[punts.season.between(punts.rookie_season, punts.rookie_season + 2)].copy()
    punts["return_yards"] = punts.return_yards.fillna(0)
    punts["touchback"] = punts.touchback.fillna(0)
    punts["net_yards"] = punts.kick_distance - punts.return_yards - 20 * punts.touchback
    valid = punts[(punts.punt_blocked.fillna(0) == 0) & punts.kick_distance.notna()]
    return valid.groupby("punter_player_id", as_index=False).agg(
        games=("game_id", "nunique"), punts=("game_id", "size"),
        gross_yards_per_punt=("kick_distance", "mean"), net_yards_per_punt=("net_yards", "mean"),
        inside_20=("punt_inside_twenty", "sum"), touchbacks=("touchback", "sum"),
        return_yards_allowed=("return_yards", "sum"))


def add_contracts(players: pd.DataFrame) -> pd.DataFrame:
    c = download(CONTRACTS_URL, "historical_contracts.csv.gz")
    c = c.sort_values(["otc_id", "year_signed"]).groupby("otc_id", as_index=False).first()
    c = c[["otc_id", "year_signed", "apy", "apy_cap_pct"]].rename(columns={
        "year_signed": "first_contract_year", "apy": "first_contract_apy",
        "apy_cap_pct": "first_contract_apy_cap_pct"})
    out = players.merge(c, on="otc_id", how="left")
    # OTC's first observed contract is treated as a rookie-contract proxy only
    # when it was signed no later than the season after the recorded rookie year.
    late = out.first_contract_year > out.rookie_season + 1
    out.loc[late, ["first_contract_apy", "first_contract_apy_cap_pct"]] = np.nan
    # Longevity outcomes use mature cohorts so all players had eight years of follow-up.
    immature = out.rookie_season > 2015
    out["eight_year_player"] = out["eight_year_player"].astype(float)
    out.loc[immature, ["career_seasons", "eight_year_player"]] = np.nan
    return out


def summarize(df: pd.DataFrame, position: str, metrics: list[str]) -> pd.DataFrame:
    x = df[df.position.eq(position)].copy()
    rows = []
    for status, g in x.groupby("draft_status", observed=True):
        row = {"position": position, "draft_status": status, "players": len(g)}
        for metric in metrics:
            row[f"{metric}_mean"] = g[metric].mean()
            row[f"{metric}_median"] = g[metric].median()
            row[f"{metric}_n"] = g[metric].notna().sum()
        rows.append(row)
    return pd.DataFrame(rows)


def regression(df: pd.DataFrame, position: str, outcomes: list[str]) -> pd.DataFrame:
    rows = []
    x = df[df.position.eq(position)].copy()
    x["rookie_centered"] = x.rookie_season - x.rookie_season.mean()
    for outcome in outcomes:
        sample = x.dropna(subset=[outcome])
        if len(sample) < 20:
            continue
        model = smf.ols(f"{outcome} ~ drafted + rookie_centered", sample).fit(cov_type="HC3")
        term = "drafted[T.True]"
        rows.append({"position": position, "outcome": outcome, "drafted_effect": model.params[term],
                     "std_error": model.bse[term], "p_value": model.pvalues[term],
                     "ci_low": model.conf_int().loc[term, 0], "ci_high": model.conf_int().loc[term, 1],
                     "n": int(model.nobs), "r_squared": model.rsquared})
    return pd.DataFrame(rows)


def main() -> None:
    setup()
    players = add_contracts(load_players())
    kick, _ = kicker_data(players)
    punt = punter_data(players)
    analysis = players.merge(kick, left_on="gsis_id", right_on="player_id", how="left")
    analysis = analysis.merge(punt, left_on="gsis_id", right_on="punter_player_id", how="left",
                              suffixes=("_kick", "_punt"))
    analysis["games_first3"] = np.where(analysis.position.eq("K"), analysis.games_kick, analysis.games_punt)
    analysis["inside_20_rate"] = analysis.inside_20 / analysis.punts
    analysis["touchback_rate"] = analysis.touchbacks / analysis.punts
    analysis["return_yards_per_punt"] = analysis.return_yards_allowed / analysis.punts
    analysis.to_csv(TABLES / "player_level_first_three_seasons.csv", index=False)

    kicker_metrics = ["fg_pct", "fgoe_per_attempt", "pat_pct", "fg_pct_0_29", "fg_pct_30_39",
                      "fg_pct_40_49", "fg_pct_50_plus", "games_first3", "career_seasons",
                      "eight_year_player", "first_contract_apy_cap_pct"]
    punter_metrics = ["net_yards_per_punt", "gross_yards_per_punt", "inside_20_rate", "touchback_rate",
                      "return_yards_per_punt", "games_first3", "career_seasons", "eight_year_player",
                      "first_contract_apy_cap_pct"]
    summary = pd.concat([summarize(analysis, "K", kicker_metrics), summarize(analysis, "P", punter_metrics)])
    summary.to_csv(TABLES / "drafted_vs_undrafted_summary.csv", index=False)
    reg = pd.concat([regression(analysis, "K", kicker_metrics[:3] + ["games_first3", "career_seasons"]),
                     regression(analysis, "P", punter_metrics[:5] + ["games_first3", "career_seasons"])])
    reg.to_csv(TABLES / "cohort_adjusted_regressions.csv", index=False)

    capital = analysis[analysis.drafted].merge(
        pd.read_csv(ROOT.parent / "data" / "raw" / "draft_values.csv")[["pick", "stuart"]],
        left_on="draft_pick", right_on="pick", how="left")
    capital.groupby("position", as_index=False).agg(players=("gsis_id", "size"),
        median_pick=("draft_pick", "median"), mean_stuart_value=("stuart", "mean"),
        total_stuart_value=("stuart", "sum")).to_csv(TABLES / "draft_capital_used.csv", index=False)

    plot = analysis[analysis.games_first3.notna()].copy()
    means = plot.groupby(["position", "draft_status"], as_index=False).games_first3.mean()
    fig, ax = plt.subplots(figsize=(8, 5))
    for i, pos in enumerate(["K", "P"]):
        z = means[means.position.eq(pos)].set_index("draft_status").games_first3
        ax.bar([i - .18, i + .18], [z.get("Drafted", np.nan), z.get("Undrafted", np.nan)], width=.34,
               color=["#174A7E", "#A8B7C7"])
    ax.set_xticks([0, 1], ["Kickers", "Punters"]); ax.set_ylabel("Mean games in first 3 seasons")
    ax.set_title("Early-career opportunity by acquisition route")
    ax.legend(["Drafted", "Undrafted"], frameon=False)
    fig.tight_layout(); fig.savefig(FIGURES / "first_three_season_games.png", dpi=180); plt.close(fig)

    results = {"cohort_min": COHORT_MIN, "cohort_max": COHORT_MAX,
               "players": int(len(analysis)), "kickers": int((analysis.position == "K").sum()),
               "punters": int((analysis.position == "P").sum()),
               "players_with_first3_performance": int(analysis.games_first3.notna().sum())}
    (TABLES / "key_results.json").write_text(json.dumps(results, indent=2))
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
