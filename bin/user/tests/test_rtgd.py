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
import unittest
from unittest.mock import patch

# Python 2/3 compatibility shims
import six

# WeeWX imports
import weewx
import weewx.defaults
import user.rtgd

from weewx.units import ValueTuple

TEST_SUITE_NAME = "WeeWX Realtime gauge-data"
TEST_SUITE_VERSION = "0.6.2"


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
                    'now_vt': ValueTuple(None, 'degree_C', 'group_temperature'),
                    'target_units': 'degree_C',
                    'db_manager': None,
                    'then_ts': 1653881839,
                    'grace': 0}

    def test_utilities(self):
        """Test utility functions

        Tests:
        1. degree_to_compass()
        2. calc_trend()
        """

        # test degree_to_compass()
        for inp, outp in six.iteritems(self.compass_dict):
            self.assertEqual(user.rtgd.degree_to_compass(inp), outp)

        # test calc_trend()
        # first get our kwargs for passing to calc_trend()
        _kwargs = dict(self.trend_kwargs)
        # first check that if now_vt has a None value we get None as the result
        self.assertIsNone(user.rtgd.calc_trend(**_kwargs))
        # now set now_vt to a None, None, None ValueTuple
        _kwargs['now_vt'] = ValueTuple(None, None, None)
        # check we still get None
        self.assertIsNone(user.rtgd.calc_trend(**_kwargs))
        # now reset now_vt
        _kwargs['now_vt'] = ValueTuple(23.5, 'degree_C', 'group_temperature')
        # create a Mock object to mimic Manager.getRecord()
        dbm_mock = unittest.mock.Mock()
        _kwargs['db_manager'] = dbm_mock
        # set the getRecord() return value to None, this is irrespective of any
        # parameters passed in
        dbm_mock.getRecord.return_value = None
        # confirm calc_trend() returns None
        self.assertIsNone(user.rtgd.calc_trend(**_kwargs))
        # set the getRecord() return value to a minimal dict that does not
        # include the obs type concerned (outTemp)
        dbm_mock.getRecord.return_value = {'dateTime': 1653881860, 'usUnits': 16, 'outHumidity': 77}
        # confirm calc_trend() returns None
        self.assertIsNone(user.rtgd.calc_trend(**_kwargs))
        # set the getRecord() return value to a minimal dict that does include
        # the obs type concerned (outTemp)
        dbm_mock.getRecord.return_value = {'dateTime': 1653881860, 'usUnits': 16, 'outTemp': 21.4}
        # confirm test calc_trend() now returns 2.1
        self.assertAlmostEqual(user.rtgd.calc_trend(**_kwargs), 2.1, places=4)
        # set the getRecord() return value to a minimal dict that does include
        # the obs type concerned (outTemp) but in degree_F not degree_C
        dbm_mock.getRecord.return_value = {'dateTime': 1653881860, 'usUnits': 1, 'outTemp': 79.4}
        # confirm test calc_trend() now returns -2.8333
        self.assertAlmostEqual(user.rtgd.calc_trend(**_kwargs), -2.8333, places=4)
        # this time change the target units to degree_F
        _kwargs['target_units'] = 'degree_F'
        # confirm test calc_trend() now returns -5.1
        self.assertAlmostEqual(user.rtgd.calc_trend(**_kwargs), -5.1, places=4)


