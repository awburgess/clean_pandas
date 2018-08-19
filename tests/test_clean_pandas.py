from pathlib import Path

import pytest
import pandas as pd

from clean_pandas import CleanPandas


@pytest.fixture
def test_data() -> pd.DataFrame:
    """
    Fixture that returns a test dataframe from dummy data

    Returns:
        Pandas DataFrame with dummy data for testing
    """
    data = Path(__file__).parent / 'resources/test_data.csv'
    return pd.read_csv(data, dtype=str, parse_dates=True)
