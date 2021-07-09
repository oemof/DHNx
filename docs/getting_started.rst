.. _getting_started_label:

~~~~~~~~~~~~~~~
Getting started
~~~~~~~~~~~~~~~

DHNx is a toolbox for optimization and simulation of district heating and cooling systems.

.. contents:: `Contents`
    :depth: 1
    :local:
    :backlinks: top

Using DHNx
================

Installation
------------

If you have a working Python3 environment, use pypi to install the latest oemof version:

::

    pip install dhnx


For Installing the latest (dev) version, clone DHNx from github:

::

    git clone https://github.com/oemof/DHNx.git


Now you can install it your local version of DHNx using pip:

::

    pip install -e <path/to/DHNx/root/dir>

.. note::
    DHNx uses geopandas and osmnx as extra requirements for some functions related
    to the processing of spatial data. On Windows machines, you might
    encounter troubles installing geopandas via ``pip install geopandas``.
    Try to install geopandas in an EMTPY environment with
    ``conda install geopandas``, first. And second, install osmnx with
    ``pip install osmnx`` (tested with Python 3.8).
    Also check `geopandas.org <https://geopandas.org/getting_started/install.html>`_.


Examples
--------

Examples are provided `here <https://github.com/oemof/DHNx/tree/dev/examples>`_. Also,
have a look at the :ref:`examples_label` section for some more explanation.


Contributing to DHNx
==========================

Contributions are welcome. You can write issues to announce bugs or errors or to propose
enhancements. Or you can contribute a new approach that helps to model district heating/cooling
systems. If you want to contribute, fork the project at github, develop your features
on a new branch and finally open a pull request to merge your contribution to DHNx.

As DHNx is part of the oemof developer group we use the same developer rules.
You will find more information
`here <https://oemof.readthedocs.io/en/latest/contributing.html>`_.
