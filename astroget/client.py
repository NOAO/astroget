"""Client module for the Astro Data Archive.
This module interfaces to the Astro Archive Server to get meta-data.

see also: pip install wrap-astro-api

TODO:
  add retrieve of WCS
"""
############################################
# Python Standard Library
from warnings import warn
from urllib.parse import urlencode, urlparse
from math import cos,sqrt,radians,isclose
############################################
# External Packages
import requests
from astropy.io import fits
from astropy.nddata import Cutout2D
from astropy.utils.data import download_file
from astropy.wcs import WCS
from astropy.coordinates import SkyCoord
from astropy import units as u
############################################
# Local Packages
from astroget.Results import Found
import astroget.exceptions as ex
from astroget import __version__
import astroget.experimental as experimental

'''Methods/functions still to add:
- voimg
- (SPARCL)

ALSO:
- lists: categoricals, fields(catalog),
'''


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
_PAT   = 'https://marsnat1-pat.csdc.noirlab.edu'    # noqa: E221
_DEV   = 'http://localhost:8010'                    # noqa: E221

client_version = __version__

hducornerkeys = ['CENRA1',   'CENDEC1',
                 'COR1RA1', 'COR1DEC1',
                 'COR2RA1', 'COR2DEC1',
                 'COR3RA1', 'COR3DEC1',
                 'COR4RA1', 'COR4DEC1']
racornerkeys = ['CENRA1', 'COR1RA1','COR2RA1','COR3RA1', 'COR4RA1']

def funcToMethod(func, clas):
    setattr(clas, func.__name__, func)

# The inverse of this is: Objects Near Position
# see: https://ned.ipac.caltech.edu/forms/nearposn.html
def get_obj_ra_dec(object_name):
    from astropy.coordinates import SkyCoord
    obj_coord = SkyCoord.from_name(object_name)
    #! return {'name': object_name,
    #!         'ra':obj_coord.ra.degree,
    #!         'dec':obj_coord.dec.degree}
    return (obj_coord.ra.degree, obj_coord.dec.degree)

#! # RETURN: FITS image
#! def cutout(imageid, ra, dec, pwidth, pheight):
#!     pass

# Display FITS in ubuntu with: fv, ds9
# TODO: allow filename to be URI
def cutout(fitsfilename, hdu_idx, pos, size, outfile="cutout.fits"):
    #size = 248 # pixels in a side
    (ra, dec) = pos # of center

    image_data,header = fits.getdata(fitsfilename, ext=hdu_idx, header=True)
    wcs = WCS(header)

    # Cutout rectangle from image_data
    position = SkyCoord(ra=ra*u.deg, dec=dec*u.deg)
    try:
        print(f'image_data.shape={image_data.shape} '
              f'position={position} '
              f'size={size} '
              f'wcs={wcs}')
        cutout = Cutout2D(image_data, position, size, wcs=wcs)
        print(f'image_data.shape={image_data.shape} cutout.shape={cutout.data.shape}')
    except Exception as err:
        print(err)
        return None

    # Save cutout with WCS into new image
    newhdu = fits.PrimaryHDU(cutout.data)
    # Update the FITS header with the cutout WCS
    newhdu.header.update(cutout.wcs.to_header())
    newhdu.writeto(outfile, overwrite=True)
    print(f'Try: \n!ds9 {outfile}  # or use "fv"')
    return outfile


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
                 connect_timeout=3.05,    # seconds
                 read_timeout=5 * 60):  # seconds
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
        self.headers = dict() # headers[hduidx] = header as json

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

        funcToMethod(experimental.hdu_bounds, CsdcClient)
        funcToMethod(experimental.fitscheck, CsdcClient)

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
             verbose=None,
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

        # Get image ids of DECam Objects for possible cutouts from big files (> 1gb)
        >>> found = client.find(outfields=['instrument', 'proc_type', 'obs_type','url', 'filesize'], constraints={'instrument': ['decam'], 'obs_type': ['object'], 'proc_type': ['instcal'], 'filesize': [1e9,1e10]}, sort="md5sum")
        _validate_fields: NOT IMPLEMENTED
        >>> found.records[:2]
        [{'obs_type': 'object', 'instrument': 'decam', 'filesize': 1776594240, 'proc_type': 'instcal', 'md5sum': '1431f0096dd79c70ea1d5ac78282d508', 'url': 'https://astroarchive.noirlab.edu/api/retrieve/1431f0096dd79c70ea1d5ac78282d508/'}, {'obs_type': 'object', 'instrument': 'decam', 'filesize': 2044751040, 'proc_type': 'instcal', 'md5sum': '52e3680b53768f12820ea1f873bd92db', 'url': 'https://astroarchive.noirlab.edu/api/retrieve/52e3680b53768f12820ea1f873bd92db/'}]

        """
        verbose = self.verbose if verbose is None else verbose
        # Let "outfields" default to ['id']; but fld may have been renamed
        if outfields is None:
            outfields = ['md5sum'] # id
        if len(constraints) > 0:
            self._validate_fields(constraints.keys())
        used = set(outfields + list(constraints.keys()))
        rectype='hdu' if any([s.startswith('hdu:') for s in used]) else 'file'

        uparams = dict(limit=limit, rectype=rectype)
        if sort is not None:
            uparams['sort'] = sort
        qstr = urlencode(uparams)
        url = f'{self.apiurl}/adv_search/find/?{qstr}'
        if verbose:
            print(f'ads/find url={url}')

        search = [[k] + v for k, v in constraints.items()]
        sspec = dict(outfields=outfields, search=search)
        res = requests.post(url, json=sspec, timeout=self.timeout)
        if res.status_code != 200:
            if verbose and ('traceback' in res.json()):
                print(f'DBG: Server traceback=\n{res.json()["traceback"]}')
            raise ex.genAstrogetException(res, verbose=self.verbose)

        return Found(res.json(), client=self)
        # END find()

    # /api/sia/vohdu?POS=194.1820667,21.6826583&SIZE=0.4
    #    &instrument=decam&obs_type=object&proc_type=instcal
    #    &FORMAT=ALL&VERB=3&limit=9
    # found = client.vohdu((194.1820667, 21.6826583), 0.3, instrument='decam',obs_type='object',proc_type='instcal',VERB=3, limit=None)
    def vohdu(self, pos, size,
              instrument=None,
              obs_type=None,
              proc_type=None,
              FORMAT='ALL',
              VERB=0,
              verbose=None,
              limit=None):
        """NEED DOCSTRING for 'client.py:vohdu()' !!!"""
        verbose = self.verbose if verbose is None else verbose
        uparams = dict(limit=limit,
                       format='json',
                       POS=','.join([str(c) for c in pos]),
                       SIZE=size)
        if instrument is not None:
            uparams['instrument'] = instrument
        if obs_type is not None:
            uparams['obs_type'] = obs_type
        if proc_type is not None:
            uparams['proc_type'] = proc_type
        if VERB is not None:
            uparams['VERB'] = VERB
        if FORMAT is not None:
            uparams['FORMAT'] = FORMAT
        qstr = urlencode(uparams)
        url = f'{self.apiurl}/sia/vohdu?{qstr}'
        if verbose:
            print(f'url={url}')
        res = requests.get(url, timeout=self.timeout)

        if res.status_code != 200:
            if verbose:
                print(f'DBG: Web-service error={res.content}')
            raise Exception(f'res={res} verbose={self.verbose}')

        found = Found(res.json(), client=self)
        for rec in found.records:
            #!print(f'rec={rec}')
            if 'url' in rec:
                newq = f"hdus=0,{rec['hdu_idx'] + 1}" # Hack for bug NAT-701!!!
                rec['url'] = urlparse(rec['url'])._replace(query=newq).geturl()
                if verbose:
                    print(f'Hack to get around bug NAT-701!!! Use {newq}')
        return found

        # END vohdu()

    def getimage(self, file_id, hdus=None, outfile=None, verbose=None):
        """Download one FITS file from the Astro Data Archive.
