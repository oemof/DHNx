# Repository Coverage

[Full report](https://htmlpreview.github.io/?https://github.com/oemof/DHNx/blob/python-coverage-comment-action-data/htmlcov/index.html)

| Name                                          |    Stmts |     Miss |   Branch |   BrPart |      Cover |   Missing |
|---------------------------------------------- | -------: | -------: | -------: | -------: | ---------: | --------: |
| src/dhnx/\_\_init\_\_.py                      |       15 |        0 |        0 |        0 |    100.00% |           |
| src/dhnx/dhn\_from\_osm.py                    |       30 |       23 |        2 |        0 |     21.88% |17-18, 26-27, 57-95 |
| src/dhnx/gistools/\_\_init\_\_.py             |        0 |        0 |        0 |        0 |    100.00% |           |
| src/dhnx/gistools/connect\_points.py          |      194 |      160 |       54 |        0 |     13.71% |19-20, 28-29, 54-63, 177-300, 316-320, 342-350, 397-515, 520-535, 610-729 |
| src/dhnx/gistools/geometry\_operations.py     |      235 |      100 |       86 |        2 |     60.75% |20-21, 33-34, 62-92, 110-170, 193-230, 236-239, 338-352, 373, 406-450, 569-\>571, 628-637 |
| src/dhnx/graph.py                             |       31 |       12 |       10 |        1 |     53.66% |33, 86, 106-123 |
| src/dhnx/helpers.py                           |       13 |        7 |        2 |        0 |     40.00% |9-10, 14-22 |
| src/dhnx/input\_output.py                     |      220 |      125 |       64 |        4 |     39.79% |26-27, 32-33, 38-39, 57, 66-68, 71, 85, 103, 109, 162, 179-181, 184, 188-196, 199-211, 222-226, 230-238, 242-254, 259-260, 265-269, 297-353, 358-364, 369-419, 423-426, 430-442, 446-454, 541-546 |
| src/dhnx/model.py                             |       28 |       12 |        0 |        0 |     57.14% |24, 27, 30, 33, 36, 45-47, 51, 61-62, 66 |
| src/dhnx/network.py                           |      118 |       20 |       36 |        2 |     81.82% |95, 102-114, 127-129, 140-145, 249, 314-318, 346, 349, 353-357 |
| src/dhnx/optimization/\_\_init\_\_.py         |        5 |        0 |        0 |        0 |    100.00% |           |
| src/dhnx/optimization/add\_components.py      |       97 |       87 |       42 |        0 |      7.19% |55-109, 141-210, 235-258, 283-354, 380-425, 455-499, 529-566 |
| src/dhnx/optimization/dhs\_nodes.py           |      110 |      105 |       40 |        0 |      3.33% |55-253, 300-331 |
| src/dhnx/optimization/oemof\_heatpipe.py      |      179 |      152 |       34 |        0 |     12.68% |32, 78-134, 142-144, 148-149, 154-159, 162-164, 206, 217-294, 339, 350-532 |
| src/dhnx/optimization/optimization\_models.py |      269 |      199 |      108 |        5 |     24.14% |36-37, 40, 43, 46, 114, 148-149, 202-242, 298-349, 362-387, 404-448, 463-469, 474-500, 505-769, 788-794, 865, 870-\>873, 895, 915-937 |
| src/dhnx/optimization/precalc\_hydraulic.py   |      113 |        4 |       24 |        3 |     94.89% |31-32, 494-\>533, 620-\>668, 657-658 |
| src/dhnx/plotting.py                          |      119 |       92 |       24 |        0 |     18.88% |32-34, 43-50, 54-62, 65-75, 89-98, 117-153, 157-218, 235-245, 248-254, 274-339 |
| **TOTAL**                                     | **1776** | **1098** |  **526** |   **17** | **36.01%** |           |


## Setup coverage badge

Below are examples of the badges you can use in your main branch `README` file.

### Direct image

[![Coverage badge](https://raw.githubusercontent.com/oemof/DHNx/python-coverage-comment-action-data/badge.svg)](https://htmlpreview.github.io/?https://github.com/oemof/DHNx/blob/python-coverage-comment-action-data/htmlcov/index.html)

This is the one to use if your repository is private or if you don't want to customize anything.

### [Shields.io](https://shields.io) Json Endpoint

[![Coverage badge](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/oemof/DHNx/python-coverage-comment-action-data/endpoint.json)](https://htmlpreview.github.io/?https://github.com/oemof/DHNx/blob/python-coverage-comment-action-data/htmlcov/index.html)

Using this one will allow you to [customize](https://shields.io/endpoint) the look of your badge.
It won't work with private repositories. It won't be refreshed more than once per five minutes.

### [Shields.io](https://shields.io) Dynamic Badge

[![Coverage badge](https://img.shields.io/badge/dynamic/json?color=brightgreen&label=coverage&query=%24.message&url=https%3A%2F%2Fraw.githubusercontent.com%2Foemof%2FDHNx%2Fpython-coverage-comment-action-data%2Fendpoint.json)](https://htmlpreview.github.io/?https://github.com/oemof/DHNx/blob/python-coverage-comment-action-data/htmlcov/index.html)

This one will always be the same color. It won't work for private repos. I'm not even sure why we included it.

## What is that?

This branch is part of the
[python-coverage-comment-action](https://github.com/marketplace/actions/python-coverage-comment)
GitHub Action. All the files in this branch are automatically generated and may be
overwritten at any moment.