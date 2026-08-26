# -*- coding: utf-8 -*-

import pytest

from dhnx.helpers import OptionalDependencyPlaceholder
from dhnx.helpers import import_optional_dependency


def test_optional_dependency_placeholder():
    original_error = "original import error"
    placeholder = OptionalDependencyPlaceholder(
        "module_name",
        "some functionality",
        original_error,
    )

    with pytest.raises(ImportError, match=original_error):
        placeholder.any_attribute


def test_optional_dependency_import_wrapper():
    non_existing_module_name = "non_existing_module"
    placeholder = import_optional_dependency(
        non_existing_module_name,
        functionality="no functionality",
    )

    with pytest.raises(ImportError, match=non_existing_module_name):
        placeholder.any_attribute
