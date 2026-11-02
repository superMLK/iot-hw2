import pytest

from pipeline.config import PipelineError
from pipeline.content import fmt_value, load_content, render, resolve

CTX = {"a": {"b": 0.123456, "n": 12345, "lst": ["x", "y"], "rows": [{"v": 1}]}, "flag": True}


def test_resolve_paths():
    assert resolve(CTX, "a.b") == 0.123456
    assert resolve(CTX, "a.rows.0.v") == 1


@pytest.mark.parametrize(
    "tmpl,expected",
    [
        ("R²={{a.b|.3f}}", "R²=0.123"),
        ("{{a.b|pct}}", "12.3%"),
        ("{{a.n|int}} 筆", "12,345 筆"),
        ("{{a.lst}}", "x、y"),
        ("{{ a.b }}", "0.123"),
        ("{{flag}}", "是"),
    ],
)
def test_render_formats(tmpl, expected):
    assert render(tmpl, CTX) == expected


def test_unknown_placeholder_fails():
    with pytest.raises(PipelineError, match="a.missing"):
        render("{{a.missing}}", CTX)


def test_malformed_placeholder_fails():
    with pytest.raises(PipelineError):
        render("{{ }}", CTX)


def test_bad_format_fails():
    with pytest.raises(PipelineError):
        fmt_value("abc", ".3f")


def test_missing_content_file_fails(tmp_path):
    with pytest.raises(PipelineError, match="找不到內容檔"):
        load_content("nope.yaml", tmp_path)


def test_unresolvable_placeholder_fails_pipeline(configs, raw, stub_content):
    from run_pipeline import analyse

    bad = {**stub_content, "crisp_dm": {**stub_content["crisp_dm"], "modeling": "{{model.nope.metrics.r2}}"}}
    with pytest.raises(PipelineError, match="model.nope"):
        analyse(configs["bike"], raw["bike"].copy(), bad)


def test_rendered_markdown_has_no_braces(results):
    for r in results.values():
        for step in r["crisp_dm"].values():
            assert "{{" not in step["markdown"] and "}}" not in step["markdown"]
        assert r["crisp_dm"]["evaluation"]["conclusion"]
