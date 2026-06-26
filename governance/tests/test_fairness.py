from governance.fairness.disparate_impact import four_fifths

def test_passes_when_balanced():
    rep = four_fifths(selected={"A": 50, "B": 48}, totals={"A": 100, "B": 100})
    assert rep.passes_four_fifths

def test_flags_disparate_group():
    rep = four_fifths(selected={"A": 80, "B": 30}, totals={"A": 100, "B": 100})
    assert not rep.passes_four_fifths and "B" in rep.flagged_groups
