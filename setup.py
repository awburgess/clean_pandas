from pathlib import Path
from setuptools import setup

_README = Path(__file__).parent / 'README.md'

def long_description() -> str:
    with _README.open(encoding='utf-8') as readme:
        long_descript = readme.read()
    return long_descript

setup(
    name='clean_pandas',
    version='0.1.1',
    packages=['tests', 'clean_pandas'],
    url='https://github.com/awburgess/clean_pandas',
    license='MIT License',
    author='Aaron Burgess',
    author_email='geoburge@gmail.com',
    description=' Pandas accessor for replacing, removing, or encrypting a DataFrame or Series that contains Personally Identifiable Information (PII) or Protected Health Information (PHI)',
    long_description=long_description(),
    long_description_content_type='text/markdown',
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    install_requires=[
        'Faker',
        'cryptography',
        'scrubadub',
    ]
)
