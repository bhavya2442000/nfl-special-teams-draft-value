import pandas as pd


def test_output_has_one_row_per_specialist():
    df = pd.read_csv("specialist_analysis/outputs/tables/player_level_first_three_seasons.csv")
    assert not df["gsis_id"].duplicated().any()
    assert set(df["position"]) == {"K", "P"}


def test_rates_are_bounded():
    df = pd.read_csv("specialist_analysis/outputs/tables/player_level_first_three_seasons.csv")
    for column in ["fg_pct", "pat_pct", "inside_20_rate", "touchback_rate"]:
        assert df[column].dropna().between(0, 1).all()


def test_first_three_season_window():
    df = pd.read_csv("specialist_analysis/outputs/tables/player_level_first_three_seasons.csv")
    assert df["games_first3"].dropna().ge(1).all()
    assert df.loc[df.position.eq("P"), "punts"].dropna().ge(1).all()
