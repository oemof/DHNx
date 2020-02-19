# -*- coding: utf-8 -*-

"""
This is a collection of helper functions that can be used within the tests.

This file is part of project DHNx (). It's copyrighted
by the contributors recorded in the version control history of the file,
available from its original location.

SPDX-License-Identifier: MIT
"""

import os
import pandas as pd


def get_basic_path():
    """Returns the basic oemof path and creates it if necessary.
    The basic path is the '.oemof' folder in the $HOME directory.
    """
    basicpath = os.path.join(os.path.expanduser('~'), '.DHNx')
    if not os.path.isdir(basicpath):
        os.mkdir(basicpath)
    return basicpath


def extend_basic_path(subfolder):
    """Returns a path based on the basic oemof path and creates it if
     necessary. The subfolder is the name of the path extension.
    """
    extended_path = os.path.join(get_basic_path(), subfolder)
    if not os.path.isdir(extended_path):
        os.mkdir(extended_path)
    return extended_path


def get_all_file_paths(dir):
    # pylint: disable=unused-variable
    file_paths = []
    for dir_path, dir_names, file_names in os.walk(dir):
        for file_name in file_names:
            file_paths.append(os.path.join(dir_path, file_name))

    return file_paths


def check_if_csv_files_equal(csv_file_a, csv_file_b):
    df1 = pd.read_csv(csv_file_a)
    df2 = pd.read_csv(csv_file_b)

    return df1.equals(df2)


def check_if_csv_dirs_equal(dir_a, dir_b):
    files_a = get_all_file_paths(dir_a)
    files_b = get_all_file_paths(dir_b)
    files_a.sort()
    files_b.sort()

    for file_a, file_b in zip(files_a, files_b):
        assert check_if_csv_files_equal(file_a, file_b)