NEED DOCSTRING for 'client.py:getimage()' !!!"""
        verbose = self.verbose if verbose is None else verbose
        uparams = dict(limit=limit,
                       format='json',
                       )
        qstr = urlencode(uparams)
        url = f'{self.apiurl}/retrieve/{file_id}?{qstr}'
        if verbose:
            print(f'url={url}')
        res = requests.get(url, timeout=self.timeout)

        if res.status_code != 200:
            if verbose:
                print(f'DBG: Web-service error={res.content}')
            raise Exception(f'res={res} verbose={verbose}')

        if outfile is None:
            hdustr = 'x' if hdus is None else '_'.join(hdus)
            outfile = f'ADA_{md5}_{hudstr}.fits' # Astro Data Archive
        with open(outfile, 'wb') as fd:
            for chunk in res.iter_content(chunk_size=128):
                fd.write(chunk)
        return outfile


    # curl -X GET "http://localhost:8010/api/cutout/b61e72a2151eb69b73248e8e146ef596?hduidx=35&ra=194.1820667&dec=21.6826583&size=40" > ~/subimage.fits
    # Get FITS containing subimage from one HDU
    def cutout(self, ra, dec, size, md5, hduidx,
               outfile=None, verbose=None):
        verbose = self.verbose if verbose is None else verbose
        # validate_params() @@@ !!!
        #! uparams = dict(ra=ra, dec=dec, size=size, hduidx=hduidx)
        # Following is hack/workaround for NAT-701
        uparams = dict(ra=ra, dec=dec, size=size, hduidx=hduidx+1)
        qstr = urlencode(uparams)
        url = f'{self.apiurl}/cutout/{md5}?{qstr}'
        if verbose:
            print(f'cutout url={url}')
        res = requests.get(url, timeout=self.timeout)

        if res.status_code != 200:
            if verbose:
                print(f'DBG: client.cutout({(ra,dec,size,md5,hduidx)});'
                      f'  Web-service error={res.json()}')
            raise Exception(f'res={res} verbose={verbose}; {res.json()}')
        #return res
        if outfile is None:
            outfile = f'subimage_{md5}_{int(ra)}_{int(dec)}.fits'
        with open(outfile, 'wb') as fd:
            for chunk in res.iter_content(chunk_size=128):
                fd.write(chunk)
        return outfile

    def fits_header(self, md5, verbose=None):
        """Return FITS header as list of dictionaries.
        (One dictionary per HDU.)"""
        verbose = self.verbose if verbose is None else verbose
        # validate_params() @@@ !!!
        uparams = dict(format='json')
        qstr = urlencode(uparams)
        url = f'{self.apiurl}/header/{md5}?{qstr}'
        if verbose:
            print(f'api/header url={url}')
        res = requests.get(url, timeout=self.timeout)
        self.headers[md5] = res.json()
        return res.json()


###
##############################################################################
##############################################################################

if __name__ == "__main__":
    import doctest
    doctest.testmod()
