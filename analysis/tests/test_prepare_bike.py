from pipeline.preparation import prepare_bike


def test_leakage_columns_removed(configs, raw):
    prep = prepare_bike(raw["bike"], configs["bike"])
    for col in ["casual", "registered", "instant", "dteday", "workingday", "cnt"]:
        assert col not in prep.features
    leak = [s for s in prep.steps if "casual" in s["name"]]
    assert leak and leak[0].get("highlight") and "cnt" in leak[0]["reason"]


def test_steps_have_reason_and_effect(results):
    for r in results.values():
        for s in r["crisp_dm"]["data_preparation"]["steps"]:
            assert s["name"] and s["reason"] and s["affected"]


def test_time_split(configs, raw):
    prep = prepare_bike(raw["bike"], configs["bike"])
    assert len(prep.X_train) == int(731 * 0.8)
    assert prep.dates_test.min() > prep.dates_train.max()


def test_one_hot_drops_baseline(configs, raw):
    prep = prepare_bike(raw["bike"], configs["bike"])
    assert "season_1" not in prep.features and "season_2" in prep.features
    assert "weekday_0" not in prep.features and "mnth_1" not in prep.features
