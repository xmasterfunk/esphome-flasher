#!/usr/bin/env python
"""esphomeflasher setup script."""
from setuptools import setup, find_packages

from esphomeflasher import const

PROJECT_NAME = 'esphomeflasher'
PROJECT_PACKAGE_NAME = 'esphomeflasher'
PROJECT_LICENSE = 'MIT'
PROJECT_AUTHOR = 'Otto Winter'
PROJECT_COPYRIGHT = '2018, Otto Winter'
PROJECT_URL = 'https://esphomelib.com/esphomeyaml/guides/esphomeflasher.html'
PROJECT_EMAIL = 'contact@otto-winter.com'

PROJECT_GITHUB_USERNAME = 'OttoWinter'
PROJECT_GITHUB_REPOSITORY = 'esphomeflasher'

PYPI_URL = 'https://pypi.python.org/pypi/{}'.format(PROJECT_PACKAGE_NAME)
GITHUB_PATH = '{}/{}'.format(PROJECT_GITHUB_USERNAME, PROJECT_GITHUB_REPOSITORY)
GITHUB_URL = 'https://github.com/{}'.format(GITHUB_PATH)

DOWNLOAD_URL = '{}/archive/{}.zip'.format(GITHUB_URL, const.__version__)

REQUIRES = [
    'esptool==2.5.1',
    'requests',
]

setup(
    name=PROJECT_PACKAGE_NAME,
    version=const.__version__,
    license=PROJECT_LICENSE,
    url=GITHUB_URL,
    download_url=DOWNLOAD_URL,
    author=PROJECT_AUTHOR,
    author_email=PROJECT_EMAIL,
    description="ESP8266/ESP32 firmware flasher for esphomelib",
    include_package_data=True,
    zip_safe=False,
    platforms='any',
    test_suite='tests',
    python_requires='>=3.5',
    install_requires=REQUIRES,
    keywords=['home', 'automation'],
    entry_points={
        'console_scripts': [
            'esphomeflasher = esphomeflasher.__main__:main'
        ]
    },
    packages=find_packages()
)
