"""
Test suite for the WeeWX Realtime gauge-data extension.

Copyright (C) 2022 Gary Roderick                    gjroderick<at>gmail.com

A python unittest based test suite for aspects of the WeeWX Realtime
gauge-data extension. The test suite tests correct operation of:

-

Version: 0.5.6                                  Date: ?? June 2022

Revision History
    ?? June 2022        v0.5.6
        -   initial release

To run the test suite:

-   copy this file to the target machine, nominally to the $BIN/user/tests
    directory

-   run the test suite using:

    $ PYTHONPATH=$BIN python3 -m user.tests.test_rtgd [-v]
"""
# python imports
import socket
import struct
import unittest
from unittest.mock import patch

# Python 2/3 compatibility shims
import six

# WeeWX imports
import weewx
import user.rtgd

from weewx.units import ValueTuple

TEST_SUITE_NAME = "WeeWX Realtime gauge-data"
TEST_SUITE_VERSION = "0.5.6"


class UtilitiesTestCase(unittest.TestCase):
    """Unit tests for utility functions."""

    # expected results for degree_to_compass() test, format is:
    #   input: expected output
    compass_dict = {0: 'N', 1: 'N', 11.24: 'N',
                    11.25: 'NNE', 11.26: 'NNE', 22.5: 'NNE', 33.74: 'NNE',
                    33.75: 'NE', 33.76: 'NE', 45.0: 'NE', 56.24: 'NE',
                    56.25: 'ENE', 56.26: 'ENE', 67.5: 'ENE', 78.74: 'ENE',
                    78.75: 'E', 78.76: 'E', 90.0: 'E', 101.24: 'E',
                    101.25: 'ESE', 101.26: 'ESE', 112.5: 'ESE', 123.74: 'ESE',
                    123.75: 'SE', 123.76: 'SE', 135.0: 'SE', 146.24: 'SE',
                    146.25: 'SSE', 146.26: 'SSE', 157.5: 'SSE', 168.74: 'SSE',
                    168.75: 'S', 168.76: 'S', 180.0: 'S', 191.24: 'S',
                    191.25: 'SSW', 191.26: 'SSW', 202.5: 'SSW', 213.74: 'SSW',
                    213.75: 'SW', 213.76: 'SW', 225.0: 'SW', 236.24: 'SW',
                    236.25: 'WSW', 236.26: 'WSW', 247.5: 'WSW', 258.74: 'WSW',
                    258.75: 'W', 258.76: 'W', 270.0: 'W', 281.24: 'W',
                    281.25: 'WNW', 281.26: 'WNW', 292.5: 'WNW', 303.74: 'WNW',
                    303.75: 'NW', 303.76: 'NW', 315.0: 'NW', 326.24: 'NW',
                    326.25: 'NNW', 326.26: 'NNW', 337.5: 'NNW', 348.74: 'NNW',
                    348.75: 'N', 348.76: 'N', 360: 'N',
                    None: None}

    trend_kwargs = {'obs_type': 'outTemp',
                    'now_vt': ValueTuple(23.5, 'degree_C', 'group_temperature'),
                    'target_units': 'degree_C',
                    'db_manager': None,
                    'then_ts': 1653881839,
                    'grace': 0}

    def test_utilities(self):
        """Test utility functions

        Tests:
        1. degree_to_compass()
        2. calc_trend()
        3. bytes_to_hex()
        """

        # test degree_to_compass()
        for inp, outp in six.iteritems(self.compass_dict):
            self.assertEqual(user.rtgd.degree_to_compass(inp), outp)

        # test calc_trend()
        _kwargs = dict(self.trend_kwargs)
        # 'now' value is None
        _kwargs['now_vt'] = ValueTuple(None, 'degree_C', 'group_temperature')
        self.assertIsNone(user.rtgd.calc_trend(**_kwargs))


class ListsAndDictsTestCase(unittest.TestCase):
    """Test case to test list and dict consistency."""

    def setUp(self):

        # construct the default field map
        self.default_field_map = dict(user.rtgd.DEFAULT_FIELD_MAP)

    def test_dicts(self):
        """Test dicts for consistency"""

        # each field map entry must include 'source' and 'format' fields, test
        # that each entry in the default field map includes these fields
        for field, field_dict in six.iteritems(self.default_field_map):
            self.assertIn('source',
                          field_dict.keys(),
                          msg="A field from the default field map is does not"
                              "include a 'source' entry")
            self.assertIn('format',
                          field_dict.keys(),
                          msg="A field from the default field map is does not"
                              "include a 'format' entry")


def suite(test_cases):
    """Create a TestSuite object containing the tests we are to perform."""

    # get a test loader
    loader = unittest.TestLoader()
    # create an empty test suite
    suite = unittest.TestSuite()
    # iterate over the test cases we are to add
    for test_class in test_cases:
        # get the tests from the test case
        tests = loader.loadTestsFromTestCase(test_class)
        # add the tests to the test suite
        suite.addTests(tests)
    # finally return the populated test suite
    return suite


def main():
    import argparse

    # test cases that are production ready
    test_cases = (UtilitiesTestCase, ListsAndDictsTestCase)

    usage = """python -m user.tests.test_rtgd --help
           python -m user.tests.test_rtgd --version
           python -m user.tests.test_rtgd [-v|--verbose=VERBOSITY]

        Arguments:

           VERBOSITY: How much detail to include in the test result output."""
    description = 'Test the WeeWX Realtime gauge-data extension code.'
    epilog = """You must ensure the WeeWX modules are in your PYTHONPATH. For example:

    PYTHONPATH=/home/weewx/bin python -m user.tests.test_rtgd --help
    """

    parser = argparse.ArgumentParser(usage=usage,
                                     description=description,
                                     epilog=epilog,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--version', dest='version', action='store_true',
                        help='display the WeeWX Realtime gauge-data extension test suite version number')
    parser.add_argument('--verbose', dest='verbosity', type=int, metavar="VERBOSITY",
                        default=2,
                        help='How much detail to include in the test result output, 0-2')
    # parse the arguments
    args = parser.parse_args()

    # display version number
    if args.version:
        print("%s test suite version: %s" % (TEST_SUITE_NAME, TEST_SUITE_VERSION))
        exit(0)
    # run the tests
    # get a test runner with appropriate verbosity
    runner = unittest.TextTestRunner(verbosity=args.verbosity)
    # create a test suite and run the included tests
    runner.run(suite(test_cases))


if __name__ == '__main__':
    main()
