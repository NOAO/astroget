# Tests for "astroget" (client for Astro Data Archive)
#
# See also: ~/sandbox/sparclclient/tests/tests_api.py
#
# Unit tests for the NOIRLab Astro Data Archive client
#
# EXAMPLES: (do after activating venv, in sandbox/astroget/)
#  python -m unittest tests.tests      # against PROD
#
#  ### Run Against PAT Server.
#  serverurl=https://marsnat1-pat.csdc.noirlab.edu python -m unittest tests.tests
#
#  ### Run Against DEV Server.
#  serverurl=http://localhost:8060 python -m unittest tests.tests
#  showact=1 serverurl=http://localhost:8060 python -m unittest tests.tests
#
#  python -m unittest  -v tests.tests    # VERBOSE
#
##############################################################################
# Python library
from contextlib import contextmanager
import unittest
from unittest import skip
import datetime
from pprint import pformat as pf
from urllib.parse import urlparse
import os
import logging
import sys
import tarfile
# External Packages
import numpy
from astropy.io import fits
# Local Packages
import astroget.client
import tests.expected_pat as exp_pat
import tests.expected_dev1 as exp_dev



_DEV1 = "http://localhost:8060"
_PAT  = "https://marsnat1-pat.csdc.noirlab.edu"
_PROD = "https://astroarchive.noirlab.edu"
serverurl = os.environ.get("serverurl", _PROD)
DEV_SERVERS = [
    "http://localhost:8060",
]
if serverurl in DEV_SERVERS:
    exp = exp_dev
    DEV=True
else:
    DEV=False
    exp = exp_pat

# Show ACTUAL results
showact = False
showact = showact or os.environ.get("showact") == "1"
# Show CURL command used to call web service (API)
showcurl = False
showcurl = showcurl or os.environ.get("showcurl") == "1"
clverb = False


# Arrange to run all doctests.
# Add package paths to python files.
# The should contain testable docstrings.
def load_tests(loader, tests, ignore):
    import doctest

    print(f"DISABLED running doctests against: astroget.client")
    #! print(f"Arranging to run doctests against: astroget.client")
    #! tests.addTests(doctest.DocTestSuite(astroget.client))
    return tests

class ClientTest(unittest.TestCase):
    """Test access to each endpoint of the Server API"""

    maxDiff = None  # to see full values in DIFF on assert failure
    # assert_equal.__self__.maxDiff = None

    @classmethod
    def setUpClass(cls):
        # Client object creation compares the version from the Server
        # against the one expected by the Client. Raise error if
        # the Client is at least one major version behind.

        print(
            f"Running Client tests\n"
            f'  against Server: "{urlparse(serverurl).netloc}"\n'
            f"  comparing to: {exp.__name__}\n"
            f"  showact={showact}\n"
            f"  showcurl={showcurl}\n"
        )

        cls.client = astroget.client.CsdcClient(
            url=serverurl,
            verbose=clverb,
            show_curl=showcurl,
        )

    @classmethod
    def tearDownClass(cls):
        pass

    def test_find_0(self):
        """Find records matching metadata."""
        found = self.client.find(sort='md5sum')
        actual = found.records[:2]

        if showact:
            print(f"find_0: actual={actual}")

        self.assertEqual(actual, exp.find_0, msg="Actual to Expected")


class ExperimentalTest(unittest.TestCase):
    """Test against EXPERIMENTAL features"""

    maxDiff = None  # too see full values in DIFF on assert failure
    # assert_equal.__self__.maxDiff = None

    @classmethod
    def setUpClass(cls):
        # Client object creation compares the version from the Server
        # against the one expected by the Client. Raise error if
        # the Client is at least one major version behind.

        cls.client = astroget.client.CsdcClient(
            url=serverurl,
            verbose=clverb,
            show_curl=showcurl,
        )

        if DEV:
            cls.targets = [
                ['09a586a9d93a14a517f6d2e0e25f53da', 36, 283.763875, -30.479861],
                ['2836105d9c941692f185a7e9ee902eab', 34, 283.763875, -30.479861],
                ['2d13e23d0cf2762890edaf9a179c3a1d', 36, 283.763875, -30.479861],
                ['3c8421ce38bf2a9112e3fbbb18405c33', 34, 283.763875, -30.479861],
                ['523c69cef368eaf24a66ac4010792490', 34, 283.763875, -30.479861],
            ]
        else:
            cls.targets = [
                ['a5fb3eef401a24461e4cd4c25e773d8f', 36, 283.763875, -30.479861],
                ['a5fb3eef401a24461e4cd4c25e773d8f', 43, 283.763875, -30.479861],
                ['b5cb08bbcf5c03e036b4f08f115e5773', 34, 283.763875, -30.479861],
                ['c0b168c47b5dcc259a0da7788d213b9e', 12, 283.763875, -30.479861],
                ['c0b168c47b5dcc259a0da7788d213b9e', 18, 283.763875, -30.479861],
            ]


    @classmethod
    def tearDownClass(cls):
        pass

    def test_cutout_0(self):
        """Get single cutout."""
        ra,dec=(283.763875, -30.479861)
        md5,hduidx=('09a586a9d93a14a517f6d2e0e25f53da', 36)
        subimage = self.client.cutout(ra, dec, 400, md5, hduidx)
        expected = 'subimage_09a586a9d93a14a517f6d2e0e25f53da_283_-30.fits'
        #print(f'cutout return type={type(subimage)}, subimage={subimage}')
        self.assertEqual(subimage, expected)
        self.assertTrue(os.path.isfile(subimage))
        with fits.open(subimage) as hdul:
            # Raise exception if invalid FITS
            hdul.verify()

    # Should check content of MANIFEST.csv when some cutouts fail.
    def test_cutouts_0(self):
        """Get batch of cutouts. Not in background. ADD CHECKS"""
        tf='test-cutouts.tar'
        status = self.client.cutouts(50, self.targets, tarfile=tf)
        assert 'From RunId=' in status
        #!print(f"cutouts_0: status={status}")
        with tarfile.open(tf) as tar:
            actual = tar.getnames()

        if showact:
            print(f"cutouts_0: actual={actual}")

        expected = ['MANIFEST.csv',
                    'cutout_0.fits',
                    'cutout_1.fits',
                    'cutout_2.fits',
                    'cutout_3.fits',
                    'cutout_4.fits',
                    ]
        #expected = ['MANIFEST.csv', 'cutout_0.fits', 'cutout_2.fits']
        self.assertEqual(actual, expected)

    # @skip('Not implemented.  Need full seperate thread?')
    def test_cutouts_1(self):
        """Get batch of cutouts with. In background (async with runid)"""
        status = self.client.cutouts(50, self.targets, background=True)

        actual = status
        expected = 'foobar'
        if showact:
            print(f"cutouts_0: actual={actual}")
        self.assertEqual(actual, expected)
