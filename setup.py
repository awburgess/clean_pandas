from setuptools import setup

setup(
    name='clean_pandas',
    version='0.1.0',
    packages=['tests', 'clean_pandas'],
    url='https://github.com/awburgess/clean_pandas',
    license='MIT License',
    author='Aaron Burgess',
    author_email='geoburge@gmail.com',
    description=' Pandas accessor for replacing, removing, or encrypting a DataFrame or Series that contains Personally Identifiable Information (PII) or Protected Health Information (PHI)',
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
