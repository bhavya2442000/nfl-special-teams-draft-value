import pandas as pd

from src.analyze import ST_CATEGORIES


def test_special_teams_categories_are_expected():
    assert {"K", "P", "LS"}.issubset(ST_CATEGORIES)


def test_raw_pick_numbers_are_unique_within_season():
    df = pd.read_csv("data/raw/draft_picks.csv")
    assert not df.duplicated(["season", "pick"]).any()


def test_draft_values_have_unique_pick_numbers():
    df = pd.read_csv("data/raw/draft_values.csv")
    assert df["pick"].is_unique
    assert df["pick"].min() == 1
