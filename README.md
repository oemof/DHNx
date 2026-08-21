# Repository Coverage

[Full report](https://htmlpreview.github.io/?https://github.com/oemof/DHNx/blob/python-coverage-comment-action-data/htmlcov/index.html)

| Name                                          |    Stmts |     Miss |   Branch |   BrPart |      Cover |   Missing |
|---------------------------------------------- | -------: | -------: | -------: | -------: | ---------: | --------: |
| src/dhnx/\_\_init\_\_.py                      |       15 |        0 |        0 |        0 |    100.00% |           |
| src/dhnx/dhn\_from\_osm.py                    |       30 |       23 |        2 |        0 |     21.88% |17-18, 26-27, 57-95 |
| src/dhnx/gistools/\_\_init\_\_.py             |        0 |        0 |        0 |        0 |    100.00% |           |
| src/dhnx/gistools/connect\_points.py          |      197 |       35 |       56 |       12 |     78.26% |19-20, 28-29, 55-64, 236-245, 321, 344, 351, 512, 522-536, 614, 658-659, 678-679, 681-\>691, 703-\>708, 728-\>736 |
| src/dhnx/gistools/geometry\_operations.py     |      270 |       35 |      106 |        6 |     88.03% |20-21, 33-34, 134-135, 142-163, 207-219, 222, 236-239, 342, 566, 747-749 |
| src/dhnx/graph.py                             |       31 |       12 |       10 |        1 |     53.66% |33, 86, 106-123 |
| src/dhnx/helpers.py                           |       13 |        7 |        2 |        0 |     40.00% |9-10, 14-22 |
| src/dhnx/input\_output.py                     |      220 |      125 |       64 |        4 |     39.79% |26-27, 32-33, 38-39, 57, 66-68, 71, 85, 103, 109, 162, 179-181, 184, 188-196, 199-211, 222-226, 230-238, 242-254, 259-260, 265-269, 297-353, 358-364, 369-419, 423-426, 430-442, 446-454, 541-546 |
| src/dhnx/model.py                             |       28 |        8 |        0 |        0 |     71.43% |27, 30, 33, 36, 45-47, 51 |
| src/dhnx/network.py                           |      118 |       18 |       36 |        2 |     83.12% |95, 102-114, 127-129, 140-145, 249, 314-318, 346, 349 |
| src/dhnx/optimization/\_\_init\_\_.py         |        5 |        0 |        0 |        0 |    100.00% |           |
| src/dhnx/optimization/add\_components.py      |       97 |       38 |       42 |        7 |     53.24% |65, 74-75, 92-93, 143-144, 160, 174-188, 192-195, 283-354, 380-425 |
| src/dhnx/optimization/dhs\_nodes.py           |      126 |       38 |       42 |       11 |     70.83% |87-94, 99, 105-112, 117-124, 138-\>70, 151, 169-176, 201-208, 261, 336, 339 |
| src/dhnx/optimization/oemof\_heatpipe.py      |      179 |       40 |       34 |        6 |     76.53% |92-95, 102, 113, 158-159, 218, 247-253, 286-289, 351, 430, 467-470, 484-501 |
| src/dhnx/optimization/optimization\_models.py |      281 |       47 |      116 |       18 |     82.12% |36-37, 40, 43, 46, 205, 223, 234-243, 307, 318-324, 387, 394, 446-455, 485, 498-502, 524, 644, 656, 671-702, 712, 792-\>769, 853-859, 934, 988-993 |
| src/dhnx/optimization/precalc\_hydraulic.py   |      137 |        4 |       30 |        4 |     95.21% |31-32, 386-\>388, 661-\>706, 817-\>871, 860-861 |
| src/dhnx/plotting.py                          |      119 |       92 |       24 |        0 |     18.88% |32-34, 43-50, 54-62, 65-75, 89-98, 117-153, 157-218, 235-245, 248-254, 274-339 |
| **TOTAL**                                     | **1866** |  **522** |  **564** |   **71** | **70.49%** |           |


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