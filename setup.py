#!/usr/bin/env python

from setuptools import setup
import os


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(name='district_heating_simulation',
      version='0.0.1',
      description='Simulation of district heating and cooling networks',
      author='Jann Launer',
      author_email='jann.launer@rl-institut.de',
      long_description=read('README.rst'),
      packages=['district_heating_simulation'],
      install_requires=[])
