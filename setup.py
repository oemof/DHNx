#!/usr/bin/env python

from setuptools import setup
import os


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    name='dhnx',
    version='0.0.1',
    description='Simulation and optimization of district heating and cooling networks',
    author="oemof developer group",
    author_email='jann.launer@rl-institut.de, johannes-roeder@uni-bremen.de',
    long_description=read('README.rst'),
    packages=['dhnx'],
    install_requires=[
        'pandas >= 0.18.0',
        'matplotlib',
        'networkx',
        'pillow',
        'folium',
        'addict',
        'oemof.solph >= 0.4.0',
        'scipy >= 1.5',
    ],
    extras_require={
        'cartopy': ['cartopy'],
        'geopandas': ['geopandas'],
        'osmnx': ['osmnx'],
    }
)
