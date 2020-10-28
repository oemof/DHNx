|badge_travis| |badge_coverage|

~~~~
DHNx
~~~~

This package provides an open toolbox for district heating and cooling network
optimization and simulation models.

.. contents::

About
=====

The aim of DHNx is to provide a toolbox for building models of
district heating/cooling systems. 

Quickstart
==========

If you have a working Python3 environment, use pypi to install the latest DHNx version:

.. code:: bash

    pip install dhnx

Install the developer version of DHNx by cloning DHNx to your computer and running

.. code:: bash

    pip install -e DHNx

in your virtualenv.

Check out the
`examples <https://github.com/oemof-heat/DHNx/tree/dev/examples>`_ to get started.

Documentation
=============

The documentation (work in progress) can be found here
`<https://dhnx.readthedocs.io/en/latest/>`_.
To build the docs locally using sphinx-build run the following in a terminal.

.. code:: bash

    sphinx-build docs <build-dir>

Contributing
============

Everybody is welcome to contribute to the development of DHNx. The `developer
guidelines of oemof <https://oemof.readthedocs.io/en/stable/developing_oemof.html>`_
are in most parts equally applicable to DHNx.

License
=======

MIT License

Copyright (c) 2020 oemof developing group

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.


.. |badge_coverage| image:: https://coveralls.io/repos/github/oemof-heat/DHNx/badge.svg?branch=dev&service=github
    :target: https://coveralls.io/github/oemof-heat/DHNx?branch=dev
    :alt: Test coverage

.. |badge_travis| image:: https://api.travis-ci.org/oemof/DHNx.svg?branch=dev
    :target: https://travis-ci.org/oemof/DHNx
    :alt: Build status
