from pathlib import Path
from datetime import datetime
from typing import NoReturn

import pytest
import pandas as pd
import numpy as np

from clean_pandas import CleanPandas


@pytest.fixture(autouse=True)
def test_data() -> pd.DataFrame:
    """
    Fixture that returns a test dataframe from dummy data

    Returns:
        Pandas DataFrame with dummy data for testing
    """
    data = Path(__file__).parent / 'resources/test_data.csv'
    return pd.read_csv(data, dtype={'postal': str},
                       converters={'dob': lambda x:
                       datetime.strptime(x, '%Y-%m-%d').date()})


def test_ssn_clean_series_faker() -> NoReturn:
    """
    Assert that fake SSNs replace all original

    """
    test_df = test_data()

    fake_values = test_df.clean_pandas.fake_it('ssn', faker_type='ssn').ssn.tolist()

    for value in test_df.ssn.values:
        assert value not in fake_values


def test_ssn_clean_series_encrypt() -> NoReturn:
    """
    Assert that fake SSNs are replaced by encrypted values

    """
    test_df = test_data()

    encrypted_df, key, dtype_dict = test_df.clean_pandas.encrypt(
        'ssn')

    encrypted_values = encrypted_df.ssn.values.tolist()

    assert all([isinstance(val, bytes) for val in encrypted_values])


def test_ssn_clean_series_truncate() -> NoReturn:
    """
    Assert that all SSN are truncated based on settings

    """
    test_df = test_data()

    truncated_values = test_df.clean_pandas.truncate('ssn', trunc_length=5).ssn

    assert all([len(val) != 11 for val in truncated_values])


def test_dob_clean_series_faker() -> NoReturn:
    """
    Assert that the dob series is replaced with datetime objects

    """
    test_df = test_data()

    fake_dates = test_df.clean_pandas.fake_it('dob', faker_type='date_time').dob

    assert all([isinstance(d, datetime) for d in fake_dates])


def test_dob_clean_series_truncate() -> NoReturn:
    """
    Assert that the dob series is truncated and returned as string

    """
    test_df = test_data()

    truncated_values = test_df.clean_pandas.truncate('dob', trunc_length=4, trunc_from_end=False).dob

    assert all([val.startswith('-') for val in truncated_values.tolist()])


def test_postal_clean_series_faker() -> NoReturn:
    """
    Assert that the postal series is replaced with fake data.

    """
    test_df = test_data()

    fake_values = test_df.clean_pandas.fake_it('postal', faker_type='zipcode').postal

    for value in test_df.postal.values:
        assert value not in fake_values


def test_first_name_clean_series_scrubadub() -> NoReturn:
    """
    Assert that first name values are replaced by Scrubadub place holders

    """
    test_df = test_data()

    scrubbed_first_name = test_df.clean_pandas.scrub_it(
        'first_name'
    ).first_name

    assert scrubbed_first_name.unique() == '{{NAME}}'


def test_last_name_clean_series_scrubadub() -> NoReturn:
    """
    Assert that last name values are replaced by Scrubadub place holders

    """
    test_df = test_data()

    scrubbed_last_name = test_df.clean_pandas.scrub_it(
        'last_name').last_name

    assert scrubbed_last_name.unique() == '{{NAME}}'


def test_ssn_clean_series_scrubadub() -> NoReturn:
    """
    Assert that SSN is redacted with Scrubadub placeholders

    """
    test_df = test_data()

    scrubbed_ssn = test_df.clean_pandas.scrub_it('ssn').ssn.unique()

    assert '{{SSN}}' in scrubbed_ssn
    # We have malformed SSN in the data, so Scrubadub picks
    # up some as phone numbers
    assert '{{PHONE}}' in scrubbed_ssn


def test_some_id_clean_series_truncate_too_much() -> NoReturn:
    """
    Ensure that truncating a value by more than the characters
    returns all None

    """
    test_df = test_data()

    series_test = test_df.clean_pandas.truncate('some_id', trunc_length=4).some_id

    assert series_test.dtype.type == np.object_


def test_income_clean_series_truncate() -> NoReturn:
    """
    Ensure that truncating an int or float value returns the same unless
    truncated past value length

    """
    test_df = test_data()

    income_clean_series = test_df.clean_pandas.truncate(
        'income',
        trunc_length=3).income

    assert income_clean_series.dtypes.type == np.int64


def test_decrypt_series() -> NoReturn:
    """
    Assert that a decrypted series is returned as the correct dtype

    """
    test_df = test_data()

    ssn_dtype = test_df.ssn.iloc[0]  # str
    some_id_dtype = test_df.some_id.iloc[0]  # int

    encrypt_df, key, dtype_dict = test_df.clean_pandas.encrypt(['ssn', 'some_id'])

    assert isinstance(encrypt_df.ssn.iloc[0], bytes)
    assert isinstance(encrypt_df.some_id.iloc[0], bytes)

    decrypt_df = encrypt_df.clean_pandas.decrypt(['ssn', 'some_id'], key, dtype_dict)

    assert decrypt_df.ssn.iloc[0] == ssn_dtype
    assert decrypt_df.some_id.iloc[0] == some_id_dtype


