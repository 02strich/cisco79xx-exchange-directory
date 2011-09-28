#!/usr/bin/env python
from setuptools import setup, find_packages

setup(name='cisco79xx-exchange',
    version = '1.0',
    description = 'Cisco 79xx IP Phone directory provider for Microsoft Exchange',
    maintainer = 'Stefan Richter',
    maintainer_email = 'stefan@02strich.de',
    url = 'http://www.02strich.de/',
    packages = find_packages(),
    package_data = {'cisco79xx_exchange': ['*.wsdl', '*.xsd']},
    install_requires = ['Flask', 'suds-ews', 'python-ntlm'],
    entry_points = {
        'console_scripts': [
            'cisco79xx_exchange = cisco79xx_exchange.main:main',
        ],
    },
)