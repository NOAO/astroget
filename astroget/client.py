"""Client module for the Astro Data Archive.
This module interfaces to the Astro Archive Server to get meta-data.
"""
############################################
# Python Standard Library
from warnings import warn
from urllib.parse import urlencode, urlparse
############################################
# External Packages
import requests
############################################
# Local Packages
from astroget.Results import Found
import astroget.exceptions as ex
from astroget import __version__

MAX_CONNECT_TIMEOUT = 3.1    # seconds
MAX_READ_TIMEOUT = 90 * 60   # seconds

# Upload to PyPi:
#   python3 -m build --wheel
#   twine upload dist/*

# Use Google Style Python Docstrings so autogen of Sphinx doc works:
#  https://www.sphinx-doc.org/en/master/usage/extensions/example_google.html
#  https://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html
#
# Use sphinx-doc emacs minor mode to insert docstring skeleton.
# C-c M-d in function/method def

# ### Generate documentation:
# cd ~/sandbox/astroget
# sphinx-apidoc -f -o source astroget
# make html
# firefox -new-tab "`pwd`/build/html/index.html"

# Using HTTPie (http://httpie.org):
# http :8010/astroget/version

_PROD  = 'https://astroarchive.noirlab.edu'         # noqa: E221
_DEV   = 'http://localhost:8010'                    # noqa: E221

client_version = __version__

###########################
# ## The Client class

