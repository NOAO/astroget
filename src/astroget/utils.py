# Python library
#!import os
import datetime
import time
import socket
# External packages
#   none
# LOCAL packages
#   none


# data = {
#     "a": "aval",
#     "b": {
#         "b1": {
#             "b2b": "b2bval",
#             "b2a": {
#                 "b3a": "b3aval",
#                 "b3b": "b3bval"
#             }
#         }
#     }
# }
#
# data1 = AttrDict(data)
# print(data1.b.b1.b2a.b3b)  # -> b3bval
class _AttrDict(dict):
    """ Dictionary subclass whose entries can be accessed by attributes
    (as well as normally).
    """
    def __init__(self, *args, **kwargs):
        def from_nested_dict(data):
            """ Construct nested AttrDicts from nested dictionaries. """
            if not isinstance(data, dict):
                return data
            else:
                return _AttrDict({key: from_nested_dict(data[key])
                                 for key in data})

        super(_AttrDict, self).__init__(*args, **kwargs)
        self.__dict__ = self

        for key in self.keys():
            self[key] = from_nested_dict(self[key])


def tic():
    """Start tracking elapsed time. Works in conjunction with toc().

    Args:
       None.
    Returns:
       Elapsed time.
    """
    tic.start = time.perf_counter()


def toc():
    """Return elapsed time since previous tic().

    Args:
       None.
    Returns:
       Elapsed time since previous tic().
    """
    elapsed_seconds = time.perf_counter() - tic.start
    return elapsed_seconds  # fractional

def EXAMPLE_tic_toc():
    tic()
    print('do a bunch of stuff')
    time.sleep(1)
    elapsed = toc()
    print(f'Elapsed time between tic() and toc() = {elapsed:2.1f} seconds')
    return elapsed
