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

    fake_values = test_df.clean_pandas.clean_series('ssn', clean_type='faker',
                                                    faker_type='ssn').tolist()

    for value in test_df.ssn.values:
        assert value not in fake_values


def test_ssn_clean_series_encrypt() -> NoReturn:
    """
    Assert that fake SSNs are replaced by encrypted values

    """
    test_df = test_data()

    encrypted_values = test_df.clean_pandas.clean_series(
        'ssn', clean_type='encrypt').tolist()

    assert all([isinstance(val, bytes) for val in encrypted_values])


def test_ssn_clean_series_truncate() -> NoReturn:
    """
    Assert that all SSN are truncated based on settings

    """
    test_df = test_data()

    truncated_values = test_df.clean_pandas.clean_series('ssn',
                                                         clean_type='truncate',
                                                         trunc_length=5)

    assert all([len(val) != 11 for val in truncated_values])


def test_dob_clean_series_faker() -> NoReturn:
    """
    Assert that the dob series is replaced with datetime objects

    """
    test_df = test_data()

    fake_dates = test_df.clean_pandas.clean_series('dob',
                                                   clean_type='faker',
                                                   faker_type='date_time')

    assert all([isinstance(d, datetime) for d in fake_dates])


def test_dob_clean_series_truncate() -> NoReturn:
    """
    Assert that the dob series is truncated and returned as string

    """
    test_df = test_data()

    truncated_values = test_df.clean_pandas.clean_series('dob',
                                                         clean_type='truncate',
                                                         trunc_length=4,
                                                         trunc_from_end=False)

    assert all([val.startswith('-') for val in truncated_values.tolist()])


def test_postal_clean_series_faker() -> NoReturn:
    """
    Assert that the postal series is replaced with fake data.

    """
    test_df = test_data()

    fake_values = test_df.clean_pandas.clean_series('postal',
                                                    clean_type='faker',
                                                    faker_type='zipcode')

    for value in test_df.postal.values:
        assert value not in fake_values


def test_first_name_clean_series_scrubadub() -> NoReturn:
    """
    Assert that first name values are replaced by Scrubadub place holders

    """
    test_df = test_data()

    scrubbed_first_name = test_df.clean_pandas.clean_series(
        'first_name', clean_type='scrubadub'
    )

    assert scrubbed_first_name.unique() == '{{NAME}}'


def test_last_name_clean_series_scrubadub() -> NoReturn:
    """
    Assert that last name values are replaced by Scrubadub place holders

    """
    test_df = test_data()

    scrubbed_last_name = test_df.clean_pandas.clean_series(
        'last_name',
        clean_type='scrubadub')

    assert scrubbed_last_name.unique() == '{{NAME}}'


def test_ssn_clean_series_scrubadub() -> NoReturn:
    """
    Assert that SSN is redacted with Scrubadub placeholders

    """
    test_df = test_data()

    scrubbed_ssn = test_df.clean_pandas.clean_series('ssn',
                                                     clean_type='scrubadub')\
        .unique()

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

    series_test = test_df.clean_pandas.clean_series('some_id',
                                                    clean_type='truncate',
                                                    trunc_length=4)

    assert series_test.dtype.type == np.object_


def test_income_clean_series_truncate() -> NoReturn:
    """
    Ensure that truncating an int or float value returns the same unless
    truncated past value length

    """
    test_df = test_data()

    income_clean_series = test_df.clean_pandas.clean_series(
        'income',
        clean_type='truncate',
        trunc_length=3)

    assert income_clean_series.dtypes.type == np.int64


def test_clean_dataframe_names_email_ssn() -> NoReturn:
    """
    Assert that, given a parameter list, the clean dataframe method
    cleans the series correctly

    """
    test_df = test_data()

    params_list_of_dicts = [
        {'series_name': 'first_name', 'clean_type': 'scrubadub'},
        {'series_name': 'last_name', 'clean_type': 'scrubadub'},
        {'series_name': 'email', 'clean_type': 'faker', 'faker_type': 'email'},
        {'series_name': 'street_address', 'clean_type': 'encrypt'},
        {'series_name': 'ssn', 'clean_type': 'truncate', 'trunc_length': 7,
         'trunc_from_end': False}
    ]

    clean_df = test_df.clean_pandas.clean_dataframe(params_list_of_dicts)

    assert clean_df.first_name.unique() == '{{NAME}}'
    assert clean_df.last_name.unique() == '{{NAME}}'
    assert (clean_df.merge(test_df, on='email', how='inner')).shape[0] == 0
    assert all([isinstance(value, bytes) for value in clean_df.street_address])
    assert all([len(value) <= 5 for value in clean_df.ssn])


def test_decrypt_series() -> NoReturn:
    """
    Assert that a decrypted series is returned as the correct dtype

    """
    test_df = test_data()

    ssn_dtype = test_df.ssn.iloc[0]  # str
    some_id_dtype = test_df.some_id.iloc[0]  # int

    test_df['ssn'] = test_df.clean_pandas.clean_series('ssn')
    test_df['some_id'] = test_df.clean_pandas.clean_series('some_id')

    assert isinstance(test_df.ssn.iloc[0], bytes)
    assert isinstance(test_df.some_id.iloc[0], bytes)

    test_df['ssn'] = test_df.clean_pandas.decrypt_series('ssn')
    test_df['some_id'] = test_df.clean_pandas.decrypt_series('some_id')

    assert test_df.ssn.iloc[0] == ssn_dtype
    assert test_df.some_id.iloc[0] == some_id_dtype