class ListsAndDictsTestCase(unittest.TestCase):
    """Test case to test list and dict consistency."""

    def setUp(self):

        # construct the default field map
        self.default_field_map = dict(user.rtgd.DEFAULT_FIELD_MAP)
        # construct the default field map
        self.default_group_map = dict(user.rtgd.DEFAULT_GROUP_MAP)
        # construct the default field map
        self.default_format_map = dict(user.rtgd.DEFAULT_FORMAT_MAP)
        # get a set of WeeWX supported units, we need to build this ourself
        # from various dicts and configs
        _unit_set = set(weewx.defaults.defaults['Units']['StringFormats'].keys())
        _unit_set.update(weewx.defaults.defaults['Units']['Groups'].values())
        _unit_set.update(weewx.defaults.defaults['Units']['Labels'].keys())
        _unit_set.update(weewx.units.conversionDict.keys())
        self.unit_set = _unit_set

    def test_dicts(self):
        """Test dicts for consistency"""

        # test the default field map
        for field, field_dict in six.iteritems(self.default_field_map):
            # each field map entry must include a 'source' field
            self.assertIn('source',
                          field_dict.keys(),
                          msg="A field in the default field map does not "
                              "include a 'source' entry")
            # each field map entry must include a 'group' field
            self.assertIn('group',
                          field_dict.keys(),
                          msg="A field in the default field map does not "
                              "include a 'format' entry")
            # each field map entry 'group' field must be a valid unit group
            self.assertIn(field_dict['group'], weewx.units.USUnits.keys(),
                          msg="A field in the default field map contains an "
                              "invalid unit group")

        # test the default group map
        for group, unit in six.iteritems(self.default_group_map):
            # each group map key must be a valid unit group
            self.assertIn(group, weewx.units.USUnits.keys(),
                          msg="A key in the default group map is not "
                              "a valid unit group")
            # each group map value must be a valid unit
            self.assertIn(unit, self.unit_set,
                          msg="A value in the default group map is not "
                              "a valid unit")

        # test the default format map
        for unit, format_str in six.iteritems(self.default_format_map):
            # each format map key must be a valid unit
            self.assertIn(unit, self.unit_set,
                          msg="A key in the default format map is not "
                              "a valid unit")
            # each format map value must be a string of length >= 2
            self.assertGreaterEqual(len(format_str), 2,
                                    msg="A value in the default format map is not "
                                        "a valid format string")


