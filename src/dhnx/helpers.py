import importlib
import types

import addict


class Dict(addict.Dict):
    def __init__(self, *args, **kwargs):
        super().__init__(self, *args, **kwargs)

    def __repr__(self):
        overview = ["* " + str(key) for key, value in self.items()]
        return "\n".join(overview)


def sum_ignore_none(*items):
    not_none = [value for value in items if value is not None]

    if not_none:
        sum_ignoring_none = sum(not_none)

    else:
        sum_ignoring_none = None

    return sum_ignoring_none


class OptionalDependencyPlaceholder:
    """Class to delay ImportErrors for optional dependencies"""
    def __init__(
        self,
        module_name: str,
        functionality: str,
        original_error: str,
    ):
        self._functionality = functionality
        self._module_name = module_name
        self._original_error = original_error

    def __getattr__(self, _):
        raise ImportError(
            f"Need {self._module_name} to {self._functionality},"
            + f" but {self._original_error}."
        )


def import_optional_dependency(
    name: str,
    functionality: str,
) -> types.ModuleType:
    """Import wrapper for optional dependencies.

    If possible, it will just import the module.
    Otherwise, it returns a placeholder so that the ImportError is not risen
    on import but only if the optional dependency is acutally used."""
    try:
        module = importlib.import_module(name)
    except ImportError as err:
        module = OptionalDependencyPlaceholder(
            name, functionality, original_error=err
        )
    return module
