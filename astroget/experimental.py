"""\
The capabilities provided in this file are EXPERIMENTAL and UNSUPPORTED.
They may be removed without notice!
"""
############################################
# Python Standard Library
from urllib.parse import urlencode, urlparse
from pprint import pformat as pf
############################################
# External Packages
import requests
############################################
# Local Packages
from astroget.Results import Found
import astroget.utils as ut

# Display FITS in ubuntu with: fv, ds9
# TODO: allow filename to be URI
def _cutout(fitsfilename, hdu_idx, pos, size, outfile="cutout.fits"):
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
        print(f'image_data.shape={image_data.shape}'
              f' cutout.shape={cutout.data.shape}')
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

# ############################################################################
# ## Targets for Monkey Patch modifications to Client class
#

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

# curl -X GET "http://localhost:8010/api/cutout/b61e72a2151eb69b73248e8e146ef596?hduidx=35&ra=194.1820667&dec=21.6826583&size=40" > ~/subimage.fits
# Get FITS containing subimage from one HDU
# RETURN: name of local FITS file
def cutout(self, ra, dec, size, md5, hduidx,
           outfile=None, verbose=None):
    """Generate and get a single cutout (FITS) from the Astro Data Archive.

    This is an UNSUPPORTED and EXPERIMENTAL feature.
    It may be removed without notice!

    Args:
        ra (:obj:`float`): right ascension (decimal degrees) of center of target
    .
        dec (:obj:`float`): declination (decimal degrees) of center of target.

        size (:obj:`int`): Width and Height of desired cutout images (in pixels)

        fid (:obj:`str`): File ID of FITS image in Astro Data Archive

        hduidx (:obj:`int`): Index of HDU in FITS file of Astro Data Archive

        outfile (str): Create subimage FITS file at this relative path location.

        public_only (:obj:`bool`, optional): If True (the default),
            do not generate cutouts for any targets that reference
            Proprietary images.
            If False, generate all cutouts but only allow Authorized users
            to retrieve the tarfile.  NOTE: unauthorized users will not be
            to retrieve ANY generated cutouts (even the public ones) since
            both proprietary and public cutouts are in the same tarfile.

        verbose (:obj:`bool`, optional): Set to True for in-depth return
            statement. Defaults to None. None means use value associated
            with client (which defaults to False).

        Returns:
            :obj:`str`: name of subimage

        Example:
            >>> client = CsdcClient()
            >>> ra,dec = (283.763875, -30.479861)
            >>> client.cutout(ra, dec, 50, 09a586a9d93a14a517f6d2e0e25f53da, 36)
            subimage_09a586a9d93a14a517f6d2e0e25f53da_283_-30.fits

    """

    verbose = self.verbose if verbose is None else verbose
    # validate_params() @@@ !!!
    #! uparams = dict(ra=ra, dec=dec, size=size, hduidx=hduidx)
    # Following is hack/workaround for NAT-701
    uparams = dict(ra=ra, dec=dec, size=size, hduidx=hduidx+1)
    qstr = urlencode(uparams)
    url = f'{self.rooturl}/experimental/cutout/{md5}?{qstr}'
    if verbose:
        print(f'cutout url={url}')

    if self.show_curl:
        cmd = ut.curl_cutout_str(url)
        print(cmd)


    res = requests.get(url, timeout=self.timeout)

    if res.status_code != 200:
        if verbose:
            print(f'DBG: client.cutout({(ra,dec,size,md5,hduidx)});'
                  #f'  Web-service error={res.json()}'
                  f'  Web-service error={res.text}'
                  )
        raise Exception(f'res={res} verbose={verbose}; {res.json()}')
    #return res
    if outfile is None:
        outfile = f'subimage_{md5}_{int(ra)}_{int(dec)}.fits'
    with open(outfile, 'wb') as fd:
        for chunk in res.iter_content(chunk_size=128):
            fd.write(chunk)
    return outfile


