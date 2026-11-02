import pandas as pd
import pytest

from pipeline.config import PipelineError
from pipeline.understanding import check_feature_count, understand


def test_feature_counts(results):
    assert results["bike"]["data_understanding"]["n_features"] == 14
    assert results["house"]["data_understanding"]["n_features"] == 19


@pytest.mark.parametrize("n", [13, 40, 5])
def test_feature_count_out_of_range_fails(configs, n):
    with pytest.raises(PipelineError, match="bike"):
        check_feature_count(n, configs["bike"])


def test_understand_rejects_small_dataset(configs):
    df = pd.DataFrame({"instant": [1, 2], "a": [1, 2], "cnt": [3, 4]})
    with pytest.raises(PipelineError):
        understand(df, configs["bike"])


def test_understanding_fields(results):
    du = results["bike"]["data_understanding"]
    assert du["n_rows"] == 731 and du["n_cols"] == 16
    assert len(du["preview"]) == 10
    assert len(du["top_corr_features"]) == 5
    assert {"count", "mean", "std", "min", "q1", "median", "q3", "max"} <= set(du["describe"]["cnt"])
    assert len(du["correlation"]["labels"]) == len(du["correlation"]["matrix"])
    assert sum(du["target_distribution"]["counts"]) == 731