class RtgdThreadTestCase(unittest.TestCase):
    """Test case to test RtgdThread."""

    rtgd_thread_config = {
        'WEEWX_ROOT': '/home/weewx',
        'Station': {
            'station_type': 'test_station_type'
        },
        'StdReport': {
            'HTML_ROOT': 'public_html'
        },
        'RealtimeGaugeData': {
        }
    }
    latitude_f = 10
    longitude_f = 10
    altitude = 10
    # default field map
    DEFAULT_FIELD_MAP = {
        'temp': {
            'source': 'outTemp',
            'group': 'group_temperature',
            'format': '%.1f',
            'default': (0, 'degree_C', 'group_temperature')
        },
        'tempTL': {
            'source': 'outTemp',
            'aggregate': 'min',
            'aggregate_period': 'day',
            'group': 'group_temperature',
            'format': '%.1f',
            'default': (0, 'degree_C', 'group_temperature')
        },
        'tempTH': {
            'source': 'outTemp',
            'aggregate': 'max',
            'aggregate_period': 'day',
            'group': 'group_temperature',
            'format': '%.1f',
            'default': (0, 'degree_C', 'group_temperature')
        },
        'TtempTL': {
            'source': 'outTemp',
            'aggregate': 'mintime',
            'aggregate_period': 'day',
            'group': 'group_time',
            'format': '%H:%M',
            'default': (0, 'unix_epoch', 'group_time')
        },
        'TtempTH': {
            'source': 'outTemp',
            'aggregate': 'maxtime',
            'aggregate_period': 'day',
            'group': 'group_time',
            'format': '%H:%M',
            'default': (0, 'unix_epoch', 'group_time')
        },
        'temptrend': {
            'source': 'outTemp',
            'aggregate': 'trend',
            'aggregate_period': '3600',
            'grace_period': '300',
            'group': 'group_temperature',
            'format': '%.1f',
            'default': (0, 'degree_C', 'group_temperature')
        },
        'intemp': {
            'source': 'inTemp',
            'group': 'group_temperature',
            'format': '%.1f',
            'default': (0, 'degree_C', 'group_temperature')
        },
        'intempTL': {
            'source': 'inTemp',
            'aggregate': 'min',
            'aggregate_period': 'day',
            'group': 'group_temperature',
            'format': '%.1f',
            'default': (0, 'degree_C', 'group_temperature')
        },
        'intempTH': {
            'source': 'inTemp',
            'aggregate': 'max',
            'aggregate_period': 'day',
            'group': 'group_temperature',
            'format': '%.1f',
            'default': (0, 'degree_C', 'group_temperature')
        },
        'TintempTL': {
            'source': 'inTemp',
            'aggregate': 'mintime',
            'aggregate_period': 'day',
            'group': 'group_time',
            'format': '%H:%M',
            'default': (0, 'unix_epoch', 'group_time')
        },
        'TintempTH': {
            'source': 'inTemp',
            'aggregate': 'maxtime',
            'aggregate_period': 'day',
            'group': 'group_time',
            'format': '%H:%M',
            'default': (0, 'unix_epoch', 'group_time')
        },
        'hum': {
            'source': 'outHumidity',
            'group': 'group_percent',
            'format': '%.0f',
            'default': (0, 'percent', 'group_percent')
        },
        'humTL': {
            'source': 'outHumidity',
            'aggregate': 'min',
            'aggregate_period': 'day',
            'group': 'group_percent',
            'format': '%.0f',
            'default': (0, 'percent', 'group_percent')
        },
        'humTH': {
            'source': 'outHumidity',
            'aggregate': 'max',
            'aggregate_period': 'day',
            'group': 'group_percent',
            'format': '%.0f',
            'default': (0, 'percent', 'group_percent')
        },
        'ThumTL': {
            'source': 'outHumidity',
            'aggregate': 'mintime',
            'aggregate_period': 'day',
            'group': 'group_time',
            'format': '%H:%M',
            'default': (0, 'unix_epoch', 'group_time')
        },
        'ThumTH': {
            'source': 'outHumidity',
            'aggregate': 'maxtime',
            'aggregate_period': 'day',
            'group': 'group_time',
            'format': '%H:%M',
            'default': (0, 'unix_epoch', 'group_time')
        },
        'inhum': {
            'source': 'inHumidity',
            'group': 'group_percent',
            'format': '%.0f',
            'default': (0, 'percent', 'group_percent')
        },
        'inhumTL': {
            'source': 'inHumidity',
            'aggregate': 'min',
            'aggregate_period': 'day',
            'group': 'group_percent',
            'format': '%.0f',
            'default': (0, 'percent', 'group_percent')
        },
        'inhumTH': {
            'source': 'inHumidity',
            'aggregate': 'max',
            'aggregate_period': 'day',
            'group': 'group_percent',
            'format': '%.0f',
            'default': (0, 'percent', 'group_percent')
        },
        'TinhumTL': {
            'source': 'inHumidity',
            'aggregate': 'mintime',
            'aggregate_period': 'day',
            'group': 'group_time',
            'format': '%H:%M',
            'default': (0, 'unix_epoch', 'group_time')
        },
        'TinhumTH': {
            'source': 'inHumidity',
            'aggregate': 'maxtime',
            'aggregate_period': 'day',
            'group': 'group_time',
            'format': '%H:%M',
            'default': (0, 'unix_epoch', 'group_time')
        },
        'dew': {
            'source': 'dewpoint',
            'group': 'group_temperature',
            'format': '%.1f',
            'default': (0, 'degree_C', 'group_temperature')
        },
        'dewpointTL': {
            'source': 'dewpoint',
            'aggregate': 'min',
            'aggregate_period': 'day',
            'group': 'group_temperature',
            'format': '%.1f',
            'default': (0, 'degree_C', 'group_temperature')
        },
        'dewpointTH': {
            'source': 'dewpoint',
            'aggregate': 'max',
            'aggregate_period': 'day',
            'group': 'group_temperature',
            'format': '%.1f',
            'default': (0, 'degree_C', 'group_temperature')
        },
        'TdewpointTL': {
            'source': 'dewpoint',
            'aggregate': 'mintime',
            'aggregate_period': 'day',
            'group': 'group_time',
            'format': '%H:%M',
            'default': (0, 'unix_epoch', 'group_time')
        },
        'TdewpointTH': {
            'source': 'dewpoint',
            'aggregate': 'maxtime',
            'aggregate_period': 'day',
            'group': 'group_time',
            'format': '%H:%M',
            'default': (0, 'unix_epoch', 'group_time')
        },
        'wchill': {
            'source': 'windchill',
            'group': 'group_temperature',
            'format': '%.1f',
            'default': (0, 'degree_C', 'group_temperature')
        },
        'wchillTL': {
            'source': 'windchill',
            'aggregate': 'min',
            'aggregate_period': 'day',
            'group': 'group_temperature',
            'format': '%.1f',
            'default': (0, 'degree_C', 'group_temperature')
        },
        'TwchillTL': {
            'source': 'windchill',
            'aggregate': 'mintime',
            'aggregate_period': 'day',
            'group': 'group_time',
            'format': '%H:%M',
            'default': (0, 'unix_epoch', 'group_time')
        },
        'heatindex': {
            'source': 'heatindex',
            'group': 'group_temperature',
            'format': '%.1f',
            'default': (0, 'degree_C', 'group_temperature')
        },
        'heatindexTH': {
            'source': 'heatindex',
            'aggregate': 'max',
            'aggregate_period': 'day',
            'group': 'group_temperature',
            'format': '%.1f',
            'default': (0, 'degree_C', 'group_temperature')
        },
        'TheatindexTH': {
            'source': 'heatindex',
            'aggregate': 'maxtime',
            'aggregate_period': 'day',
            'group': 'group_time',
            'format': '%H:%M',
            'default': (0, 'unix_epoch', 'group_time')
        },
        'apptemp': {
            'source': 'appTemp',
            'group': 'group_temperature',
            'format': '%.1f',
            'default': (0, 'degree_C', 'group_temperature')
        },
        'apptempTL': {
            'source': 'appTemp',
            'aggregate': 'min',
            'aggregate_period': 'day',
            'group': 'group_temperature',
            'format': '%.1f',
            'default': (0, 'degree_C', 'group_temperature')
        },
        'apptempTH': {
            'source': 'appTemp',
            'aggregate': 'max',
            'aggregate_period': 'day',
            'group': 'group_temperature',
            'format': '%.1f',
            'default': (0, 'degree_C', 'group_temperature')
        },
        'TapptempTL': {
            'source': 'appTemp',
            'aggregate': 'mintime',
            'aggregate_period': 'day',
            'group': 'group_time',
            'format': '%H:%M',
            'default': (0, 'unix_epoch', 'group_time')
        },
        'TapptempTH': {
            'source': 'appTemp',
            'aggregate': 'maxtime',
            'aggregate_period': 'day',
            'group': 'group_time',
            'format': '%H:%M',
            'default': (0, 'unix_epoch', 'group_time')
        },
        'humidex': {
            'source': 'humidex',
            'group': 'group_temperature',
            'format': '%.1f',
            'default': (0, 'degree_C', 'group_temperature')
        },
        'press': {
            'source': 'barometer',
            'group': 'group_pressure',
            'format': '%.1f',
            'default': (0, 'hPa', 'group_pressure')
        },
        'pressTL': {
            'source': 'barometer',
            'aggregate': 'min',
            'aggregate_period': 'day',
            'group': 'group_pressure',
            'format': '%.1f',
            'default': (0, 'hPa', 'group_pressure')
        },
        'pressTH': {
            'source': 'barometer',
            'aggregate': 'max',
            'aggregate_period': 'day',
            'group': 'group_pressure',
            'format': '%.1f',
            'default': (0, 'hPa', 'group_pressure')
        },
        'TpressTL': {
            'source': 'barometer',
            'aggregate': 'mintime',
            'aggregate_period': 'day',
            'group': 'group_time',
            'format': '%H:%M',
            'default': (0, 'unix_epoch', 'group_time')
        },
        'TpressTH': {
            'source': 'barometer',
            'aggregate': 'maxtime',
            'aggregate_period': 'day',
            'group': 'group_time',
            'format': '%H:%M',
            'default': (0, 'unix_epoch', 'group_time')
        },
        'presstrendval': {
            'source': 'barometer',
            'aggregate': 'trend',
            'aggregate_period': '3600',
            'grace_period': '300',
            'group': 'group_pressure',
            'format': '%.1f',
            'default': (0, 'hPa', 'group_pressure')
        },
        'rfall': {
            'source': 'rain',
            'aggregate': 'sum',
            'aggregate_period': 'day',
            'group': 'group_rain',
            'format': '%.1f',
            'default': (0, 'mm', 'group_rain')
        },
        'rrate': {
            'source': 'rainRate',
            'group': 'group_rainrate',
            'format': '%.1f',
            'default': (0, 'mm_per_hour', 'group_rainrate')
        },
        'rrateTM': {
            'source': 'rainRate',
            'aggregate': 'max',
            'aggregate_period': 'day',
            'group': 'group_rainrate',
            'format': '%.1f',
            'default': (0, 'mm_per_hour', 'group_rainrate')
        },
        'TrrateTM': {
            'source': 'rainRate',
            'aggregate': 'maxtime',
            'aggregate_period': 'day',
            'group': 'group_time',
            'format': '%H:%M',
            'default': (0, 'unix_epoch', 'group_time')
        },
        'wlatest': {
            'source': 'windSpeed',
            'group': 'group_speed',
            'format': '%.0f',
            'default': (0, 'km_per_hour', 'group_speed')
        },
        'windTM': {
            'source': 'windSpeed',
            'aggregate': 'max',
            'aggregate_period': 'day',
            'group': 'group_speed',
            'format': '%.0f',
            'default': (0, 'km_per_hour', 'group_speed')
        },
        'wgust': {
            'source': 'windGust',
            'group': 'group_speed',
            'format': '%.0f',
            'default': (0, 'km_per_hour', 'group_speed')
        },
        'wgustTM': {
            'source': 'windGust',
            'aggregate': 'max',
            'aggregate_period': 'day',
            'group': 'group_speed',
            'format': '%.0f',
            'default': (0, 'km_per_hour', 'group_speed')
        },
        'TwgustTM': {
            'source': 'windGust',
            'aggregate': 'maxtime',
            'aggregate_period': 'day',
            'group': 'group_time',
            'format': '%H:%M',
            'default': (0, 'unix_epoch', 'group_time')
        },
        'bearing': {
            'source': 'windDir',
            'group': 'group_direction',
            'format': '%.0f',
            'default': (0.0, 'degree_compass', 'group_direction')
        },
        'avgbearing': {
            'source': 'wind',
            'aggregate': 'vecdir',
            'aggregate_period': 600,
            'group': 'group_direction',
            'format': '%.0f',
            'default': (0, 'degree_compass', 'group_direction')
        },
        'bearingTM': {
            'source': 'wind',
            'aggregate': 'maxdir',
            'aggregate_period': 'day',
            'group': 'group_direction',
            'format': '%.0f',
            'default': (0, 'degree_compass', 'group_direction')
        },
        'windrun': {
            'source': 'windrun',
            'aggregate': 'sum',
            'aggregate_period': 'day',
            'group': 'group_distance',
            'format': '%.1f',
            'default': (0, 'km', 'group_distance')
        },
        'UV': {
            'source': 'UV',
            'group': 'group_uv',
            'format': '%.1f',
            'default': (0, 'uv_index', 'group_uv')
        },
        'UVTH': {
            'source': 'UV',
            'aggregate': 'max',
            'aggregate_period': 'day',
            'group': 'group_uv',
            'format': '%.1f',
            'default': (0, 'uv_index', 'group_uv')
        },
        'SolarRad': {
            'source': 'radiation',
            'group': 'group_radiation',
            'format': '%.0f',
            'default': (0, 'watt_per_meter_squared', 'group_radiation'),
        },
        'SolarRadTM': {
            'source': 'radiation',
            'aggregate': 'max',
            'aggregate_period': 'day',
            'group': 'group_radiation',
            'format': '%.0f',
            'default': (0, 'watt_per_meter_squared', 'group_radiation')
        },
        'CurrentSolarMax': {
            'source': 'maxSolarRad',
            'group': 'group_radiation',
            'format': '%.0f',
            'default': (0, 'watt_per_meter_squared', 'group_radiation')
        },
        'cloudbasevalue': {
            'source': 'cloudbase',
            'group': 'group_altitude',
            'format': '%.0f',
            'default': (0, 'foot', 'group_altitude')
        }
    }

    def setUp(self):
        pass

    def test_field_map(self):
        """Test creation of the field map."""

        _rtgd_thread = user.rtgd.RealtimeGaugeDataThread(control_queue=None,
                                                         result_queue=None,
                                                         config_dict=self.rtgd_thread_config,
                                                         manager_dict={},
                                                         latitude=self.latitude_f,
                                                         longitude=self.longitude_f,
                                                         altitude=self.altitude)
        # self.maxDiff = None
        self.assertDictEqual(_rtgd_thread.field_map,
                             self.DEFAULT_FIELD_MAP,
                             msg='Default field map mismatch')

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
    test_cases = (UtilitiesTestCase, ListsAndDictsTestCase, RtgdThreadTestCase)

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
