from typing import Dict, Union, Any
from datetime import datetime

import pandas as pd
import numpy

from cryptography.fernet import Fernet
from faker import Faker


class UnknownCleanType(Exception):
    """Custom Exception for unknown clean type"""
    pass


@pd.api.extensions.register_dataframe_accessor('clean_pandas')
class CleanPandas:
    def __init__(self, pandas_object: Union[pd.DataFrame]):
        self._pd_obj = pandas_object
        self._key = Fernet.generate_key()
        self._fernet = Fernet(self._key)
        self._faker = Faker()

    def _encrypt_value(self, value: Any) -> bytes:
        """
        Take an input value, convert to bytes, and encrypt as bytes

        Args:
            value: Incoming value from Pandas Series

        Returns:
            An encrypted bytes object
        """
        return self._fernet.encrypt(str(value).encode())

    def _fake_value(self, faker_type: str) -> Any:
        """
        Replace an input value with a fake output value of a matching type

        Args:
            faker_type: Faker provider type to use

        Returns:
            Same data type as incoming but a fake value
        """
        return self._faker.__dict__[faker_type]()

    def _truncate_value(self, value: Any,
                        dtype: Any,
                        trunc_length: int,
                        trunc_from_end: bool) -> Any:
        """
        Truncates a given value given a truncation length and direction from which to truncate

        Args:
            value: Incoming value from Pandas Series
            dtype: Numpy object type
            trunc_length: Length of characters to truncate
            trunc_from_end: Boolean indicating whether to truncate from end of value or start

        Returns:
            A truncated value
        """
        trunc_index = len(value) - trunc_length
        truncate_value = str(value)[:trunc_index] if trunc_from_end else str(value)[trunc_index:]

        if dtype in [numpy.datetime64, numpy.object, numpy.object_]:
            return truncate_value
        else:
            return dtype(truncate_value)

    def _create_unique_value_dict(self, column_name: str,
                                  clean_type: str,
                                  faker_type: str,
                                  trunc_length: int = 0,
                                  trunc_from_end=True) -> Dict[Any, Any]:
        """
        Take the unique values in a series and perform the desired cleaning operations

        Args:
            clean_type: String indicating 'encrypt', 'replace', 'truncate'
            faker_type: String indicating faker provider to use
            trunc_length: Used if clean_type is 'truncate', indicates how many characters to remove
            trunc_from_end: Truncate from the end, will truncate from the start if False

        Returns:
            Dictionary with unique values as keys and replacement values as dictionary values
        """
        replacement_xwalk_dict = {}

        for value in self._pd_obj[column_name].unique():
            if clean_type == 'encrypt':
                new_value = self._encrypt_value(value)
            elif clean_type == 'faker':
                new_value = self._fake_value(faker_type)
            elif clean_type == 'truncate':
                new_value = self._truncate_value(value, self._pd_obj[column_name].dtype.type,
                                            trunc_length, trunc_from_end)
            else:
                raise UnknownCleanType("Clean type must be 'encrypt', 'faker', or 'truncate'")

            replacement_xwalk_dict[value] = new_value

        return replacement_xwalk_dict

    def clean_series(self, series_name: str, clean_type: str = 'encrypt', faker_type: Union[str, None] = None,
                     trunc_length: int=0, trunc_from_end: bool = True) -> pd.Series:
        """
        Takes the unique values in a given series, applies the clean_type and replaces all values in the
        given series with the new "clean" values

        Args:
            series_name: Pandas series name
            clean_type: 'encrypt', 'faker', 'truncate' are the options
            faker_type: Faker provider type to use
            trunc_length: Length of characters to truncate
            trunc_from_end: Boolean that indicates if truncation should start from the end, defaults to True

        Returns:
            Returns new Series with updated values
        """
        value_dict = self._create_unique_value_dict(series_name, faker_type, clean_type, trunc_length, trunc_from_end)
        new_series = self._pd_obj[series_name].replace(value_dict)
        return new_series
