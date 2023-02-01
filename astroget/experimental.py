"""\
The capabilities provided in this file are EXPERIMENTAL and UNSUPPORTED.
They may be removed without notice!
"""
############################################
# Python Standard Library
from urllib.parse import urlencode, urlparse
############################################
# External Packages
import requests

#client.hdu_bounds('013e55fa35798e0d46f02eeebb64b730',34) #prod
def hdu_bounds(self, md5, hduidx, vet=0, verbose=True):
    verbose = self.verbose if verbose is None else verbose
    # validate_params() @@@ !!!
    uparams = dict(format='json', limit=1)
    qstr = urlencode(uparams)
    url = f'{self.apiurl}/header/{md5}?{qstr}'
    if verbose:
        print(f'api/header url={url}')
    res = requests.get(url, timeout=self.timeout)
    self.headers[md5] = res.json()

    #!header = res.json()[hduidx]
    header = res.json()[hduidx+1]

    wcs = WCS(header)
    if verbose:
        print(f'wcs={wcs}')

    llpos = wcs.pixel_to_world(0,0)
    urpos = wcs.pixel_to_world(*wcs.pixel_shape)
    rawl = [llpos.ra.degree, urpos.ra.degree]
    decwl = [llpos.dec.degree, urpos.dec.degree]
    wcs_ra_extent = (min(rawl), max(rawl))
    wcs_dec_extent = (min(decwl), max(decwl))

    ra_cor_keys = ['COR4RA1','COR3RA1','COR2RA1','COR1RA1']
    dec_cor_keys = ['COR4DEC1','COR3DEC1','COR2DEC1','COR1DEC1']

    ra_corners = [header[k] for k in ra_cor_keys]
    dec_corners = [header[k] for k in dec_cor_keys]
    if verbose:
        print(f'ra_corners={ra_corners}')

    db_keys = ['hdu:ra_min','hdu:ra_max', 'hdu:dec_min','hdu:dec_max',
               'hdu:ra_center', 'hdu:dec_center']
    out = db_keys
    cons = {'md5sum': [md5], 'hdu:hdu_idx': [hduidx] }
    found = self.find(outfields=out, constraints=cons,
                      limit=1, verbose=verbose)
    r = found.records[0]
    ra_extremes = [r['hdu:ra_min'],r['hdu:ra_max']]
    dec_extremes = [r['hdu:dec_min'],r['hdu:dec_max']]
    bounds = dict(
        corners=((min(ra_corners), max(ra_corners)),
                 (min(dec_corners), max(dec_corners))),
        header_center=(header['CENRA1'],header['CENDEC1']),
        db=((min(ra_extremes),max(ra_extremes)),
            (min(dec_extremes),max(dec_extremes))),
        db_center=(r['hdu:ra_center'], r['hdu:dec_center']),
        #!wcs=(wcs_ra_extent,wcs_dec_extent)
        )
    if vet == 1:
        tol=1e-03
        ra_min_db,ra_max_db = (min(ra_extremes),max(ra_extremes))
        ra_min_co,ra_max_co = (min(ra_corners),max(ra_corners))
        if not isclose(ra_min_db, ra_min_co, abs_tol=tol):
            msg = (f'Database and Corner RA minimums do not match.'
                   f'\n  Difference = {abs(ra_min_db - ra_min_co)}')
            print(f'\nERROR: {msg}')
        if not isclose(ra_max_db, ra_max_co, abs_tol=tol):
            msg = (f'Database and Corner RA maximums do not match.'
                   f'\n  Difference = {abs(ra_max_db - ra_max_co)}')
            print(f'\nERROR: {msg}')
    return bounds

