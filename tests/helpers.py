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
from pandas.testing import assert_frame_equal


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


def check_if_csv_files_equal(csv_file_a, csv_file_b, **kwargs):
    r"""
    Compares two csv files.

    Parameters
    ----------
    csv_file_a
    csv_file_b

    """
    df1 = pd.read_csv(csv_file_a)
    df2 = pd.read_csv(csv_file_b)

    assert_frame_equal(df1, df2, **kwargs)


def check_if_csv_dirs_equal(dir_a, dir_b, **kwargs):
    r"""
    Compares the csv files in two directories and asserts that
    they are equal.

    The function asserts that:

    1. The file names of csv files found in the directories are the same.
    2. The file contents are the same.

    Parameters
    ----------
    dir_a : str
        Path to first directory containing csv files

    dir_b : str
        Path to second directory containing csv files

    """
    files_a = get_all_file_paths(dir_a)
    files_b = get_all_file_paths(dir_b)

    files_a = [file for file in files_a if file.split('.')[-1] == 'csv']
    files_b = [file for file in files_b if file.split('.')[-1] == 'csv']

    files_a.sort()
    files_b.sort()

    f_names_a = [os.path.split(f)[-1] for f in files_a]
    f_names_b = [os.path.split(f)[-1] for f in files_b]

    diff = list(set(f_names_a).symmetric_difference(set(f_names_b)))

    assert not diff,\
        f"Lists of filenames are not the same." \
        f" The diff is: {diff}"

    for file_a, file_b in zip(files_a, files_b):
        try:
            check_if_csv_files_equal(file_a, file_b, **kwargs)
        except AssertionError:
            diff.append([file_a, file_b])

    if diff:
        error_message = ''
        for pair in diff:
            short_name_a, short_name_b = (os.path.join(*f.split(os.sep)[-4:]) for f in pair)
            line = ' - ' + short_name_a + ' and ' + short_name_b + '\n'
            error_message += line

        raise AssertionError(f" The contents of these file are different:\n{error_message}")
