"""Containers for results from Astro Archive Server.
These include results of client.find().
"""

from collections import UserList
from astroget.utils import _AttrDict


class Results(UserList):

    def __init__(self, dict_list, client=None):
        super().__init__(dict_list)
        self.hdr = dict_list[0]
        self.recs = dict_list[1:]
        self.client = client
        self.fields = client.fields
        self.hdr['Count'] = len(self.recs)

    # https://docs.python.org/3/library/collections.html#collections.deque.clear
    def clear(self):
        """Delete the contents of this collection."""
        super().clear()
        self.hdr = {}
        self.recs = []

    @property
    def info(self):
        """Info about this collection.
        e.g. Warnings, parameters used to get the collection, etc."""
        return self.hdr

    @property
    def count(self):
        """Number of records in this collection."""
        return self.hdr['Count']
        return self.hdr['Count']

    @property
    def records(self):
        """Records in this collection. Each record is a dictionary."""
        return self.recs

    # just some columns (keys) of each records.
    # flat=True means do not output keys -- use tuple of values
    #   unless there is only one, then the record is just the naked singleton
    def reccols(self, fields=None, flat=False):
        """This an an unsupported, experimental feature.
        It may be removed without notice!"""

        if fields is None:
            return self.recs
        else:
            if flat:
                if len(fields) == 1:
                    return [r.get(fields[0]) for r in self.recs]
                else:
                    return [tuple(r[key] for key in fields if key in r)
                            for r in self.recs]
            else:
                return [{key: r[key] for key in fields if key in r}
                        for r in self.recs]

    def json(self):
        return self.data


class Found(Results):
    """Holds metadata records (and header)."""

    def __init__(self, dict_list, client=None):
        super().__init__(dict_list, client=client)

    def __repr__(self):
        return f'Find Results: {len(self.recs)} records'

    @property
    def ids(self):
        """List of unique identifiers of matched records."""

        return [d.get('md5sum') for d in self.recs]
