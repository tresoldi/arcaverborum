from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def fixtures_dir():
    return FIXTURES_DIR


@pytest.fixture
def minimal_dataset_path():
    return FIXTURES_DIR / "minimal_dataset" / "cldf"
