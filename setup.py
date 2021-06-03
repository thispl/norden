# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

with open('requirements.txt') as f:
	install_requires = f.read().strip().split('\n')

# get version from __version__ variable in norden/__init__.py
from norden import __version__ as version

setup(
	name='norden',
	version=version,
	description='Norden',
	author='Teampro',
	author_email='sarumathy.d@groupteampro.com',
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
