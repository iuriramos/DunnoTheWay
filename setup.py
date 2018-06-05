# -*- coding: utf-8 -*-

# Learn more: https://github.com/kennethreitz/setup.py

from setuptools import setup, find_packages


with open('README.md') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

setup(
    name='DunnoTheWay',
    version='0.1.0',
    description='This project aims to auto-generate airways for a given Air Space where one can track the location of aircraft within it.',
    long_description=readme,
    author='Iuri Ramos',
    author_email='iuri.srb@gmail.com',
    url='https://github.com/iuriramos/DunnoTheWay',
    license=license,
    packages=find_packages(exclude=('tests', 'docs'))
)

