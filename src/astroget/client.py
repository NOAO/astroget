"""Client module for NATICA.
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
from nat.Results import Found
from nat import __version__

MAX_CONNECT_TIMEOUT = 3.1    # seconds
MAX_READ_TIMEOUT = 90 * 60   # seconds

_pat_hosts = ['marsnat1-pat.csdc.noirlab.edu',
              ]

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
# cd ~/sandbox/sparclclient
# sphinx-apidoc -f -o source sparcl
# make html
# firefox -new-tab "`pwd`/build/html/index.html"

# Using HTTPie (http://httpie.org):
# http :8010/nat/version

_PROD  = 'https://astroarchive.noirlab.edu'         # noqa: E221
_STAGE = 'https://marsnat1-stage.csdc.noirlab.edu'  # noqa: E221
_PAT   = 'https://marsnat1-pat.csdc.noirlab.edu'    # noqa: E221
_DEV   = 'http://localhost:8010'                    # noqa: E221

client_version = __version__

###########################
# ## The Client class

class NatClient():
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
        >>> client = nat.client.NatClient()

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
            if urlparse(url).hostname in _pat_hosts:
                msg += 'Did you enable VPN?'
            raise ex.ServerConnectionError(msg) from None  # disable chaining

        self.apiversion = float(verstr)

        expected_api = NatClient.KNOWN_GOOD_API_VERSION
        if (int(self.apiversion) - int(expected_api)) >= 1:
            msg = (f'The Astro Archive Client you are running expects an older '
                   f'version of the API services. '
                   f'Please upgrade to the latest "natclient".  '
                   f'The Client you are using expected version '
                   f'{NatClient.KNOWN_GOOD_API_VERSION} but got '
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
        return(f'(natclient:{self.clientversion},'
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
    def version(self):
        """Return version of Server Rest API used by this client.
        If the Rest API changes such that the Major version increases,
        a new version of this module will likely need to be used.

        Returns:
            API version (:obj:`float`).

        Example:
            >>> client = nat.client.NatClient()
            >>> client.version()

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
            :class:`~nat.Results.Found`: Contains header and records.

        Example:
            >>> client = nat.client.NatClient()
            >>> outs = ['id', 'ra', 'dec']
            >>> cons = {'spectype': ['GALAXY'], 'redshift': [0.5, 0.9]}
            >>> found = client.find(outfields=outs, constraints=cons)
            >>> found.records
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
            raise ex.genNatException(res, verbose=self.verbose)

        return Found(res.json(), client=self)

if __name__ == "__main__":
    import doctest
    doctest.testmod()