#
# vohdu
#! ["hdu:ra_center", -400, 400]
#! ok {"outfields": ["archive_filename","md5sum", "hdu:hdu_idx", "hdu:ra_center", "hdu:dec_center"], "search": [["archive_filename", "m54", "contains"]]}
def cutouts(self, size, target_list, tarfile='cutouts.tar',
            public_only=True, background=False, verbose=None):
    """Retrieve a batch of cutout images from the Astro Data Archive.

    This is an UNSUPPORTED and EXPERIMENTAL feature.
    It may be removed without notice!

    Args:
        size (:obj:`int`): Width and Height of desired cutout images (in pixels)

        target_list (:obj:`list`): List of 'targets'. Each 'target' consists
            of a tuple containing: fileId, hduIdx, RA_center, DEC_center

        background (:obj:`bool`, optional): If False (the default),
            wait for all subimages to produced, then return a tarfile
            containing all sub-images.
            If True, return a RunId (string) that can be used to poll
            and retrieve the tarfile.
            The tarfile will only be available for 24 hours from the time
            it is generated.

        tarfile (str): Create tarfile at this relative path location.
            The tarfile will contain each cutout image as a FITS file and
            MANIFEST.org file listed the files and where they came from.
            Default: 'cutouts.tar'

        public_only (:obj:`bool`, optional): If True (the default),
            do not generate cutouts for any targets that reference
            Proprietary images.
            If False, generate all cutouts but only allow Authorized users
            to retrieve the tarfile.  NOTE: unauthorized users will not be
            to retrieve ANY generated cutouts (even the public ones) since
            both proprietary and public cutouts are in the same tarfile.

        verbose (:obj:`bool`, optional): Set to True for in-depth return
            statement. Defaults to None. None means use value associated
            with client (which defaults to False).

        Returns:
            :obj:`str`: tarfile if background=False, RUNID otherwise.

        Example:
            >>> client = CsdcClient()
            >>> ra,dec = (283.763875, -30.479861)
            >>> targets =  [['09a586a9d93a14a517f6d2e0e25f53da', 36, ra, dec], ['2836105d9c941692f185a7e9ee902eab', 34, ra, dec]]
            >>> client.cutouts(50, targets, tarfile='example-cutouts.tar')
            >>> tarfile.open('example-cutouts.tar').getnames()
            ['MANIFEST.csv', 'cutout_0.fits', 'cutout_1.fits', 'cutout_2.fits', 'cutout_3.fits', 'cutout_4.fits']

    """
    assert public_only, ('ERROR: Only public_only=True is allowed')
    verbose = self.verbose if verbose is None else verbose

    # Following is hack/workaround for NAT-701
    targets = [(fid, hduidx+1, ra, dec)
               for  (fid, hduidx, ra, dec) in target_list]

    # validate_params() @@@ !!!
    uparams = dict(size=size, background=1 if background else 0)
    qstr = urlencode(uparams)
    url = f'{self.rooturl}/experimental/cutouts/?{qstr}'
    if verbose:
        print(f'cutouts url={url}')

    if self.show_curl:
        cmd = ut.curl_cutouts_str(url, targets)
        print(cmd)

    res = requests.post(url, json=targets, timeout=self.timeout)

    #!print(f'cutouts.res.headers={res.headers} reason={res.reason}')

    if res.status_code != 200:
        print(f'cutouts res[{len(res.content)}]={res.content}')
        print(f'cutouts result.json={pf(res.json())}')
        if verbose:
            print(f'DBG: client.cutouts({size}, {target_list})\n'
                  #f'  Web-service error={res.json()}'
                  f'  Web-service error={res.text}'
                  )
        raise Exception(f'res={res} verbose={verbose}; {res.json()}')
    with open(tarfile, 'wb') as fd:
        for chunk in res.iter_content(chunk_size=128):
            fd.write(chunk)
    return res.reason


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
