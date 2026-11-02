import sys
import warnings
from pathlib import Path

import pandas as pd
import pytest

ANALYSIS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ANALYSIS))

from pipeline.config import load_configs  # noqa: E402

warnings.filterwarnings("ignore", category=FutureWarning)

STEPS = ["business_understanding", "data_understanding", "data_preparation", "modeling", "evaluation", "deployment"]


@pytest.fixture(scope="session")
def configs():
    return {c.id: c for c in load_configs()}


@pytest.fixture(scope="session")
def raw(configs):
    return {k: pd.read_csv(c.raw_path) for k, c in configs.items()}


@pytest.fixture(scope="session")
def stub_content():
    """單元測試用的最小內容（真正的內容檔在 analysis/content/）。"""
    return {
        "feature_labels": {},
        "success": {"threshold": 0.5, "value": "best.metrics.r2"},
        "conclusion": {"met": "達標 {{best.metrics.r2|.3f}}", "not_met": "未達標 {{best.metrics.r2|.3f}}"},
        "crisp_dm": {k: f"{k}：{{{{best.label}}}}" for k in STEPS},
    }


@pytest.fixture(scope="session")
def results(configs, raw, stub_content):
    from run_pipeline import analyse

    return {k: analyse(c, raw[k].copy(), stub_content) for k, c in configs.items()}
