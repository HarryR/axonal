#!/usr/bin/env python

import sys

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

requirements = [
    'aiohttp',
]

if sys.version_info[:2] < (3, 4):
    requirements.append('asyncio')

test_requirements = [
    'pytest'
]

setup(
    name='axonal',
    version='0.0.1',
    description="",
    long_description=readme + '\n\n' + history,
    author="Harry Roberts",
    author_email='axonal@midnight-labs.org',
    url='https://github.com/harryr/axonal',
    packages=[
        'axonal',
    ],
    package_dir={
        'axonal': 'axonal',
    },
    include_package_data=True,
    install_requires=requirements,
    license="BSD",
    zip_safe=False,
    keywords='axonal',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
    test_suite='tests',
    tests_require=test_requirements
)
