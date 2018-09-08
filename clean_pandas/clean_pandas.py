from typing import Dict, Union, Any, List, NoReturn
import webbrowser
import warnings

import pandas as pd
import numpy

from cryptography.fernet import Fernet
from faker import Faker
from faker.providers import BaseProvider
import scrubadub


class UnknownCleanType(Exception):
    """Custom Exception for unknown clean type"""
    pass


@pd.api.extensions.register_dataframe_accessor('clean_pandas')
class CleanPandas:
    def __init__(self, pandas_object: Union[pd.DataFrame, pd.Series]):
        self._pd_obj = pandas_object
        self._key = Fernet.generate_key()
        self._fernet = Fernet(self._key)
        self._faker = Faker()
        self._dataframe_dtypes: dict = self._pd_obj.dtypes.to_dict()

    @staticmethod
    def get_faker_types() -> NoReturn:  # pragma: no cover
        """
        Opens the web page for Faker Providers

        Returns:
            None
        """
        webbrowser.open('https://faker.readthedocs.io/en/latest/providers.html')

    def _encrypt_value(self, value: Any) -> bytes:
        """
        Take an input value, convert to bytes, and encrypt as bytes

        Args:
            value: Incoming value from Pandas Series

        Returns:
            An encrypted bytes object
        """
        return self._fernet.encrypt(str(value).encode())

    def _decrypt_value(self, value: Any, series_name: str, dtype: Any = None) -> Any:
        """
        Take an encrypted value and return the original value

        Args:
            value: Incoming, encrypted value from Pandas Series
            series_name: The name of the series being decrypted
            dtype: User specified dtype object,
                   only use if you do not want to use the original dtype value on the dataframe

        Returns:
            A decrypted value that is cast to it's series original data
        """
        if not isinstance(value, bytes):
            raise ValueError("Expected bytes, encountered %s" % type(value))
        decrypted_value = self._fernet.decrypt(value).decode('utf-8')
        if not dtype:
            return self._dataframe_dtypes[series_name].type(decrypted_value)
        return dtype.type(decrypted_value)

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
        Truncates a given value given a truncation length
        and direction from which to truncate

        Args:
            value: Incoming value from Pandas Series
            dtype: Numpy object type
            trunc_length: Length of characters to truncate
            trunc_from_end: Boolean indicating whether to truncate from
            end of value or start

        Returns:
            A truncated value
        """
        string_value = str(value)
        trunc_index = len(string_value) - trunc_length
        if abs(trunc_index) > len(string_value):
            warnings.warn('Truncation exceeds character length, '
                          'will return None')
        truncate_value = string_value[:trunc_index] if trunc_from_end \
            else string_value[-trunc_index:]

        if dtype in [numpy.datetime64, numpy.object, numpy.object_]:
            return truncate_value
        else:
            try:
                return dtype(truncate_value)
            except ValueError:  # Value is truncated beyond length
                return None

    def _scrubabdub(self, value: Any) -> str:
        """
        Take a given value, cast to string, and apply the Scrubadub
        clean method. Returns original value if cast to string
        raises a ValueError

        Args:
            value: Incoming value from Pandas Series

        Returns:
            String from Scrubadub clean method
        """
        try:
            str_value = str(value)
        except ValueError:
            return value
        return scrubadub.clean(str_value)

    def _create_unique_value_dict(self, column_name: str,
                                  clean_type: str,
                                  faker_type: str,
                                  trunc_length: int = 0,
                                  trunc_from_end=True) -> Dict[Any, Any]:
        """
        Take the unique values in a series and perform the desired cleaning
        operations

        Args:
            clean_type: String indicating 'encrypt', 'replace', 'truncate',
                        'scrubadub'
            faker_type: String indicating faker provider to use
            trunc_length: Used if clean_type is 'truncate', indicates how many
                          characters to remove
            trunc_from_end: Truncate from the end, will truncate from the start
                            if False

        Returns:
            Dictionary with unique values as keys and replacement values as
            dictionary values
        """
        replacement_xwalk_dict = {}

        for value in self._pd_obj[column_name].unique():
            if clean_type == 'encrypt':
                new_value = self._encrypt_value(value)
            elif clean_type == 'faker':
                new_value = self._fake_value(faker_type)
            elif clean_type == 'truncate':
                new_value = self._truncate_value(
                    value,
                    self._pd_obj[column_name].dtype.type,
                    trunc_length, trunc_from_end)
            elif clean_type == 'scrubadub':
                new_value = self._scrubabdub(value)
            else:
                raise UnknownCleanType("Clean type must be 'encrypt', "
                                       "'scrubadub', 'faker', or 'truncate'. Given %s" % clean_type)

            replacement_xwalk_dict[value] = new_value

        return replacement_xwalk_dict

    def serialize_encryption_key(self,
                                 outpath: str) -> NoReturn:  # pragma: no cover
        """
        Serialize the encryption key used by this accessor instance

        Args:
            outpath: String representation of path for serialization

        Returns:
            None
        """
        with open(outpath, 'wb') as outfile:
            outfile.write(self._key)

    def decrypt_series(self, series_name: str, dtype: Any = None) -> pd.Series:
        """
        Decrypt a series that has been encrypted

        Args:
            series_name: Name of series

        Keyword Args:
            dtype: Pandas dtype object that will be used to cast the decrypted string, will use original dtype
                   of series

        Returns:
            Pandas series
        """
        return self._pd_obj[series_name].apply(lambda x: self._decrypt_value(x, series_name, dtype))

    def add_faker_provider(self, provider_object: BaseProvider) -> NoReturn:
        """
        Add a faker provider object for use in Clean Pandas accessor

        Args:
            provider_object: Provider object as detailed on
            Faker (https://faker.readthedocs.io/en/latest/#how-to-create-a-provider)

        Returns:
            None
        """
        self._faker.add_provider(provider_object)  # pragma: no cover

    def clean_series(self, series_name: str, clean_type: str = 'encrypt',
                     faker_type: Union[str, None] = None,
                     trunc_length: int=0,
                     trunc_from_end: bool = True) -> pd.Series:
        """
        Takes the unique values in a given series, applies the clean_type
        and replaces all values in the
        given series with the new "clean" values

        Args:
            series_name: Pandas series name
            clean_type: 'encrypt', scrubadub', 'faker', 'truncate' are options
            faker_type: Faker provider type to use
            trunc_length: Length of characters to truncate
            trunc_from_end: Boolean that indicates if truncation should start
                            from the end, defaults to True

        Returns:
            Returns new Series with updated values
        """
        value_dict = self._create_unique_value_dict(series_name, clean_type,
                                                    faker_type, trunc_length,
                                                    trunc_from_end)
        new_series = self._pd_obj[series_name].replace(value_dict)
        return new_series

    def clean_dataframe(self,
                        list_of_clean_series_dicts: List[
                            Dict[str,
                                 Union[str, int, bool, None]]
                        ]) -> pd.DataFrame:
        """
        Convenience method that, given a list of dictionaries representing the
        parameters for clean series,
        this method will call clean_series with the given parameters

        Args:
            list_of_clean_series_dicts: List of dictionaries with the params
            that can be unpacked into clean_series

        Returns:
            Pandas DataFrame with the cleaned series values
        """
        clean_pd_obj = self._pd_obj.copy()

        for params_dict in list_of_clean_series_dicts:
            try:
                clean_pd_obj[
                    params_dict['series_name']
                ] = self.clean_series(**params_dict)
            except (KeyError, UnknownCleanType):  # pragma: no cover
                continue

        return clean_pd_obj
