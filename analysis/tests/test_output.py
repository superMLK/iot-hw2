"""以進入點實際輸出檔案：大小限制、圖檔、重現性。"""
import json

import pytest

import run_pipeline

MAX = 2 * 1024 * 1024


@pytest.fixture(scope="module")
def two_runs(tmp_path_factory):
    out = []
    for i in range(2):
        d = tmp_path_factory.mktemp(f"run{i}")
        fig = tmp_path_factory.mktemp(f"fig{i}")
        assert run_pipeline.main(["--out-dir", str(d), "--figures-dir", str(fig), *([] if i == 0 else ["--no-figures"])]) == 0
        out.append((d, fig))
    return out


def _strip(path):
    doc = json.loads(path.read_text(encoding="utf-8"))
    assert doc["meta"].pop("generated_at")
    return json.dumps(doc, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def test_json_size_and_contract(two_runs):
    d, _ = two_runs[0]
    for ds in ("bike", "house"):
        p = d / f"{ds}.json"
        assert p.stat().st_size < MAX
        doc = json.loads(p.read_text(encoding="utf-8"))
        assert set(doc) == {"meta", "crisp_dm", "data_understanding", "feature_selection", "models"}
        assert doc["meta"]["id"] == ds
        for step in doc["crisp_dm"].values():
            assert step["markdown"] and "{{" not in step["markdown"]


def test_figures_written(two_runs):
    _, fig = two_runs[0]
    names = {p.name for p in fig.iterdir()}
    for ds in ("bike", "house"):
        assert f"{ds}_correlation.png" in names
        assert f"{ds}_pred_mlr_selected.png" in names
        assert f"{ds}_residuals_mlr_selected.png" in names
        assert f"{ds}_infographic_pred.png" in names
    assert "bike_pred_ar.png" in names


def test_reproducible(two_runs):
    (a, _), (b, _) = two_runs
    for ds in ("bike", "house"):
        assert _strip(a / f"{ds}.json") == _strip(b / f"{ds}.json")
