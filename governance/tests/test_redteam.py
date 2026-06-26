from governance.redteam.scenarios import run_all

def test_all_redteam_scenarios_pass():
    results = run_all()
    assert all(results.values()), results
