import pytest

from pipeline.config import PipelineError, load_configs

BASE = """datasets:
  - id: x
    name: X
    kaggle_url: {url}
    license: {lic}
    file: x.csv
    target: y
    split: random
"""


def test_real_config_has_license_and_links(configs):
    for c in configs.values():
        assert c.kaggle_url.startswith("https://www.kaggle.com/")
        assert c.license.strip() and "TODO" not in c.license


@pytest.mark.parametrize("url,lic,missing", [("''", "CC0", "kaggle_url"), ("https://k", "''", "license")])
def test_missing_required_field_fails(tmp_path, url, lic, missing):
    p = tmp_path / "datasets.yaml"
    p.write_text(BASE.format(url=url, lic=lic), encoding="utf-8")
    with pytest.raises(PipelineError, match=missing):
        load_configs(p)


def test_main_returns_nonzero_on_config_error(monkeypatch):
    import run_pipeline

    def boom():
        raise PipelineError("缺少欄位：license")

    monkeypatch.setattr(run_pipeline, "load_configs", boom)
    assert run_pipeline.main(["--no-figures"]) == 1
