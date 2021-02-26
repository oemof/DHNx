.. _geometry_preparation_label:

~~~~~~~~~~~~~~~~~~~~
Geometry preparation
~~~~~~~~~~~~~~~~~~~~

For setting up a *ThermalNetwork*, you need to prepare your input data somehow.
Therefore, the dhnx package provides some helpful modules and function with
the geometry processing modules, see :py:mod:`~dhnx.gistools.connect_points`,
especially the :py:func:`dhnx.gistools.connect_points.process_geometry`.

The example folder included in this repository also contains the
`import_osm_invest` example, that provides an illustrative introduction
on how to use and prepare your geometry based on open street maps data
(See ```examples/investment_optimisation/import_osm_invest```).
