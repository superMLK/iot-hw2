from run_pipeline import analyse


def test_vif_handles_temp_atemp(results):
    fs = results["bike"]["feature_selection"]
    final_vif = {r["feature"] for r in fs["vif_final"]}
    assert not {"temp", "atemp"} <= final_vif
    assert any(r["removed"] in ("temp", "atemp") for r in fs["vif_rounds"])
    for r in fs["vif_final"]:
        assert r["vif"] <= fs["vif_threshold"]


def test_comparison_and_final(results):
    for r in results.values():
        fs = r["feature_selection"]
        assert len(fs["comparison"]) == fs["n_candidates"]
        kept = [c["feature"] for c in fs["comparison"] if c["stepwise_kept"]]
        assert sorted(kept) == sorted(fs["final_features"])
        assert all(c["vif_kept"] for c in fs["comparison"] if c["stepwise_kept"])
        for s in fs["stepwise_steps"]:
            assert s["action"] in ("add", "remove")


def test_selection_ignores_test_set(configs, raw, stub_content, results):
    cfg = configs["bike"]
    df = raw["bike"].copy().sort_values("dteday").reset_index(drop=True)
    n_train = int(len(df) * 0.8)
    df.loc[n_train:, "cnt"] = df.loc[n_train:, "cnt"][::-1].values * 3
    changed = analyse(cfg, df, stub_content)["feature_selection"]
    assert changed == results["bike"]["feature_selection"]
