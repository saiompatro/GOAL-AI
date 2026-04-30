from __future__ import annotations

import pandas as pd

from goal_ai.simulate import group_fixtures, simulate_tournament


def test_simulate_tournament_probability_contract():
    groups = {
        f"G{i:02d}": [f"T{i:02d}{j}" for j in range(4)]
        for i in range(12)
    }
    fixtures = group_fixtures(groups)

    out = simulate_tournament(None, fixtures, n=100, random_state=7)

    assert isinstance(out, pd.DataFrame)
    assert set(out.columns) == {"team", "p_win", "p_final", "p_semi", "p_quarter", "p_groupexit"}
    assert len(out) == 48
    assert abs(out["p_win"].sum() - 1.0) < 1e-9
    assert ((out[["p_win", "p_final", "p_semi", "p_quarter", "p_groupexit"]] >= 0).all().all())
    assert ((out[["p_win", "p_final", "p_semi", "p_quarter", "p_groupexit"]] <= 1).all().all())
