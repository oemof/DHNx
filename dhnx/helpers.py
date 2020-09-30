import addict


class Dict(addict.Dict):
    def __init__(self, *args, **kwargs):
        super().__init__(self, *args, **kwargs)

    def __repr__(self):
        overview = ['* ' + str(key) for key, value in self.items()]
        return '\n'.join(overview)


def sum_ignore_none(*items):
    not_none = [value for value in items if value is not None]

    if not_none:
        sum_ignoring_none = sum(not_none)

    else:
        sum_ignoring_none = None

    return sum_ignoring_none
