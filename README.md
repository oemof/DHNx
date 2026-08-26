# Repository Coverage

[Full report](https://htmlpreview.github.io/?https://github.com/oemof/DHNx/blob/python-coverage-comment-action-data/htmlcov/index.html)

| Name                                          |    Stmts |     Miss |   Branch |   BrPart |      Cover |   Missing |
|---------------------------------------------- | -------: | -------: | -------: | -------: | ---------: | --------: |
| src/dhnx/\_\_init\_\_.py                      |       15 |        0 |        0 |        0 |    100.00% |           |
| src/dhnx/dhn\_from\_osm.py                    |       24 |       19 |        2 |        0 |     19.23% |     49-89 |
| src/dhnx/gistools/\_\_init\_\_.py             |        0 |        0 |        0 |        0 |    100.00% |           |
| src/dhnx/gistools/connect\_points.py          |      189 |       33 |       56 |       13 |     77.96% |47-56, 230-241, 317, 340, 347, 508, 518-532, 610, 616-621, 654-655, 674-675, 677-\>687, 699-\>704, 724-\>732 |
| src/dhnx/gistools/geometry\_operations.py     |      259 |       31 |      106 |        6 |     88.77% |127-128, 135-162, 206-218, 221, 235-238, 341, 565, 746-748 |
| src/dhnx/graph.py                             |       31 |       12 |       10 |        1 |     53.66% |33, 86, 106-123 |
| src/dhnx/helpers.py                           |       28 |        7 |        2 |        0 |     70.00% |12-13, 17-25 |
| src/dhnx/input\_output.py                     |      211 |      119 |       64 |        4 |     40.00% |43, 52-54, 57, 71, 89, 95, 148, 165-167, 170, 174-182, 185-197, 208-212, 216-224, 228-240, 245-246, 251-255, 283-343, 348-354, 359-409, 413-416, 420-432, 436-444, 531-536 |
| src/dhnx/model.py                             |       28 |        8 |        0 |        0 |     71.43% |27, 30, 33, 36, 45-47, 51 |
| src/dhnx/network.py                           |      118 |       18 |       36 |        2 |     83.12% |95, 102-114, 127-129, 140-145, 249, 314-318, 346, 349 |
| src/dhnx/optimization/\_\_init\_\_.py         |        5 |        0 |        0 |        0 |    100.00% |           |
| src/dhnx/optimization/add\_components.py      |       97 |       38 |       42 |        7 |     53.24% |65, 74-75, 92-93, 143-144, 160, 174-188, 192-195, 283-354, 380-425 |
| src/dhnx/optimization/dhs\_nodes.py           |      126 |       38 |       42 |       11 |     70.83% |87-94, 99, 105-112, 117-124, 138-\>70, 151, 169-176, 201-208, 261, 336, 339 |
| src/dhnx/optimization/oemof\_heatpipe.py      |      179 |       40 |       34 |        6 |     76.53% |92-95, 102, 113, 158-159, 218, 247-253, 286-289, 351, 430, 467-470, 484-501 |
| src/dhnx/optimization/optimization\_models.py |      281 |       47 |      116 |       18 |     82.12% |36-37, 40, 43, 46, 205, 223, 234-243, 307, 318-324, 387, 394, 446-455, 485, 498-502, 524, 644, 656, 671-702, 712, 792-\>769, 853-859, 934, 988-993 |
| src/dhnx/optimization/precalc\_hydraulic.py   |      135 |        2 |       30 |        4 |     96.36% |386-\>388, 660-\>705, 816-\>870, 859-860 |
| src/dhnx/plotting.py                          |      119 |       92 |       24 |        0 |     18.88% |32-34, 43-50, 54-62, 65-75, 89-98, 117-153, 157-218, 235-245, 248-254, 274-339 |
| **TOTAL**                                     | **1845** |  **504** |  **564** |   **72** | **70.94%** |           |


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