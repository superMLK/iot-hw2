METRIC_KEYS = {"r2", "adj_r2", "rmse", "mae", "pi_coverage"}
COEF_KEYS = {"name", "coef", "std_err", "t", "p", "ci_low", "ci_high"}


def test_bike_models(results):
    models = results["bike"]["models"]
    assert [m["type"] for m in models] == ["slr", "mlr", "mlr", "ar"]
    slr = models[0]
    top = results["bike"]["feature_selection"]["correlation"][0]["feature"]
    assert slr["features"] == [top]
    ar = models[3]
    assert 1 <= ar["ar_order"] <= 14


def test_house_models(results):
    models = results["house"]["models"]
    assert [m["type"] for m in models] == ["slr", "mlr", "mlr"]
    assert models[0]["features"] == ["sqft_living"]


def test_coefficient_tables(results):
    for r in results.values():
        for m in r["models"]:
            assert m["coefficients"]
            for row in m["coefficients"]:
                assert COEF_KEYS <= set(row)


def test_ols_intervals_ordered(results):
    for r in results.values():
        for m in r["models"]:
            if m["type"] == "ar":
                continue
            for p in m["prediction"]["points"]:
                assert p["pi_low"] <= p["ci_low"] <= p["pred"] <= p["ci_high"] <= p["pi_high"]


def test_ar_only_prediction_interval(results):
    ar = results["bike"]["models"][3]
    assert ar["prediction"]["x_kind"] == "date"
    assert ar["prediction"]["train_points"]
    for p in ar["prediction"]["points"]:
        assert p["ci_low"] is None and p["ci_high"] is None
        assert p["pi_low"] < p["pred"] < p["pi_high"]


def test_metrics_and_cv(results):
    for r in results.values():
        for m in r["models"]:
            assert METRIC_KEYS <= set(m["metrics"])
            assert 0 <= m["metrics"]["pi_coverage"] <= 1
            assert len(m["cv"]["scores_r2"]) == 5
            assert m["cv"]["mean"] is not None and m["cv"]["std"] is not None
            r_ = m["residuals"]
            assert len(r_["fitted"]) == len(r_["resid"]) and len(r_["qq_theoretical"]) == len(r_["qq_sample"])


def test_single_best_model(results):
    for r in results.values():
        best = [m for m in r["models"] if m["is_best"]]
        assert len(best) == 1
        assert all(best[0]["metrics"]["r2"] >= m["metrics"]["r2"] for m in r["models"])
