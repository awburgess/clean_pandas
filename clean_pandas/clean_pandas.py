from typing import Tuple, Union, Any, List, NoReturn
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

    def _process_columns(self, columns: Union[str, List[str]]) -> List[str]:
        """
        Given the possibility of either being a string or a list, ensure a list is always provided

        Args:
            columns: String or list of strings representing columns

        Returns:
            List of column names as strings
        """
        return [columns] if isinstance(columns, str) else columns

    def _encrypt_value(self, value: Any) -> bytes:
        """
        Take an input value, convert to bytes, and encrypt as bytes

        Args:
            value: Incoming value from Pandas Series

        Returns:
            An encrypted bytes object
        """
        return self._fernet.encrypt(str(value).encode())

    def _decrypt_value(self, value: Any, series_name: str, key: bytes, dtype: Any = None) -> Any:
        """
        Take an encrypted value and return the original value

        Args:
            value: Incoming, encrypted value from Pandas Series
            series_name: The name of the series being decrypted
            key: Bytes object representing encryption key
            dtype: User specified dtype object,
                   only use if you do not want to use the original dtype value on the dataframe

        Returns:
            A decrypted value that is cast to it's series original data
        """
        if not isinstance(value, bytes):
            raise ValueError("Expected bytes, encountered %s" % type(value))
        f = Fernet(key)
        decrypted_value = f.decrypt(value).decode('utf-8')
        if not dtype:
            return decrypted_value
        elif isinstance(dtype, dict):
            return dtype[series_name].type(decrypted_value)
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

    def encrypt(self, columns: Union[str, List[str]]) -> Tuple[pd.DataFrame, bytes, dict]:
        """
        Apply Fermet encryption to provided columns creating bytes objects

        Args:
            columns: String or list of strings representing columns to apply encryption

        Returns:
            Pandas DataFrame
        """
        processed_columns = self._process_columns(columns)
        new_df = self._pd_obj.copy()
        for column in processed_columns:
            replacement_values = {value: self._encrypt_value(value) for value in new_df[column].unique()}
            new_df[column] = new_df[column].replace(replacement_values)
        return new_df, self._key, {k: v for k, v in self._dataframe_dtypes.items() if k in columns}

    def decrypt(self, columns: Union[str, List[str]], key: bytes, dtype: Any = None) -> pd.DataFrame:
        """
        Decrypt a series that has been encrypted

        Args:
            columns: String or list of strings representing columns to apply encryption

        Keyword Args:
            dtype: Pandas dtype object or dictionary of columns and dtypes that will be used to cast the decrypted string;
                 if None then value will be returned as decrypted
            key: Bytes object representing encryption key

        Returns:
            Pandas DataFrame
        """
        processed_columns = self._process_columns(columns)
        for column in processed_columns:
            replacement_values = {value: self._decrypt_value(value, column, key, dtype) for value in self._pd_obj[column].unique()}
            self._pd_obj[column] = self._pd_obj[column].replace(replacement_values)
        return self._pd_obj

    def fake_it(self, columns: Union[str, List[str]], faker_type: str) -> pd.DataFrame:
        """
        Apply the Faker library to the provided columns by creating dummy values

        Args:
            columns: String or list of strings representing columns to apply Faker
            faker_type: The Faker provider type to apply

        Returns:
            Pandas DataFrame
        """
        processed_columns = self._process_columns(columns)
        new_df = self._pd_obj.copy()
        for column in processed_columns:
            replacement_values = {value: self._fake_value(faker_type) for value in new_df[column].unique()}
            new_df[column] = new_df[column].replace(replacement_values)
        return new_df

    def truncate(self, columns: Union[str, List[str]], trunc_length: int, trunc_from_end: bool = True) -> pd.DataFrame:
        """
        Truncate the provided columns by a certain number of characters and from the end or beginning of string

        Args:
            columns: String or list of strings representing columns to apply Faker
            trunc_length: Total characters to truncate

        Keyword Args:
            trunc_from_end: Boolean with True meaning start from end of word

        Returns:
            Pandas DataFrame
        """
        processed_columns = self._process_columns(columns)
        new_df = self._pd_obj.copy()
        for column in processed_columns:
            dtype = new_df[column].dtype.type
            replacement_values = {value: self._truncate_value(value, dtype, trunc_length, trunc_from_end) for value
                                  in new_df[column].unique()}
            new_df[column] = new_df[column].replace(replacement_values)
        return new_df

    def scrub_it(self, columns: Union[str, List[str]]) -> pd.DataFrame:
        """
        Apply the Scrubadub library against the given columns

        Args:
            columns: String or list of strings representing columns to apply Faker

        Returns:
            Pandas DataFrame
        """
        processed_columns = self._process_columns(columns)
        new_df = self._pd_obj.copy()
        for column in processed_columns:
            replacement_values = {value: self._scrubabdub(value) for value in new_df[column].unique()}
            new_df[column] = new_df[column].replace(replacement_values)
        return new_df
