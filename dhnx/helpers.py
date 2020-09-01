import addict


class Dict(addict.Dict):
    def __init__(self, *args, **kwargs):
        super().__init__(self, *args, **kwargs)

    def __repr__(self):
        overview = ['* ' + str(key) for key, value in self.items()]
        return '\n'.join(overview)