def fitscheck(self, file_id, verbose=False):
    """Verify FITS file"""
    verbose = self.verbose if verbose is None else verbose
    uparams = dict(format='json',
                   )
    qstr = urlencode(uparams)
    url = f'{self.apiurl}/check/{file_id}?{qstr}'
    if verbose:
        print(f'url={url}')
    res = requests.get(url, timeout=self.timeout)

    if res.status_code != 200:
        if verbose:
            print(f'DBG: Web-service error={res.json()}')
        raise Exception(f'res={res} verbose={verbose}')
    return res.json()

##############################################################################
##############################################################################
###  Tryin things out....

# This uses a hack to find HDUs that contain the given RA,DEC location.
# The "radius" (2 dims) is 1/2 the estimated width/height of each HDU.
# Since HDU sizes vary, this is silly (aka, wrong).
#
# Hack necessary because constraint on HDU ra,dec (each is a range)
# currently broken in ADS.
#
# Best solution: Allow search_filters.val_in_range() to
# use full list of django/postgres range operators.
# see:
# https://docs.djangoproject.com/en/4.0/ref/contrib/postgres/fields/#querying-range-fields
# In particular: Hdu.objects.filter(ra__contains=NumericRange(t_ra_min, t_ra_max)
#   t_ra_min:: Target RA Minimum. Left side of target region
# A "target" is the (ramin:ramax,decmin:decmax) area of the sky that
# reside completely in a HDU that will be source of cutout.
# NOTE: A cutout will never cross HDU boundaries (so some useful data may
#       me rejected.)
def get_M64():
    tra,tdec = (194.1820667, 21.6826583) # Target Center for RA, DEC search
    rra,rdec = (0.45, 0.16) # Radius for RA, DEC search

    out = ['archive_filename',
           'md5sum',  # cannot use "url" in HDU search (which this is)
           'hdu:hdu_idx',
           'hdu:ra_center', 'hdu:ra_min',  'hdu:ra_max',
           'hdu:dec_center','hdu:dec_min', 'hdu:dec_max']

    # ads.find() bug does not allow ra_min, etc.
    # They are synth fields from ra (range) etc.
    #! cons = {'md5sum': ['b1dbbe234ae87da3b031ff621699643b'],
    #!         'hdu:ra_min':  [-400, tra], # [inf:tra]
    #!         'hdu:ra_max':  [tra, +400], # [tra:inf]
    #!         'hdu:dec_min':  [-400, tdec], # [inf:tdec]U
    #!         'hdu:dec_max':  [tdec, +400], # [tdec:inf]
    #!         }

    cons = {'md5sum': ['b1dbbe234ae87da3b031ff621699643b'],
            'hdu:ra_center':  [tra-rra, tra+rra],
            'hdu:dec_center': [tdec-rdec, tdec+rdec]}

    client = CsdcClient(verbose=True)
    found = client.find(out, constraints=cons)
    return found


def get_cutout_metadata(pos=(194.1820667, 21.6826583), size=0.3):
    tra,tdec = pos # Target Center for RA, DEC search
    rra,rdec = (size, size) # Radius for RA, DEC search

    outfields=['md5sum', 'archive_filename',
               # 'url', # cannot use "url" in HDU search (which this is)
               'filesize',
               'instrument', 'proc_type', 'obs_type',
               'hdu:hdu_idx',
               'hdu:ra_center', 'hdu:ra_min',  'hdu:ra_max',
               'hdu:dec_center','hdu:dec_min', 'hdu:dec_max']
    # This forces join, takes a long time. Killed after 10 minutes. Why so long?
    cons = {'hdu:ra_center':  [tra-rra, tra+rra],
            'hdu:dec_center': [tdec-rdec, tdec+rdec],
            'instrument': ['decam'],
            'obs_type': ['object'],
            'proc_type': ['instcal'],
            }

    client = CsdcClient(verbose=True)
    found = client.vohdu(pos, size,
                         instrument='decam',
                         obs_type='object',
                         proc_type='instcal',
                         limit=None, VERB=3)
    return found

###
##############################################################################
##############################################################################

if __name__ == "__main__":
    import doctest
    doctest.testmod()
