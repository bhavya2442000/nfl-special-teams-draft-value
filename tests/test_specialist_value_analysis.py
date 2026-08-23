import pandas as pd

from src.specialist_value_analysis import load_specialists


def test_specialist_sample_is_mature_kickers_and_punters_only():
    df = load_specialists()
    assert set(df["category"]) == {"K", "P"}
    assert df["season"].max() == 2015
    assert df["season"].min() == 1980


def test_round_groups_cover_sample():
    df = load_specialists()
    assert df["round_group"].notna().all()
    assert set(df["round_group"].astype(str)) == {
        "Early (1–3)", "Middle (4–5)", "Late (6+)"
    }


def test_success_indicators_are_boolean():
    df = load_specialists()
    for name in ["played_one_game", "games_48", "games_80", "positive_wav", "pro_bowl", "all_pro"]:
        assert df[name].dtype == bool


def test_nonparticipants_are_retained_as_zero_outcomes():
    df = load_specialists()
    no_id = df["pfr_player_id"].isna()
    assert (df.loc[no_id, "games"] == 0).all()
    assert (df.loc[no_id, "w_av"] == 0).all()
