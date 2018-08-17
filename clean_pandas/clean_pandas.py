from typing import Dict, Union, List, Any
import pandas as pd


@pd.tools.util.pd.api.extensions.register_dataframe_accessor('clean_pandas')
class CleanPandas:
    def __init__(self, pandas_object: Union[pd.DataFrame]):
        self._pd_obj = pandas_object

        def _create_unique_value_dict(column_name: str,
                                      clean_type: str ='encrypt',
                                      trunc_level: int = 0,
                                      trunc_from_end=True) -> Dict[Any, Any]:
            """
            Take the unique values in a series and perform the desired cleaning operations

            Args:
                clean_type: String indicating 'encrypt', 'replace', 'truncate'
                trunc_level: Used if clean_type is 'truncate', indicates how many characters to remove
                trunc_from_end: Truncate from the end, will truncate from the start if False

            Returns:
                Dictionary with unique values as keys and replacement values as dictionary values
            """
            replacement_xwalk_dict = {}

            for value in self._pd_obj[column_name].unique():
                ## TODO: Using replacement_xwalk_dict, make the value object the key and apply the clean_type to the same object as the dictionary value
                replacement_xwalk_dict[value] = value