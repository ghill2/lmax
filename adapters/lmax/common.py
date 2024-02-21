from collections import OrderedDict


class EvictingDict(OrderedDict):
    def __init__(self, max_size):
        super().__init__()
        self.max_size = max_size

    def __setitem__(self, key, value):
        if len(self) >= self.max_size:
            self.popitem(last=False)  # Remove the oldest item
        super().__setitem__(key, value)