# Community Science and Data Center (CSDC)
class CsdcClient():
    """Provides interface to Astro Archive Server.
    When using this to report a bug, set verbose to True. Also print
    your instance of this.  The results will include important info
    about the Client and Server that is useful to Developers.

    Args:
        url (:obj:`str`, optional): Base URL of Astro Archive Server. Defaults
            to 'https://astroarchive.noirlab.edu'.

        verbose (:obj:`bool`, optional): Default verbosity is set to
            False for all client methods.

        connect_timeout (:obj:`float`, optional): Number of seconds to
            wait to establish connection with server. Defaults to
            1.1.

        read_timeout (:obj:`float`, optional): Number of seconds to
            wait for server to send a response. Generally time to
            wait for first byte. Defaults to 5400.

    Example:
        >>> client = CsdcClient()
        >>> client
        (astroget:0.1.0, api:6.0, https://astroarchive.noirlab.edu/api, verbose=False, connect_timeout=1.1, read_timeout=5400)

    Raises:
        Exception: Object creation compares the version from the
            Server against the one expected by the Client. Throws an
            error if the Client is a major version or more behind.

    """

    KNOWN_GOOD_API_VERSION = 8.0  # @@@ Change this on Server version increment

    def __init__(self, *,
                 url=_PROD,
                 verbose=False,
                 connect_timeout=1.1,    # seconds
                 read_timeout=90 * 60):  # seconds
        """Create client instance.
        """
        self.rooturl = url.rstrip("/")
        self.apiurl = f'{self.rooturl}/api'
        self.apiversion = None
        self.verbose = verbose
        self.c_timeout = min(MAX_CONNECT_TIMEOUT,
                             float(connect_timeout))  # seconds
        self.r_timeout = min(MAX_READ_TIMEOUT,  # seconds
                             float(read_timeout))

        # require response within this num seconds
        # https://2.python-requests.org/en/master/user/advanced/#timeouts
        # (connect timeout, read timeout) in seconds
        self.timeout = (self.c_timeout, self.r_timeout)
        #@@@ read timeout should be a function of the POST payload size

        if verbose:
            print(f'apiurl={self.apiurl}')

        # Get API Version
        try:
            endpoint = f'{self.apiurl}/version/'
            verstr = requests.get(endpoint, timeout=self.timeout).content
        except requests.ConnectionError as err:
            msg = f'Could not connect to {endpoint}. {str(err)}'
            raise ex.ServerConnectionError(msg) from None  # disable chaining

        self.apiversion = float(verstr)

        expected_api = CsdcClient.KNOWN_GOOD_API_VERSION
        if (int(self.apiversion) - int(expected_api)) >= 1:
            msg = (f'The Astro Archive Client you are running expects an older '
                   f'version of the API services. '
                   f'Please upgrade to the latest "astroget".  '
                   f'The Client you are using expected version '
                   f'{CsdcClient.KNOWN_GOOD_API_VERSION} but got '
                   f'{self.apiversion} from the Astro Archive Server '
                   f'at {self.apiurl}.')
            raise Exception(msg)
        self.clientversion = client_version
        #@@@  diff for each instrument,proctype !!!
        # aux+hdu
        self.fields = list()

        ###
        ####################################################
        # END __init__()

    def __repr__(self):
        return(f'(astroget:{self.clientversion},'
               f' api:{self.apiversion},'
               f' {self.apiurl},'
               f' verbose={self.verbose},'
               f' connect_timeout={self.c_timeout},'
               f' read_timeout={self.r_timeout})')

    def _validate_fields(self, fields):
        """Raise exception if any field name in FIELDS is
        not registered."""
        print('_validate_fields: NOT IMPLEMENTED')

    @property
    def expected_server_version(self):
        """Return version of Server Rest API used by this client.
        If the Rest API changes such that the Major version increases,
        a new version of this module will likely need to be used.

        Returns:
            API version (:obj:`float`).

        Example:
            >>> client = CsdcClient()
            >>> client.expected_server_version
            6.0
        """

        if self.apiversion is None:
            response = requests.get(f'{self.apiurl}/version',
                                    timeout=self.timeout,
                                    cache=True)
            self.apiversion = float(response.content)
        return self.apiversion

    def find(self, outfields=None, *,
             constraints={},  # dict(fname) = [op, param, ...]
             limit=500,
             sort=None):
        """Find records in the Astro Archive database.

        Args:
            outfields (:obj:`list`, optional): List of fields to return.
                Only CORE fields may be passed to this parameter.
                Defaults to None, which will return only the id and _dr
                fields.

            constraints (:obj:`dict`, optional): Key-Value pairs of
                constraints to place on the record selection. The Key
                part of the Key-Value pair is the field name and the
                Value part of the Key-Value pair is a list of values.
                Defaults to no constraints. This will return all records in the
                database subject to restrictions imposed by the ``limit``
                parameter.

            limit (:obj:`int`, optional): Maximum number of records to
                return. Defaults to 500.

            sort (:obj:`list`, optional): Comma separated list of fields
                to sort by. Defaults to None. (no sorting)

        Returns:
            :class:`~astroget.Results.Found`: Contains header and records.

        Examples:

        # Default find; no constraints, get md5sum field (image id)
        >>> client = CsdcClient()
        >>> found = client.find()
        >>> found
        Find Results: 500 records
        >>> found.records[:2]
        [{'md5sum': '0000004ab27d9e427bb93c640b358633'}, {'md5sum': '0000032cfbe72cc162eaec4c0a9ce6ec'}]

        # Get image ids of DECam Objects
        >>> found = client.find(outfields=['md5sum', 'instrument', 'proc_type', 'obs_type'], constraints={'instrument': ['decam'], 'obs_type': ['object'], 'proc_type': ['instcal']}, sort="md5sum"  )
        _validate_fields: NOT IMPLEMENTED
        >>> found.records[:2]
        [{'obs_type': 'object', 'proc_type': 'instcal', 'md5sum': '000007c08dc11d70622574eec3819a02', 'instrument': 'decam'}, {'obs_type': 'object', 'proc_type': 'instcal', 'md5sum': '0000081373392f93bcacc31ba0153467', 'instrument': 'decam'}]

        """
        # Let "outfields" default to ['id']; but fld may have been renamed
        if outfields is None:
            outfields = ['md5sum'] # id
        if len(constraints) > 0:
            self._validate_fields(constraints.keys())
        uparams = dict(limit=limit,)
        if sort is not None:
            uparams['sort'] = sort
        qstr = urlencode(uparams)
        url = f'{self.apiurl}/adv_search/find/?{qstr}'
        search = [[k] + v for k, v in constraints.items()]
        sspec = dict(outfields=outfields, search=search)
        res = requests.post(url, json=sspec, timeout=self.timeout)

        if res.status_code != 200:
            if self.verbose and ('traceback' in res.json()):
                print(f'DBG: Server traceback=\n{res.json()["traceback"]}')
            raise ex.genAstrogetException(res, verbose=self.verbose)

        return Found(res.json(), client=self)

if __name__ == "__main__":
    import doctest
    doctest.testmod()
