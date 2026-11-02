import numpy as np

from pipeline.preparation import prepare_house

EXPECTED = {
    "bedrooms", "bathrooms", "sqft_living", "sqft_lot", "floors", "waterfront", "view", "condition", "grade",
    "lat", "long", "sqft_living15", "sqft_lot15", "sale_year", "is_renovated", "house_age", "has_basement",
} | {f"sale_month_{m}" for m in range(2, 13)}


def test_house_features(configs, raw):
    prep = prepare_house(raw["house"], configs["house"])
    assert set(prep.features) == EXPECTED
    for col in ["id", "zipcode", "sqft_above", "sqft_basement", "yr_built", "yr_renovated", "date", "price"]:
        assert col not in prep.features


def test_outlier_rules_logged(configs, raw):
    prep = prepare_house(raw["house"], configs["house"])
    rules = [s for s in prep.steps if s["name"].startswith("移除異常值")]
    assert len(rules) == 3
    assert all(s["affected"].startswith("移除 ") and s["affected"].endswith(" 筆") for s in rules)
    removed = sum(int(s["affected"].split()[1]) for s in rules)
    assert prep.after["rows"] == prep.before["rows"] - removed
    both = np.concatenate([prep.X_train["bedrooms"], prep.X_test["bedrooms"]])
    assert (both < 30).all() and (both > 0).all()


def test_log_target_and_split(configs, raw):
    prep = prepare_house(raw["house"], configs["house"])
    assert np.allclose(np.exp(prep.y_train), prep.y_train_raw)
    n = prep.after["rows"]
    assert len(prep.X_test) == int(np.ceil(n * 0.2))
    again = prepare_house(raw["house"], configs["house"])
    assert prep.X_test.equals(again.X_test)


def test_house_predictions_in_price_units(results):
    for m in results["house"]["models"]:
        for p in m["prediction"]["points"]:
            assert p["pred"] > 10_000 and p["actual"] > 10_000
            assert p["pi_low"] > 0
        assert m["metrics"]["rmse"] > 10_000  # 以美元計
        assert "log(price)" in m["metrics_note"]
    assert not any(m["type"] == "ar" for m in results["house"]["models"])


def test_house_intervals_asymmetric(results):
    p = results["house"]["models"][2]["prediction"]["points"][-1]
    assert (p["pi_high"] - p["pred"]) > (p["pred"] - p["pi_low"])


def test_house_sampling(results):
    meta = results["house"]["meta"]
    assert meta["sampled"] is True
    assert meta["n_points_shown"] <= 500 < meta["n_points_total"]
    for m in results["house"]["models"]:
        assert len(m["prediction"]["points"]) <= 500
        assert len(m["residuals"]["fitted"]) <= 500
        preds = [p["pred"] for p in m["prediction"]["points"]]
        if m["type"] == "mlr":
            assert preds == sorted(preds)
    assert results["bike"]["meta"]["sampled"] is False
