# Tests for "astroget" (client for Astro Data Archive)
#
# See also: ~/sandbox/sparclclient/tests/tests_api.py
#
# Unit tests for the NOIRLab Astro Data Archive client
# EXAMPLES: (do after activating venv, in sandbox/astroget/)
#   python -m unittest tests.tests
#
#  ### Run Against DEV Server.
#  serverurl=http://localhost:8060 python -m unittest tests.tests
#  showact=1 serverurl=http://localhost:8050 python -m unittest tests.tests
#
# python -m unittest  -v tests.tests    # VERBOSE
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
else:
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

    print(f"Arranging to run doctests against: astroget.client")
    tests.addTests(doctest.DocTestSuite(astroget.client))
    return tests

class ClientTest(unittest.TestCase):
    """Test access to each endpoint of the Server API"""

    maxDiff = None  # too see full values in DIFF on assert failure
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
        found = self.client.find()
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
        found = self.client.find()
        actual = found.records[:2]

        if showact:
            print(f"find_0: actual={actual}")

        self.assertEqual(actual, exp.find_0, msg="Actual to Expected")


    def test_cutout_0(self):
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
