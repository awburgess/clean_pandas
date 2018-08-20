# Clean Pandas
Pandas accessor for replacing, removing, or encrypting a DataFrame or Series that contains Personally Identifiable Information (PII) or Protected Health Information (PHI)

## Dependencies

* [Faker](https://github.com/joke2k/faker)
* [Scrubadub](https://github.com/datascopeanalytics/scrubadub)
* [cryptography](https://github.com/pyca/cryptography)

## Clean Type Options

* ```encrypt``` (default) - Utilizes the [cryptography](https://github.com/pyca/cryptography) library and uses Fernet (symmetric encryption)
  * **NOTE**: You must use the ```serialize_encryption_key``` before ending your REPL or program in order to decrypt
* ```faker``` - Utilizes the [Faker](https://github.com/joke2k/faker) library and requires user denote the Faker "fake" to use
* ```scrubadub``` - Utilizes the [Scrubadub](https://github.com/datascopeanalytics/scrubadub) library to detect and replace PII
* ```truncate``` - Truncates the data by casting to a string, if possible, and recast to original type if possible.  Returns ```None``` if truncation is longer than the value length.  Returns the string value if cannot be cast back to original type


## Basic Usage

```python
>>> from clean_pandas import CleanPandas
>>> import pandas as pd

>>> test_df = pd.DataFrame({"first_name": ["Charles", "Stephen"], "last_name": ["Darwin", "Hawking"], 'ssn': ['555-55-5555', '123-45-6789']})

>>> test_df.clean_pandas.clean_series('ssn')
0    b'gAAAAABbextrtJcQfOt37HK7pEISBokuh9ndWwGhvZpv...
1    b'gAAAAABbextrHo7qFr6DIZ0FlvVyO73HOmOYujKsv6vS...
Name: ssn, dtype: object

>>> test_df.clean_pandas.clean_series('last_name', clean_type='faker', faker_type='first_name')
0     Joshua
1    Michael
Name: last_name, dtype: object

>>> test_df.clean_pandas.clean_series('ssn', clean_type='scrubadub')
0    {{SSN}}
1    {{SSN}}
Name: ssn, dtype: object

>>> test_df.clean_pandas.clean_series('ssn', clean_type='truncate', trunc_length=7, trunc_from_end=False)
0    5555
1    6789
Name: ssn, dtype: object

```

## Batch Clean

```python
>>> cleaner_params = [{'series_name': 'last_name', 'clean_type': 'faker', 'faker_type': 'last_name'}, {'series_name': 'ssn', 'clean_type': 'scrubadub'}]

>>> test_df.clean_pandas.clean_dataframe(cleaner_params)
  first_name last_name      ssn
0    Charles   Pacheco  {{SSN}}
1    Stephen     Hogan  {{SSN}}
```

## License

MIT License

Copyright (c) 2018 Aaron Burgess

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
