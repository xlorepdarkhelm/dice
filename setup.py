import os

from codecs import open

import hgdistver

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

pampas_core_path = os.path.join(here, 'pampas', 'core')

try:
    version = hgdistver.get_version()

except AssertionError:
    version = hgdistver.get_version(guess_next=False)

setup(
    name='xdh-dice',

    version=version.split('+')[0],

    description='A library that provides a numeric datatype that simulates polyhedral dice.',

    long_description=long_description,

    author='Cliff Hill',
    author_email='xlorep@darkhelm.org',

    url='https://github.com/xlorepdarkhelm/dice',
    download_url = 'https://github.com/xlorepdarkhelm/dice/archive/master.zip',

    license='MIT',

    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Information Technology',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3 :: Only',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],

    keywords='dice xdh',

    install_requires=[
        'xdh-config>=0.1',
    ],

    packages=find_packages(exclude=['test*']),
)
