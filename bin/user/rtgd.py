"""
rtgd.py

A WeeWX service to generate a loop based gauge-data.txt.

Copyright (C) 2017-2023 Gary Roderick             gjroderick<at>gmail.com

This program is free software: you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free Software
Foundation, either version 3 of the License, or (at your option) any later
version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY
WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
PARTICULAR PURPOSE.  See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with
this program.  If not, see https://www.gnu.org/licenses/.

Version: 0.6.3                                          Date: 3 April 2023

  Revision History
    3 April 2023        v0.6.3
        - fix issue with missing or sporadic windGust/windSpeed loop data
    16 March 2023       v0.6.2
        - fix issue that resulted in incorrect formatting of some non-metric
          observations
        - fix unhandled TypeError that occurs if the WeeWX engine restarts as a
          result of a recoverable error, issue #30 refers
    4 November 2022     v0.6.1
        - fixed issue where a user specified max_cache_age config option is
          used as a string instead of an integer
    3 November 2022     v0.6.0
        - fixed bug whereby 10 minute average wind bearing always matched
          current wind bearing
        - significant rewrite of get_field_value() method in preparation for
          full implementation of field map
    17 April 2022       v0.5.5
        - fixed bug in date and dateFormat fields that resulted in the
          incorrect 'last rainfall' date and time being displayed on rainfall
          gauge mouseovers
        - as a result of the date and dateFormat bug fix date_format and
          time_format config options are now limited to a number of fixed
          formats
    13 April 2022       v0.5.4
        - added the inadvertently omitted humidex field
        - added field TrrateTM
        - reformatted DEFAULT_FIELD_MAP
    11 April 2022       v0.5.3
        - fixed bug where incorrect output field name is used for inside
          temperature and associated aggregates/times
        - added inside humidity and associated aggregates/times to output
    22 October 2021     v0.5.2
        - fixed bug where tempTH contained today's outTemp minimum rather than
          maximum
    17 October 2021     v0.5.1
        - fixed bug where the default metric rain rate units used cm per hour
          rather than mm per hour
    15 September 2021   v0.5.0
        - added ability to rsync gauge-data.txt to an rsync capable server,
          thanks to John Kline
        - fixed bug that caused rtgd to abort if the first loop packet did not
          contain inTemp
        - reworked buffering of loop data, now use dedicated scalar and vector
          buffer objects similar in operation to the WeeWX accumulators
        - implemented a field_map config item allowing certain JSON output field
          properties to be controlled by the user
        - field currentSolarMax is no longer directly calculated by rtgd but is
          now populated from WeeWX field maxSolarRad
        - field lastRainTipISO is now populated
        - removed deprecated field Tbeaufort
        - rtgd now logs the rtgd version number on WeeWX startup
    23 November 2019    v0.4.2
        - fix error in some expressions including > and < where operands could
          be None
    19 November 2019    v0.4.1
        - fix max() error under python3
        - implemented kludgy work around for lack of response message when
          using HTTP POST under python 3
    16 November 2019    v0.4.0
        - updated to work under WeeWX v4.0 using either python 2 or 3
    4 April 2019        v0.3.7
        - revised WU API response parsing to eliminate occasional errors where
          no forecast text was found
    28 March 2019       v0.3.6
        - added support for new weather.com based WU API
        - removed support for old api.wunderground.com based WU API
        - updated to gauge-data.txt version 14 through addition of inTemp
          max/min and times fields (intempTH, intempTL, TintempTH and TintempTL)
        - minor reformatting of some RealtimeGaugeDataThread __init__ logging
        - reformatted up front comments
        - fixed incorrect rtgd.py version number
    1 January 2019      v0.3.5
        - added support for Darksky forecast API
        - added support for Zambretti forecast text (subject to WeeWX
          forecasting extension being installed)
        - refactored code for obtaining scroller text
        - each scroller text block now uses its own 2nd level (ie [[ ]]) config
          with the scroller block specified under [RealtimeGaugeData]
    26 April 2018       v0.3.4 (not released)
        - Added support for optional fields mrfall and yrfall that provide 
          month and year to date rainfall respectively. Optional fields are 
          calculated/added to output if config options mtd_rain and/or ytd_rain 
          are set True.
    26 April 2018       v0.3.3
        - implemented atomic write when writing gauge-data.txt to file
    20 January 2018     v0.3.2
        - modified rtgdthread queue management to fix 100% CPU usage issue
    3 December 2017     v0.3.1
        - added ignore_lost_contact config option to ignore the sensor contact
          check result
        - refactored lost contact flag check code, now uses a dedicated method
          to determine whether sensor contact has been lost
        - changed a log entry to indicate 'rtgd' as the block not 'engine'
    4 September 2017    v0.3.0
        - added ability to include Weather Underground forecast text
    8 July 2017         v0.2.14
        - changed default decimal places for foot, inHg, km_per_hour and
          mile_per_hour
        - reformatted change summary
        - minor refactoring of RtgdBuffer class
    6 May 2017          v0.2.13
        - unnecessary whitespace removed from JSON output(issue #2)
        - JSON output now sorted alphabetically by key (issue #2)
        - Revised debug logging. Now supports debug=0,1,2 and 3: (issue #7)
          0 - standard WeeWX output, no debug info
          1 - as per debug=0, advises whether Zambretti is available, logs
              minor non-fatal errors (eg posting)
          2 - as per debug=1, logs events that occur, eg packets queued,
              packets processed, output generated
          3   as per debug=2, logs packet/record contents
        - gauge-data.txt destination directory tree is created if it does not
          exist(issue #8)
    27 March 2017       v0.2.12(never released)
        - fixed empty sequence ValueError associated with BearingRangeFrom10
          and BearingRangeTo10
        - fixed division by zero error in windrun calculations for first
          archive period of the day
    22 March 2017       v0.2.11
        - can now include local date/time in scroller text by including
          strftime() format directives in the scroller text
        - gauge-data.txt content can now be sent to a remote URL via HTTP POST.
          Thanks to Alec Bennett for his idea.
    17 March 2017       v0.2.10
        - now supports reading scroller text from a text file specified by the
          scroller_text config option in [RealtimeGaugeData]
    7 March 2017        v0.2.9
        - reworked ten minute gust calculation to fix problem where red gust
          'wedge' would occasionally temporarily disappear from wind speed
          gauge
    28 February 2017    v0.2.8
        - reworked day max/min calculations to better handle missing historical
          data. If historical max/min data is missing day max/min will default
          to the current value for the obs concerned.
    26 February 2017    v0.2.7
        - loop packets are now cached to support stations that emit partial
          packets
        - windSpeed obtained from archive is now only handled as a ValueTuple
          to avoid units issues
    22 February 2017    v0.2.6
        - updated docstring config options to reflect current library of
          available options
        - 'latest' and 'avgbearing' wind directions now return the last
          non-None wind direction respectively when their feeder direction is
          None
        - implemented optional scroller_text config option allowing fixed
          scroller text to be specified in lieu of Zambretti forecast text
        - renamed rtgd thread and queue variables
        - no longer reads unit group config options that have only one possible
          unit
        - use of mmHg, knot or cm units reverts to hPa, mile_per_hour and mm
          respectively due to WeeWX or SteelSeries Gauges not understanding the
          unit (or derived unit)
        - made gauge-data.txt unit code determination more robust
        - reworked code that formats gauge-data.txt field data to better handle
          None values
    21 February 2017    v0.2.5
        - fixed error where altitude units could not be changed from meter
        - rainrate and windrun unit groups are now derived from rain and speed
          units groups respectively
        - solar calc config options no longer searched for in [StdWXCalculate]
    20 February 2017    v0.2.4
        - fixed error where rain units could not be changed from mm
        - pressures now formats to correct number of decimal places
        - reworked temp and pressure trend formatting
    20 February 2017    v0.2.3
        - Fixed logic error in windrose calculations. Minor tweaking of
          windrose processing.
    19 February 2017    v0.2.2
        - Added config option apptemp_binding specifying a binding containing
          appTemp data. apptempTL and apptempTH default to apptemp if binding
          not specified or it does not contain appTemp data.
    15 February 2017    v0.2.1
        - fixed error that resulted in incorrect pressL and pressH values
    24 January 2017     v0.2.0
        - now runs in a thread to eliminate blocking impact on WeeWX
        - now calculates WindRoseData
        - now calculates pressL and pressH
        - frequency of generation is now specified by a single config option
          min_interval
        - gauge-data.txt output path is now specified by rtgd_path config
          option
        - added config options for windrose period and number of compass points
          to be generated
    19 January 2017     v0.1.2
        - fix error that occurred when stations do not emit radiation
    18 January 2017     v0.1.1
        - better handles loop observations that are None
    3 January 2017      v0.1.0
        - initial release


A WeeWX service to generate a loop based gauge-data.txt.

Used to update the SteelSeries Weather Gauges in near real time.

Inspired by crt.py v0.5 by Matthew Wall, a WeeWX service to emit loop data to
file in Cumulus realtime format. Refer http://wiki.sandaysoft.com/a/Realtime.txt

Use of HTTP POST to send gauge-data.txt content to a remote URL inspired by
work by Alec Bennett. Refer https://github.com/wrybread/weewx-realtime_gauge-data.

Abbreviated instructions for use:

1.  Install the Realtime gauge-data extension using the wee_extension utility:

    - download the latest Realtime gauge-data extension package:

        $ wget -P /var/tmp https://github.com/gjr80/weewx-realtime_gauge-data/releases/download/v0.6.2/rtgd-0.6.2.tar.gz

    - install the Realtime gauge-data extension:

        $ wee_extension --install=/var/tmp/rtgd-0.6.2.tar.gz

        Note: Depending on your system/installation the above command may need
              to be prefixed with 'sudo'.

        Note: Depending on your WeeWX installation wee_extension may need to be
              prefixed with the path to wee_extension.

2.  Restart the WeeWX daemon:

        $ sudo /etc/init.d/weewx restart

    or

        $ sudo service weewx restart

    or

        $ sudo systemctl restart weewx

3.  Confirm that gauge-data.txt is being generated regularly.


To do:
    - hourlyrainTH and ThourlyrainTH. Need to populate these fields, presently
      set to 0.0 and 00:00 respectively.
    - Lost contact with station sensors is implemented for Vantage and
      Simulator stations only. Need to extend current code to cater for the
      WeeWX supported stations. Current code assume that contact is there
      unless told otherwise.
    - consolidate wind lists into a single list.

Handy things/conditions noted from analysis of SteelSeries Weather Gauges:
    - wind direction is from 1 to 360, 0 is treated as calm ie no wind
    - trend periods are assumed to be one hour except for barometer which is
      taken as three hours
    - wspeed is 10 minute average wind speed (refer to wind speed gauge hover
      and gauges.js
"""

# python imports
import copy
import datetime
import errno
import json
import logging
import math
import os
import os.path
import socket
import sys
import threading
import time

from operator import itemgetter

# Python 2/3 compatibility shims
import six
from six.moves import http_client
from six.moves import queue
from six.moves import urllib

# WeeWX imports
import weewx
import weeutil.logger
import weeutil.rsyncupload
import weeutil.weeutil
import weewx.units
import weewx.wxformulas

from weewx.engine import StdService
from weewx.units import ValueTuple, convert, getStandardUnitType, ListOfDicts, as_value_tuple
from weeutil.weeutil import to_bool, to_int

# get a logger object
log = logging.getLogger(__name__)

# version number of this script
RTGD_VERSION = '0.6.3'
# version number (format) of the generated gauge-data.txt
GAUGE_DATA_VERSION = '14'

# ordinal compass points supported
COMPASS_POINTS = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE',
                  'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW', 'N']

# default units to use
# Default to Metric with speed in 'km_per_hour' and rain in 'mm'.
# weewx.units.MetricUnits is close, but we need to change the rain units (we
# could use MetricWX, but then we would need to change the speed units!)
# start by making a deepcopy
_UNITS = copy.deepcopy(weewx.units.MetricUnits)
# now set the group_rain and group_rainrate units
_UNITS['group_rain'] = 'mm'
_UNITS['group_rainrate'] = 'mm_per_hour'
# now assign to our defaults
DEFAULT_UNITS = _UNITS

# map WeeWX unit names to unit names supported by the SteelSeries Weather
# Gauges
UNITS_WIND = {'mile_per_hour':      'mph',
              'meter_per_second':   'm/s',
              'km_per_hour':        'km/h'}
UNITS_TEMP = {'degree_C': 'C',
              'degree_F': 'F'}
UNITS_PRES = {'inHg': 'in',
              'mbar': 'mb',
              'hPa':  'hPa'}
UNITS_RAIN = {'inch': 'in',
              'mm':   'mm'}
UNITS_CLOUD = {'foot':  'ft',
               'meter': 'm'}
GROUP_DIST = {'mile_per_hour':      'mile',
              'meter_per_second':   'km',
              'km_per_hour':        'km'}

# list of obs that we will attempt to buffer
MANIFEST = ['outTemp', 'barometer', 'outHumidity', 'rain', 'rainRate',
            'humidex', 'windchill', 'heatindex', 'windSpeed', 'inTemp',
            'inHumidity', 'appTemp', 'dewpoint', 'windDir', 'UV', 'radiation',
            'wind', 'windGust', 'windGustDir', 'windrun']

# obs for which we need a history
HIST_MANIFEST = ['windSpeed', 'windDir', 'windGust', 'wind']

# length of history to be maintained in seconds
MAX_AGE = 600

# Define station lost contact checks for supported stations. Note that at
# present only Vantage and FOUSB stations lost contact reporting is supported.
STATION_LOST_CONTACT = {'Vantage': {'field': 'rxCheckPercent', 'value': 0},
                        'FineOffsetUSB': {'field': 'status', 'value': 0x40},
                        'Ultimeter': {'field': 'rxCheckPercent', 'value': 0},
                        'WMR100': {'field': 'rxCheckPercent', 'value': 0},
                        'WMR200': {'field': 'rxCheckPercent', 'value': 0},
                        'WMR9x8': {'field': 'rxCheckPercent', 'value': 0},
                        'WS23xx': {'field': 'rxCheckPercent', 'value': 0},
                        'WS28xx': {'field': 'rxCheckPercent', 'value': 0},
                        'TE923': {'field': 'rxCheckPercent', 'value': 0},
                        'WS1': {'field': 'rxCheckPercent', 'value': 0},
                        'CC3000': {'field': 'rxCheckPercent', 'value': 0}
                        }
# stations supporting lost contact reporting through their archive record
ARCHIVE_STATIONS = ['Vantage']
# stations supporting lost contact reporting through their loop packet
LOOP_STATIONS = ['FineOffsetUSB']

# default field map
DEFAULT_FIELD_MAP = {
    'temp': {
        'source': 'outTemp',
        'group': 'group_temperature'
    },
    'tempTL': {
        'source': 'outTemp',
        'aggregate': 'min',
        'aggregate_period': 'day',
        'group': 'group_temperature'
    },
    'tempTH': {
        'source': 'outTemp',
        'aggregate': 'max',
        'aggregate_period': 'day',
        'group': 'group_temperature'
    },
    'TtempTL': {
        'source': 'outTemp',
        'aggregate': 'mintime',
        'aggregate_period': 'day',
        'group': 'group_time'
    },
    'TtempTH': {
        'source': 'outTemp',
        'aggregate': 'maxtime',
        'aggregate_period': 'day',
        'group': 'group_time'
    },
    'temptrend': {
        'source': 'outTemp',
        'aggregate': 'trend',
        'aggregate_period': '3600',
        'grace_period': '300',
        'group': 'group_temperature'
    },
    'intemp': {
        'source': 'inTemp',
        'group': 'group_temperature'
    },
    'intempTL': {
        'source': 'inTemp',
        'aggregate': 'min',
        'aggregate_period': 'day',
        'group': 'group_temperature'
    },
    'intempTH': {
        'source': 'inTemp',
        'aggregate': 'max',
        'aggregate_period': 'day',
        'group': 'group_temperature'
    },
    'TintempTL': {
        'source': 'inTemp',
        'aggregate': 'mintime',
        'aggregate_period': 'day',
        'group': 'group_time'
    },
    'TintempTH': {
        'source': 'inTemp',
        'aggregate': 'maxtime',
        'aggregate_period': 'day',
        'group': 'group_time'
    },
    'hum': {
        'source': 'outHumidity',
        'group': 'group_percent'
    },
    'humTL': {
        'source': 'outHumidity',
        'aggregate': 'min',
        'aggregate_period': 'day',
        'group': 'group_percent'
    },
    'humTH': {
        'source': 'outHumidity',
        'aggregate': 'max',
        'aggregate_period': 'day',
        'group': 'group_percent'
    },
    'ThumTL': {
        'source': 'outHumidity',
        'aggregate': 'mintime',
        'aggregate_period': 'day',
        'group': 'group_time'
    },
    'ThumTH': {
        'source': 'outHumidity',
        'aggregate': 'maxtime',
        'aggregate_period': 'day',
        'group': 'group_time'
    },
    'inhum': {
        'source': 'inHumidity',
        'group': 'group_percent'
    },
    'inhumTL': {
        'source': 'inHumidity',
        'aggregate': 'min',
        'aggregate_period': 'day',
        'group': 'group_percent'
    },
    'inhumTH': {
        'source': 'inHumidity',
        'aggregate': 'max',
        'aggregate_period': 'day',
        'group': 'group_percent'
    },
    'TinhumTL': {
        'source': 'inHumidity',
        'aggregate': 'mintime',
        'aggregate_period': 'day',
        'group': 'group_time'
    },
    'TinhumTH': {
        'source': 'inHumidity',
        'aggregate': 'maxtime',
        'aggregate_period': 'day',
        'group': 'group_time'
    },
    'dew': {
        'source': 'dewpoint',
        'group': 'group_temperature'
    },
    'dewpointTL': {
        'source': 'dewpoint',
        'aggregate': 'min',
        'aggregate_period': 'day',
        'group': 'group_temperature'
    },
    'dewpointTH': {
        'source': 'dewpoint',
        'aggregate': 'max',
        'aggregate_period': 'day',
        'group': 'group_temperature'
    },
    'TdewpointTL': {
        'source': 'dewpoint',
        'aggregate': 'mintime',
        'aggregate_period': 'day',
        'group': 'group_time'
    },
    'TdewpointTH': {
        'source': 'dewpoint',
        'aggregate': 'maxtime',
        'aggregate_period': 'day',
        'group': 'group_time'
    },
    'wchill': {
        'source': 'windchill',
        'group': 'group_temperature'
    },
    'wchillTL': {
        'source': 'windchill',
        'aggregate': 'min',
        'aggregate_period': 'day',
        'group': 'group_temperature'
    },
    'TwchillTL': {
        'source': 'windchill',
        'aggregate': 'mintime',
        'aggregate_period': 'day',
        'group': 'group_time'
    },
    'heatindex': {
        'source': 'heatindex',
        'group': 'group_temperature'
    },
    'heatindexTH': {
        'source': 'heatindex',
        'aggregate': 'max',
        'aggregate_period': 'day',
        'group': 'group_temperature'
    },
    'TheatindexTH': {
        'source': 'heatindex',
        'aggregate': 'maxtime',
        'aggregate_period': 'day',
        'group': 'group_time'
    },
    'apptemp': {
        'source': 'appTemp',
        'group': 'group_temperature'
    },
    'apptempTL': {
        'source': 'appTemp',
        'aggregate': 'min',
        'aggregate_period': 'day',
        'group': 'group_temperature'
    },
    'apptempTH': {
        'source': 'appTemp',
        'aggregate': 'max',
        'aggregate_period': 'day',
        'group': 'group_temperature'
    },
    'TapptempTL': {
        'source': 'appTemp',
        'aggregate': 'mintime',
        'aggregate_period': 'day',
        'group': 'group_time'
    },
    'TapptempTH': {
        'source': 'appTemp',
        'aggregate': 'maxtime',
        'aggregate_period': 'day',
        'group': 'group_time'
    },
    'humidex': {
        'source': 'humidex',
        'group': 'group_temperature'
    },
    'press': {
        'source': 'barometer',
        'group': 'group_pressure'
    },
    'pressTL': {
        'source': 'barometer',
        'aggregate': 'min',
        'aggregate_period': 'day',
        'group': 'group_pressure'
    },
    'pressTH': {
        'source': 'barometer',
        'aggregate': 'max',
        'aggregate_period': 'day',
        'group': 'group_pressure'
    },
    'TpressTL': {
        'source': 'barometer',
        'aggregate': 'mintime',
        'aggregate_period': 'day',
        'group': 'group_time'
    },
    'TpressTH': {
        'source': 'barometer',
        'aggregate': 'maxtime',
        'aggregate_period': 'day',
        'group': 'group_time'
    },
    'presstrendval': {
        'source': 'barometer',
        'aggregate': 'trend',
        'aggregate_period': '3600',
        'grace_period': '300',
        'group': 'group_pressure'
    },
    'rfall': {
        'source': 'rain',
        'aggregate': 'sum',
        'aggregate_period': 'day',
        'group': 'group_rain'
    },
    'rrate': {
        'source': 'rainRate',
        'group': 'group_rainrate'
    },
    'rrateTM': {
        'source': 'rainRate',
        'aggregate': 'max',
        'aggregate_period': 'day',
        'group': 'group_rainrate'
    },
    'TrrateTM': {
        'source': 'rainRate',
        'aggregate': 'maxtime',
        'aggregate_period': 'day',
        'group': 'group_time'
    },
    'wlatest': {
        'source': 'windSpeed',
        'group': 'group_speed'
    },
    'windTM': {
        'source': 'windSpeed',
        'aggregate': 'max',
        'aggregate_period': 'day',
        'group': 'group_speed'
    },
    'wgust': {
        'source': 'windGust',
        'group': 'group_speed'
    },
    'wgustTM': {
        'source': 'windGust',
        'aggregate': 'max',
        'aggregate_period': 'day',
        'group': 'group_speed'
    },
    'TwgustTM': {
        'source': 'windGust',
        'aggregate': 'maxtime',
        'aggregate_period': 'day',
        'group': 'group_time'
    },
    'bearing': {
        'source': 'windDir',
        'default': 0,
        'group': 'group_direction'
    },
    'avgbearing': {
        'source': 'wind',
        'aggregate': 'vecdir',
        'aggregate_period': 600,
        'group': 'group_direction'
    },
    'bearingTM': {
        'source': 'wind',
        'aggregate': 'maxdir',
        'aggregate_period': 'day',
        'group': 'group_direction'
    },
    'windrun': {
        'source': 'windrun',
        'aggregate': 'sum',
        'aggregate_period': 'day',
        'group': 'group_distance'
    },
    'UV': {
        'source': 'UV',
        'group': 'group_uv'
    },
    'UVTH': {
        'source': 'UV',
        'aggregate': 'max',
        'aggregate_period': 'day',
        'group': 'group_uv'
    },
    'SolarRad': {
        'source': 'radiation',
        'group': 'group_radiation'
    },
    'SolarRadTM': {
        'source': 'radiation',
        'aggregate': 'max',
        'aggregate_period': 'day',
        'group': 'group_radiation'
    },
    'CurrentSolarMax': {
        'source': 'maxSolarRad',
        'group': 'group_radiation'
    },
    'cloudbasevalue': {
        'source': 'cloudbase',
        'group': 'group_altitude'
    }
}

# default group map
DEFAULT_GROUP_MAP = {
    'group_temperature': 'degree_C',
    'group_percent': 'percent',
    'group_pressure': 'hPa',
    'group_speed': 'km_per_hour',
    'group_distance': 'km',
    'group_direction': 'degree_compass',
    'group_rain': 'mm',
    'group_rainrate': 'mm_per_hour',
    'group_radiation': 'watt_per_meter_squared',
    'group_uv': 'uv_index',
    'group_altitude': 'foot',
    'group_time': 'unix_epoch'
}

# default format map
DEFAULT_FORMAT_MAP = {
    'degree_C': '%.1f',
    'degree_compass': '%.0f',
    'degree_F': '%.1f',
    'foot': '%.0f',
    'hPa': '%.1f',
    'hPa_per_hour': '%.3f',
    'inch': '%.2f',
    'inch_per_hour': '%.2f',
    'inHg': '%.3f',
    'inHg_per_hour': '%.5f',
    'km': '%.1f',
    'km_per_hour': '%.0f',
    'knot': '%.0f',
    'kPa': '%.2f',
    'kPa_per_hour': '%.4f',
    'mbar': '%.1f',
    'mbar_per_hour': '%.4f',
    'meter': '%.0f',
    'meter_per_second': '%.1f',
    'mile': '%.1f',
    'mile_per_hour': '%.0f',
    'mm': '%.1f',
    'mm_per_hour': '%.1f',
    'mmHg': '%.1f',
    'mmHg_per_hour': '%.4f',
    'percent': '%.0f',
    'unix_epoch': '%H:%M',
    'uv_index': '%.1f',
    'watt_per_meter_squared': '%.0f'
}


# ============================================================================
#                     Exceptions that could get thrown
# ============================================================================

class MissingApiKey(IOError):
    """Raised when an API key cannot be found for an external service"""


# ============================================================================
#                          class RealtimeGaugeData
# ============================================================================

class RealtimeGaugeData(StdService):
    """Service that generates gauge-data.txt in near realtime.

    The RealtimeGaugeData class creates and controls a threaded object of class
    RealtimeGaugeDataThread that generates gauge-data.txt. Class
    RealtimeGaugeData feeds the RealtimeGaugeDataThread object with data via an
    instance of queue.Queue.
    """

    def __init__(self, engine, config_dict):
        # initialize my superclass
        super(RealtimeGaugeData, self).__init__(engine, config_dict)

        # log my version number
        log.info('version is %s' % RTGD_VERSION)
        self.rtgd_ctl_queue = queue.Queue()
        # get the RealtimeGaugeData config dictionary
        rtgd_config_dict = config_dict.get('RealtimeGaugeData', {})
        manager_dict = weewx.manager.get_manager_dict_from_config(config_dict,
                                                                  'wx_binding')
        self.db_manager = weewx.manager.open_manager(manager_dict)

        # get a source object that will provide the scroller text
        self.source = self.source_factory(config_dict, rtgd_config_dict, engine)
        # 'start' our block object
        self.source.start()
        # get an instance of class RealtimeGaugeDataThread and start the
        # thread running
        self.rtgd_thread = RealtimeGaugeDataThread(self.rtgd_ctl_queue,
                                                   self.result_queue,
                                                   config_dict,
                                                   manager_dict,
                                                   latitude=engine.stn_info.latitude_f,
                                                   longitude=engine.stn_info.longitude_f,
                                                   altitude=convert(engine.stn_info.altitude_vt, 'meter').value)
        self.rtgd_thread.start()

        # are we providing month and/or year to date rain, default is no we are 
        # not
        self.mtd_rain = to_bool(rtgd_config_dict.get('mtd_rain', False))
        self.ytd_rain = to_bool(rtgd_config_dict.get('ytd_rain', False))
        
        # bind our self to the relevant WeeWX events
        self.bind(weewx.NEW_LOOP_PACKET, self.new_loop_packet)
        self.bind(weewx.NEW_ARCHIVE_RECORD, self.new_archive_record)

        self.source_ctl_queue = None
        self.result_queue = None

    def source_factory(self, config_dict, rtgd_config_dict, engine):
        """Factory to produce a block object."""

        _source = rtgd_config_dict.get('scroller_source', 'text').lower()
        # permit any variant of 'wu' as shorthand for Weather Underground
        _source = 'weatherunderground' if _source == 'wu' else _source
        # permit any variant of 'ds' as shorthand for Dark Sky
        _source = 'darksky' if _source == 'ds' else _source
        # if we made it this far we have all we need to create an object
        source_class = SCROLLER_SOURCES.get(_source)
        if source_class is None:
            # We have an invalid block specified. Log this and use the default
            # class Source which will provide a zero length string for the 
            # scroller text.
            log.info("Unknown block specified for scroller_text")
            source_class = Source
        # create queues for passing data and controlling our block object
        self.source_ctl_queue = queue.Queue()
        self.result_queue = queue.Queue()
        # get the block object
        source_object = source_class(self.source_ctl_queue,
                                     self.result_queue,
                                     engine,
                                     config_dict)
        return source_object

    def new_loop_packet(self, event):
        """Puts new loop packets in the rtgd queue."""

        # package the loop packet in a dict since this is not the only data
        # we send via the queue
        _package = {'type': 'loop',
                    'payload': event.packet}
        self.rtgd_ctl_queue.put(_package)
        if weewx.debug == 2:
            log.debug("queued loop packet (%s)" % _package['payload']['dateTime'])
        elif weewx.debug >= 3:
            log.debug("queued loop packet: %s" % _package['payload'])

    def new_archive_record(self, event):
        """Puts archive records in the rtgd queue."""

        # package the archive record in a dict since this is not the only data
        # we send via the queue
        _package = {'type': 'archive',
                    'payload': event.record}
        self.rtgd_ctl_queue.put(_package)
        if weewx.debug == 2:
            log.debug("queued archive record (%s)" % _package['payload']['dateTime'])
        elif weewx.debug >= 3:
            log.debug("queued archive record: %s" % _package['payload'])
        # get alltime min max baro and put in the queue
        # get the min and max values (incl usUnits)
        _minmax_baro = self.get_minmax_obs('barometer')
        # if we have some data then package it in a dict since this is not the
        # only data we send via the queue
        if _minmax_baro:
            _package = {'type': 'stats',
                        'payload': _minmax_baro}
            self.rtgd_ctl_queue.put(_package)
            if weewx.debug == 2:
                log.debug("queued min/max barometer values")
            elif weewx.debug >= 3:
                log.debug("queued min/max barometer values: %s" % _package['payload'])
        # if required get updated month to date rainfall and put in the queue
        if self.mtd_rain:
            _tspan = weeutil.weeutil.archiveMonthSpan(event.record['dateTime']) 
            _rain = self.get_rain(_tspan)
            # if we have some data then package it in a dict since this is not the
            # only data we send via the queue
            if _rain:
                _payload = {'month_rain': _rain}
                _package = {'type': 'stats',
                            'payload': _payload}
                self.rtgd_ctl_queue.put(_package)
                if weewx.debug == 2:
                    log.debug("queued month to date rain")
                elif weewx.debug >= 3:
                    log.debug("queued month to date rain: %s" % _package['payload'])
        # if required get updated year to date rainfall and put in the queue
        if self.ytd_rain:
            _tspan = weeutil.weeutil.archiveYearSpan(event.record['dateTime']) 
            _rain = self.get_rain(_tspan)
            # if we have some data then package it in a dict since this is not the
            # only data we send via the queue
            if _rain:
                _payload = {'year_rain': _rain}
                _package = {'type': 'stats',
                            'payload': _payload}
                self.rtgd_ctl_queue.put(_package)
                if weewx.debug == 2:
                    log.debug("queued year to date rain")
                elif weewx.debug >= 3:
                    log.debug("queued year to date rain: %s" % _package['payload'])

    def shutDown(self):
        """Shut down any threads.

        Would normally do all of a given threads actions in one go but since
        we may have more than one thread and so that we don't have sequential
        (potential) waits of up to 15 seconds we send each thread a shutdown
        signal and then go and check that each has indeed shutdown.
        """

        if hasattr(self, 'rtgd_ctl_queue') and hasattr(self, 'rtgd_thread'):
            if self.rtgd_ctl_queue and self.rtgd_thread.is_alive():
                # Put a None in the rtgd_ctl_queue to signal the thread to
                # shut down
                self.rtgd_ctl_queue.put(None)
        if hasattr(self, 'source_ctl_queue') and hasattr(self, 'source_thread'):
            if self.source_ctl_queue and self.source_thread.is_alive():
                # Put a None in the source_ctl_queue to signal the thread to
                # shut down
                self.source_ctl_queue.put(None)
        if hasattr(self, 'rtgd_thread') and self.rtgd_thread.is_alive():
            # Wait up to 15 seconds for the thread to exit:
            self.rtgd_thread.join(15.0)
            if self.rtgd_thread.is_alive():
                log.error("Unable to shut down %s thread" % self.rtgd_thread.name)
            else:
                log.debug("Shut down %s thread." % self.rtgd_thread.name)
        if hasattr(self, 'source_thread') and self.source_thread.is_alive():
            # Wait up to 15 seconds for the thread to exit:
            self.source_thread.join(15.0)
            if self.source_thread.is_alive():
                log.error("Unable to shut down %s thread" % self.source_thread.name)
            else:
                log.debug("Shut down %s thread." % self.source_thread.name)

    def get_minmax_obs(self, obs_type):
        """Obtain the alltime max/min values for an observation."""

        # create an interpolation dict
        inter_dict = {'table_name': self.db_manager.table_name,
                      'obs_type': obs_type}
        # the query to be used
        minmax_sql = "SELECT MIN(min), MAX(max) FROM %(table_name)s_day_%(obs_type)s"
        # execute the query
        _row = self.db_manager.getSql(minmax_sql % inter_dict)
        if not _row or None in _row:
            return {'min_%s' % obs_type: None,
                    'max_%s' % obs_type: None}
        else:
            return {'min_%s' % obs_type: _row[0],
                    'max_%s' % obs_type: _row[1]}

    def get_rain(self, tspan):
        """Calculate rainfall over a given timespan."""

        _result = {}
        _rain_vt = self.db_manager.getAggregate(tspan, 'rain', 'sum')
        if _rain_vt:
            return _rain_vt
        else:
            return None


# ============================================================================
#                            class HttpPostExport
# ============================================================================

class HttpPostExport(object):
    """Class to handle HTTP posting of gauge-data.txt.

    Once initialised data is posted by calling the objects export method and
    passing the data to be posted.
    """

    def __init__(self, rtgd_config_dict, *_):

        # first find our config
        if 'HttpPost' in rtgd_config_dict:
            post_config_dict = rtgd_config_dict.get('HttpPost', {})
        else:
            post_config_dict = rtgd_config_dict
        # get the remote server URL if it exists, if it doesn't set it to None
        self.remote_server_url = post_config_dict.get('remote_server_url', None)
        # timeout to be used for remote URL posts
        self.timeout = to_int(post_config_dict.get('timeout', 2))
        # response text from remote URL if post was successful
        self.response = post_config_dict.get('response_text', None)

    def export(self, data, dateTime):
        """Post the data."""

        self.post_data(data)

    def post_data(self, data):
        """Post data to a remote URL via HTTP POST.

        This code is modelled on the WeeWX restFUL API, but rather then
        retrying a failed post the failure is logged and then ignored. If
        remote posts are not working then the user should set debug=1 and
        restart WeeWX to see what the log says.

        The data to be posted is sent as a JSON string.

        Inputs:
            data: dict to sent as JSON string
        """

        # get a Request object
        req = urllib.request.Request(self.remote_server_url)
        # set our content type to json
        req.add_header('Content-Type', 'application/json')
        # POST the data but wrap in a try..except so we can trap any errors
        try:
            response = self.post_request(req, json.dumps(data,
                                                         separators=(',', ':'),
                                                         sort_keys=True))
        except (urllib.error.URLError, socket.error,
                http_client.BadStatusLine, http_client.IncompleteRead) as e:
            # an exception was thrown, log it and continue
            log.debug("Failed to post data: %s" % e)
        else:
            if 200 <= response.code <= 299:
                # No exception thrown and we got a good response code, but did
                # we get self.response back in a return message? Check for
                # self.response, if its there then we can return. If it's
                # not there then log it and return.
                if self.response is not None:
                    if self.response in response:
                        # did get 'success' so log it and continue
                        if weewx.debug == 2:
                            log.debug("Successfully posted data")
                    else:
                        # it's possible the POST was successful if a response
                        # code of 200 was received if under python3, check
                        # response code and give it the benefit of the doubt
                        # but log it anyway
                        if response.code == 200:
                            log.debug("Data may have been posted successfully. "
                                      "Response message was not received but a valid response code was received.")
                        else:
                            log.debug("Failed to post data: Unexpected response")
                return
            # we received a bad response code, log it and continue
            log.debug("Failed to post data: Code %s" % response.code())

    def post_request(self, request, payload):
        """Post a Request object.

        Inputs:
            request: urllib2 Request object
            payload: the data to sent

        Returns:
            The urllib2.urlopen() response
        """

        # Under python 3 POST data should be bytes or an iterable of bytes and
        # not of type str. So attempt to convert the POST data to bytes, if it
        # already is of type bytes an error will be thrown under python 3, be
        # prepared to catch this error.
        try:
            payload_b = payload.encode('utf-8')
        except TypeError:
            payload_b = payload
        # do the POST
        _response = urllib.request.urlopen(request,
                                           data=payload_b,
                                           timeout=self.timeout)
        return _response


# ============================================================================
#                            class RsyncExport
# ============================================================================

class RsyncExport(object):
    """Class to handle rsync of gauge-data.txt.

    Once initialised data is rsynced by calling the objects export method and
    passing the data to be rsynced.
    """

    def __init__(self, rtgd_config_dict, rtgd_path_file):

        # first find our config
        if 'Rsync' in rtgd_config_dict:
            rsync_config_dict = rtgd_config_dict.get('Rsync', {})
        else:
            rsync_config_dict = rtgd_config_dict
        self.rtgd_path_file = rtgd_path_file
        self.rsync_server = rsync_config_dict.get('rsync_server')
        self.rsync_port = rsync_config_dict.get('rsync_port')
        self.rsync_user = rsync_config_dict.get('rsync_user')
        self.rsync_ssh_options = rsync_config_dict.get('rsync_ssh_options',
                                                       '-o ConnectTimeout=1')
        self.rsync_remote_rtgd_dir = rsync_config_dict.get('rsync_remote_rtgd_dir')
        self.rsync_dest_path_file = os.path.join(self.rsync_remote_rtgd_dir,
                                                 rsync_config_dict.get('rtgd_file_name',
                                                                       'gauge-data.txt'))
        self.rsync_compress = to_bool(rsync_config_dict.get('rsync_compress',
                                                            False))
        self.rsync_log_success = to_bool(rsync_config_dict.get('rsync_log_success',
                                                               False))
        self.rsync_timeout = rsync_config_dict.get('rsync_timeout')
        self.rsync_skip_if_older_than = to_int(rsync_config_dict.get('rsync_skip_if_older_than',
                                                                     4))

    def export(self, data, dateTime):
        """Rsync the data."""

        packet_time = datetime.datetime.fromtimestamp(dateTime)
        self.rsync_data(packet_time)

    def rsync_data(self, packet_time):
        """Perform the actual rsync."""

        # don't upload if more than rsync_skip_if_older_than seconds behind.
        if self.rsync_skip_if_older_than != 0:
            now = datetime.datetime.now()
            age = now - packet_time
            if age.total_seconds() > self.rsync_skip_if_older_than:
                log.info("skipping packet (%s) with age: %d" % (packet_time, age.total_seconds()))
                return
        rsync_upload = weeutil.rsyncupload.RsyncUpload(local_root=self.rtgd_path_file,
                                                       remote_root=self.rsync_dest_path_file,
                                                       server=self.rsync_server,
                                                       user=self.rsync_user,
                                                       port=self.rsync_port,
                                                       ssh_options=self.rsync_ssh_options,
                                                       compress=self.rsync_compress,
                                                       delete=False,
                                                       log_success=self.rsync_log_success,
                                                       timeout=self.rsync_timeout)
        try:
            rsync_upload.run()
        except IOError as e:
            (cl, unused_ob, unused_tr) = sys.exc_info()
            log.error("rtgd.rsync_data: Caught exception %s: %s" % (cl, e))


# ============================================================================
#                       class RealtimeGaugeDataThread
# ============================================================================

class RealtimeGaugeDataThread(threading.Thread):
    """Thread that generates gauge-data.txt in near realtime."""

    def __init__(self, control_queue, result_queue, config_dict, manager_dict,
                 latitude, longitude, altitude):
        # Initialize my superclass:
        threading.Thread.__init__(self)

        # set up a few thread things
        self.setName('RtgdThread')
        self.setDaemon(True)

        self.control_queue = control_queue
        self.result_queue = result_queue
        self.config_dict = config_dict
        self.manager_dict = manager_dict

        # get our RealtimeGaugeData config dictionary
        rtgd_config_dict = config_dict.get('RealtimeGaugeData', {})

        # setup file generation timing
        self.min_interval = rtgd_config_dict.get('min_interval', None)
        self.last_write = 0  # ts (actual) of last generation

        # get our file paths and names
        _path = rtgd_config_dict.get('rtgd_path', '/var/tmp')
        _html_root = os.path.join(config_dict['WEEWX_ROOT'],
                                  config_dict['StdReport'].get('HTML_ROOT', ''))

        self.rtgd_path = os.path.join(_html_root, _path)
        self.rtgd_path_file = os.path.join(self.rtgd_path,
                                           rtgd_config_dict.get('rtgd_file_name',
                                                                'gauge-data.txt'))
        self.rtgd_path_file_tmp = self.rtgd_path_file + '.tmp'

        # get windrose settings
        try:
            self.wr_period = int(rtgd_config_dict.get('windrose_period',
                                                      86400))
        except ValueError:
            self.wr_period = 86400
        try:
            self.wr_points = int(rtgd_config_dict.get('windrose_points', 16))
        except ValueError:
            self.wr_points = 16

        # Construct the group map to be used. The group map maps the unit to be
        # used for each unit group. It is based on the default group map with
        # user overrides from the [RealtimeGaugeData] [[Groups]] stanza.
        _group_map = copy.deepcopy(DEFAULT_GROUP_MAP)
        _group_map.update(rtgd_config_dict.get('Groups', {}))
        # The SteelSeries Gauges do not support rain in cm, but cm is a valid
        # WeeWX rain unit. So if we have rain or rainRate in cm/cm_per_hour
        # force change the unit to mm/mm_per_hour.
        if _group_map['group_rain'] == 'cm':
            _group_map['group_rain'] = 'mm'
        if _group_map['group_rainrate'] == 'cm_per_hour':
            _group_map['group_rainrate'] = 'mm_per_hour'
        self.group_map = _group_map
        # Construct the format map to be used. The format map maps string
        # formats to be used for each unit. It is based on the default format
        # map with user overrides from the [RealtimeGaugeData]
        # [[StringFormats]] stanza.
        _format_map = copy.deepcopy(DEFAULT_FORMAT_MAP)
        _format_map.update(rtgd_config_dict.get('StringFormats', {}))
        self.format_map = _format_map

        # get our groups and format strings
        self.date_format = rtgd_config_dict.get('date_format', '%Y/%m/%d')
        self.time_format = rtgd_config_dict.get('time_format', '%H:%M')
        self.flag_format = '%.0f'
        # Get the field map from our config, if it does not exist use the
        # default. Use a deepcopy of the defaults as we will possibly be
        # modifying the field map.
        _field_map = rtgd_config_dict.get('FieldMap', copy.deepcopy(DEFAULT_FIELD_MAP))

        # get any extensions
        _extensions = rtgd_config_dict.get('FieldMapExtensions', {})
        # and update the field map with the extensions
        _field_map.update(_extensions)
        # make a deepcopy of the extended field map as we will be iterating
        # over it and possibly making changes
        updated_field_map = copy.deepcopy(_field_map)
        # iterate over each field map config entry and convert any default
        # values in the field map to ValueTuples
        for field, field_config in six.iteritems(_field_map):
            # obtain the unit group for this field
            _group = self.get_unit_group(field_config['source'],
                                         field_config.get('aggregate'))
            # Obtain the default; the default could be a scalar, a scalar and a
            # unit or a scalar with unit and unit group. If no default was
            # specified it will be None.
            _default = weeutil.weeutil.to_list(field_config.get('default', None))
            # create a ValueTuple based on the default
            if _default is None:
                # no default specified so use 0 in output units
                _vt = ValueTuple(0, _group_map[_group], _group)
            elif len(_default) == 1:
                # just a value so use it in output units
                _vt = ValueTuple(float(_default[0]), _group_map[_group], _group)
            elif len(_default) == 2:
                # we have a value and units so use that value in those units
                _vt = ValueTuple(float(_default[0]), _group_map[_group], _default[1])
            elif len(_default) == 3:
                # we already have all the elements of a ValueTuple so no
                # calculations just creating of the ValueTuple object
                _vt = ValueTuple(float(_default[0]), _default[1], _default[2])
            # update the default in the config for this field in the field map,
            # but make sure we update our copy of the field map not the version
            # we aer iterating over
            updated_field_map[field]['default'] = _vt
            # now add in the format to be used but only if it does not exist
            if 'format' not in field_config:
                # we don't have a format so get it from our unit dict
                updated_field_map[field]['format'] = _format_map[_group_map[_group]]
        # finally set our field map property
        self.field_map = updated_field_map

        # get max cache age
        self.max_cache_age = to_int(rtgd_config_dict.get('max_cache_age', 600))

        # initialise last average wind direction
        self.last_average_dir = 0

        # Are we updating windrun using archive data only or archive and loop
        # data?
        self.windrun_loop = to_bool(rtgd_config_dict.get('windrun_loop',
                                                         False))

        # WeeWX does not normally archive appTemp so day stats are not usually
        # available; however, if the user does have appTemp in a database then
        # if we have a binding we can use it. Check if an appTemp binding was
        # specified, if so use it, otherwise default to 'wx_binding'. We will
        # check for data existence before using it.
        self.apptemp_binding = rtgd_config_dict.get('apptemp_binding',
                                                    'wx_binding')

        # Lost contact
        # do we ignore the lost contact 'calculation'
        self.ignore_lost_contact = to_bool(rtgd_config_dict.get('ignore_lost_contact',
                                                                False))
        # set the lost contact flag, assume we start off with contact
        self.lost_contact_flag = False

        # initialise the packet unit dict
        self.packet_unit_dict = None

        # initialise some properties used to hold archive period wind data
        self.windSpeedAvg_vt = ValueTuple(None, 'km_per_hour', 'group_speed')
        self.min_barometer = None
        self.max_barometer = None

        self.db_manager = None
        self.apptemp_manager = None
        self.stats_unit_system = None
        self.day_span = None

        self.packet_cache = None

        self.buffer = None
        self.rose = None
        self.last_rain_ts = None

        # initialise the scroller text
        self.scroller_text = None

        # get some station info
        self.latitude = latitude
        self.longitude = longitude
        self.altitude_m = altitude
        self.station_type = config_dict['Station']['station_type']

        # gauge-data.txt version
        self.version = str(GAUGE_DATA_VERSION)

        # are we providing month and/or year to date rain, default is no we are
        # not
        self.mtd_rain = to_bool(rtgd_config_dict.get('mtd_rain', False))
        self.ytd_rain = to_bool(rtgd_config_dict.get('ytd_rain', False))
        # initialise some properties if we are providing month and/or year to
        # date rain
        if self.mtd_rain:
            self.month_rain = None
        if self.ytd_rain:
            self.year_rain = None

        # obtain an object for exporting gauge-data.txt if required, if export
        # not required property will be set to None
        self.exporter = self.export_factory(rtgd_config_dict,
                                            self.rtgd_path_file)

        # notify the user of a couple of things that we will do
        # frequency of generation
        if self.min_interval is None:
            _msg = "'%s' wil be generated. "\
                       "min_interval is None" % self.rtgd_path_file
        elif self.min_interval == 1:
            _msg = "'%s' will be generated. "\
                       "min_interval is 1 second" % self.rtgd_path_file
        else:
            _msg = "'%s' will be generated. "\
                       "min_interval is %s seconds" % (self.rtgd_path_file,
                                                       self.min_interval)
        log.info(_msg)
        # lost contact
        if self.ignore_lost_contact:
            log.info("Sensor contact state will be ignored")

    @staticmethod
    def export_factory(rtgd_config_dict, rtgd_path_file):
        """Factory method to produce an object to export gauge-data.txt."""

        exporter = None
        # do we have a legacy remote_server_url setting or a HttpPost stanza
        if 'HttpPost' in rtgd_config_dict or 'remote_server_url' in rtgd_config_dict:
            exporter = 'httppost'
        elif 'Rsync' in rtgd_config_dict:
            exporter = 'rsync'
        exporter_class = EXPORTERS.get(exporter) if exporter else None
        if exporter_class is None:
            # We have no exporter specified or otherwise lacking the necessary
            # config. Log this and return None which will result in nothing
            # being exported (only saving of gauge-data.txt locally).
            log.info("gauge-data.txt will not be exported.")
            exporter_object = None
        else:
            # get the exporter object
            exporter_object = exporter_class(rtgd_config_dict, rtgd_path_file)
        return exporter_object

    def run(self):
        """Collect packets from the rtgd queue and manage their processing.

        Now that we are in a thread get a manager for our db so we can
        initialise our forecast and day stats. Once this is done we wait for
        something in the rtgd queue.
        """

        # would normally do this in our objects __init__ but since we are
        # running in a thread we need to wait until the thread is actually
        # running before getting db managers

        try:
            # get a db manager
            self.db_manager = weewx.manager.open_manager(self.manager_dict)
            # get a db manager for appTemp
            self.apptemp_manager = weewx.manager.open_manager_with_config(self.config_dict,
                                                                          self.apptemp_binding)
            # obtain the current day stats so we can initialise a Buffer object
            day_stats = self.db_manager._get_day_summary(time.time())
            # save our day stats unit system for use later
            self.stats_unit_system = day_stats.unit_system
            # obtain the current day stats from our appTemp source so we can
            # initialise a Buffer object
            apptemp_day_stats = self.apptemp_manager._get_day_summary(time.time())
            # get a Buffer object
            self.buffer = Buffer(MANIFEST,
                                 day_stats=day_stats,
                                 additional_day_stats=apptemp_day_stats)

            # initialise the time of last rain
            self.last_rain_ts = self.calc_last_rain_stamp()

            # get a windrose to start with since it is only on receipt of an
            # archive record
            self.rose = calc_windrose(int(time.time()),
                                      self.db_manager,
                                      self.wr_period,
                                      self.wr_points)
            if weewx.debug == 2:
                log.debug("windrose data calculated")
            elif weewx.debug >= 3:
                log.debug("windrose data calculated: %s" % (self.rose,))
            # set up our loop cache and set some starting wind values
            _ts = self.db_manager.lastGoodStamp()
            if _ts is not None:
                _rec = self.db_manager.getRecord(_ts)
            else:
                _rec = {'usUnits': None}
            # get a CachedPacket object as our loop packet cache and prime it with
            # values from the last good archive record if available
            self.packet_cache = CachedPacket(_rec)
            if weewx.debug >= 2:
                log.debug("loop packet cache initialised")
            # save the windSpeed value to use as our archive period average, this
            # needs to be a ValueTuple since we may need to convert units
            if 'windSpeed' in _rec:
                self.windSpeedAvg_vt = weewx.units.as_value_tuple(_rec, 'windSpeed')

            # now run a continuous loop, waiting for records to appear in the rtgd
            # queue then processing them.
            while True:
                # inner loop to monitor the queues
                while True:
                    # If we have a result queue check to see if we have received
                    # any forecast data. Use get_nowait() so we don't block the
                    # rtgd control queue. Wrap in a try..except to catch the error
                    # if there is nothing in the queue.
                    if self.result_queue:
                        try:
                            # use nowait() so we don't block
                            _package = self.result_queue.get_nowait()
                        except queue.Empty:
                            # nothing in the queue so continue
                            pass
                        else:
                            # we did get something in the queue but was it a
                            # 'forecast' package
                            if isinstance(_package, dict):
                                if 'type' in _package and _package['type'] == 'forecast':
                                    # we have forecast text so log and save it
                                    if weewx.debug >= 2:
                                        log.debug("received forecast text: %s" % _package['payload'])
                                    self.scroller_text = _package['payload']
                    # now deal with the control queue
                    try:
                        # block for one second waiting for package, if nothing
                        # received throw queue.Empty
                        _package = self.control_queue.get(True, 1.0)
                    except queue.Empty:
                        # nothing in the queue so continue
                        pass
                    else:
                        # a None record is our signal to exit
                        if _package is None:
                            return
                        elif _package['type'] == 'archive':
                            if weewx.debug == 2:
                                log.debug("received archive record (%s)" % _package['payload']['dateTime'])
                            elif weewx.debug >= 3:
                                log.debug("received archive record: %s" % _package['payload'])
                            self.process_new_archive_record(_package['payload'])
                            self.rose = calc_windrose(_package['payload']['dateTime'],
                                                      self.db_manager,
                                                      self.wr_period,
                                                      self.wr_points)
                            if weewx.debug == 2:
                                log.debug("windrose data calculated")
                            elif weewx.debug >= 3:
                                log.debug("windrose data calculated: %s" % (self.rose,))
                            continue
                        elif _package['type'] == 'stats':
                            if weewx.debug == 2:
                                log.debug("received stats package")
                            elif weewx.debug >= 3:
                                log.debug("received stats package: %s" % _package['payload'])
                            self.process_stats(_package['payload'])
                            continue
                        elif _package['type'] == 'loop':
                            # we now have a packet to process, wrap in a
                            # try..except so we can catch any errors
                            try:
                                if weewx.debug == 2:
                                    log.debug("received loop packet (%s)" % _package['payload']['dateTime'])
                                elif weewx.debug >= 3:
                                    log.debug("received loop packet: %s" % _package['payload'])
                                self.process_packet(_package['payload'])
                                continue
                            except Exception as e:
                                # Some unknown exception occurred. This is probably
                                # a serious problem. Exit.
                                log.critical("Unexpected exception of type %s" % (type(e),))
                                weeutil.logger.log_traceback(log.debug, 'rtgdthread: **** ')
                                log.critical("Thread exiting. Reason: %s" % (e, ))
                                return
                    # if packets have backed up in the control queue, trim it until
                    # it's not bigger than the max allowed backlog
                    while self.control_queue.qsize() > 5:
                        self.control_queue.get()
        except Exception as e:
            # Some unknown exception occurred. This is probably
            # a serious problem. Exit.
            log.critical("Unexpected exception of type %s" % (type(e), ))
            weeutil.logger.log_traceback(log.debug, 'rtgdthread: **** ')
            log.critical("Thread exiting. Reason: %s" % (e, ))
            return

    def process_packet(self, packet):
        """Process incoming loop packets and generate gauge-data.txt.

        Input:
            packet: dict containing the loop packet to be processed
        """

        # get time for debug timing
        t1 = time.time()
        # if we have the first packet from a new day we need to reset the Buffer
        # objects stats
        if self.day_span is not None:
            # we have a day_span so this i snot our first time, check to see if
            # our packet timestamp belongs to the following day
            if packet['dateTime'] > self.day_span.stop:
                # we have a packet from a new day, so reset the Buffer stats
                self.buffer.start_of_day_reset()
                # and reset our day_span
                self.day_span = weeutil.weeutil.archiveDaySpan(packet['dateTime'])
        else:
            # we don't have a day_span, it must be the first packet since we
            # started, so initialise a day_span
            self.day_span = weeutil.weeutil.archiveDaySpan(packet['dateTime'])
        # convert our incoming packet
        _conv_packet = weewx.units.to_std_system(packet,
                                                 self.stats_unit_system)
        # update the packet cache with this packet
        self.packet_cache.update(_conv_packet, _conv_packet['dateTime'])
        # update the buffer with the converted packet
        self.buffer.add_packet(_conv_packet)
        # generate if we have no minimum interval setting or if minimum
        # interval seconds have elapsed since our last generation
        if self.min_interval is None or (self.last_write + float(self.min_interval)) < time.time():
            # get a cached packet
            cached_packet = self.packet_cache.get_packet(_conv_packet['dateTime'],
                                                         self.max_cache_age)
            if weewx.debug == 2:
                log.debug("created cached loop packet (%s)" % cached_packet['dateTime'])
            elif weewx.debug >= 3:
                log.debug("created cached loop packet: %s" % (cached_packet,))
            # set our lost contact flag if applicable
            self.lost_contact_flag = self.get_lost_contact(cached_packet, 'loop')
            # get a data dict from which to construct our file
            try:
                data = self.calculate(cached_packet)
            except Exception as e:
                weeutil.logger.log_traceback(log.info, 'rtgdthread: **** ')
            else:
                # write to our file
                try:
                    self.write_data(data)
                except Exception as e:
                    weeutil.logger.log_traceback(log.info, 'rtgdthread: **** ')
                else:
                    # set our write time
                    self.last_write = time.time()
                    # export gauge-data.txt if we have an exporter object
                    if self.exporter:
                        self.exporter.export(data, packet['dateTime'])
                    # log the generation
                    if weewx.debug == 2:
                        log.info("gauge-data.txt (%s) generated in %.5f seconds" % (cached_packet['dateTime'],
                                                                                    (self.last_write - t1)))
        else:
            # we skipped this packet so log it
            if weewx.debug == 2:
                log.debug("packet (%s) skipped" % _conv_packet['dateTime'])

    def process_stats(self, package):
        """Process a stats package.

        Input:
            package: dict containing the stats data to process
        """

        if package is not None:
            for key, value in package.items():
                setattr(self, key, value)

    def write_data(self, data):
        """Write the gauge-data.txt file.

        Takes dictionary of data elements, converts them to JSON format and
        writes them to file. JSON output is sorted by key and any non-critical
        whitespace removed before being written to file. An atomic write to
        file is used to lessen chance of rtgd/web server file access conflict.
        Destination directory is created if it does not exist.

        Inputs:
            data: dictionary of gauge-data.txt data elements
        """

        # make the destination directory, wrapping it in a try block to catch
        # any errors
        try:
            os.makedirs(self.rtgd_path)
        except OSError as error:
            # raise if the error is anything other than the dir already exists
            if error.errno != errno.EEXIST:
                raise
        # now write to temporary file
        with open(self.rtgd_path_file_tmp, 'w') as f:
            json.dump(data, f, separators=(',', ':'), sort_keys=True)
        # and copy the temporary file to our destination
        os.rename(self.rtgd_path_file_tmp, self.rtgd_path_file)

    def get_field_value(self, field, packet):
        """Obtain the value for an output field.

        Obtain the field value given using the field map entry for the field.
        Results are unit converted and formatted as per the field map.

        A limited set of aggregates is supported for each observation. Some
        aggregates support a limited range of aggregate periods. Details on
        each aggregate are provided below:
            min. Minimum value of an observation over the aggregate period.
                 Supported aggregate periods are:
                    day. The minimum value seen so far today.
                    xxx. The minimum value seen in the last xxx seconds where
                         xxx is a number in seconds (up to the maximum buffer
                         history size - nominally 600 seconds).
            mintime. The time of the minimum value. Aggregate periods supported
                     are as for min.
            max. Maximum value of an observation over the aggregate period. 
                 Supported aggregate periods are:
                    day. The maximum value seen so far today.
                    xxx. The maximum value seen in the last xxx seconds where
                         xxx is a number in seconds (up to the maximum buffer
                         history size - nominally 600 seconds).
            mintime. The time of the maximum value. Aggregate periods supported
                     are as for max.
            sum: The sum of the values seen so far today.
            last: The last value seen. Aggregate period is not applicable.
            lasttime: The time of the last value seen. Aggregate period is not
                      applicable.
            trend: The difference in value over the aggregate period. Aggregate
                   period is a number in seconds (up to the maximum buffer
                   history size - nominally 600 seconds).
            count: The number of non-None values over the aggregate period.
                   Aggregate period is a number in seconds (up to the maximum
                   buffer history size - nominally 600 seconds).
            maxdir: For vector observations (eg 'wind') the direction at the
                    time the maximum value was seen today.
            vecavg: For vector observations (eg 'wind') the vector average 
                    magnitude of an observation over the aggregate period. 
                    Supported aggregate periods are:
                    day. The vector average magnitude so far today.
                    xxx. The vector average magnitude over the last xxx seconds 
                         where xxx is a number in seconds (up to the maximum 
                         buffer history size - nominally 600 seconds).
            vecdir: For vector observations (eg 'wind') the vector average 
                    direction of an observation over the aggregate period. 
                    Supported aggregate periods are:
                    day. The vector average direction so far today.
                    xxx. The vector average direction over the last xxx seconds 
                         where xxx is a number in seconds (up to the maximum 
                         buffer history size - nominally 600 seconds).
        """

        # prime our result
        result = None
        # get the map for this field
        this_field_map = self.field_map.get(field)
        # do we know about this field and do we have a source?
        if this_field_map is not None and this_field_map.get('source') is not None:
            # we have a source
            source = this_field_map['source']
            # get a few things about our result:
            # unit group
            result_group = this_field_map['group'] if 'group' in this_field_map \
                else self.get_unit_group(source, this_field_map.get('aggregate'))
            # result units
            result_units = self.group_map[result_group]
            # initialise agg to None
            agg = None
            # do we have an aggregate
            if this_field_map.get('aggregate') is not None:
                # we have an aggregate
                agg = this_field_map['aggregate'].lower()
                _agg_period = this_field_map.get('aggregate_period')
                try:
                    aggregate_period = int(_agg_period)
                except (TypeError, ValueError):
                    # Likely we encountered None (TypeError) or a string that
                    # could not be converted to an int (ValueError). In either
                    # case set aggregate_period to None.
                    aggregate_period = None
                # obtain the raw aggregate value, any unit conversion and
                # formatting will be done later
                if agg == 'trend':
                    # if no aggregate period was specified default to 3600 seconds
                    trend_period = aggregate_period if aggregate_period is not None else 3600
                    # the largest difference in time that is acceptable when
                    # finding the historical record for calculating the trend
                    grace_period = int(this_field_map.get('grace', 300))
                    # obtain the current value as a ValueTuple
                    _current_vt = as_value_tuple(packet, source)
                    # calculate the trend, no need to convert the result as
                    # calc_trend() does that
                    _result = calc_trend(obs_type=source,
                                         now_vt=_current_vt,
                                         target_units=result_units,
                                         db_manager=self.db_manager,
                                         then_ts=packet['dateTime'] - trend_period,
                                         grace=grace_period)
                elif agg == 'maxdir':
                    # only applicable to vectors, so we need to be prepared to
                    # handle an AttributeError if we have a scalar obs
                    # try to get the maxdir attribute for the field, no need
                    # for unit conversion
                    try:
                        _result = getattr(self.buffer[source], agg)
                    except AttributeError:
                        # maxdir attribute does not exist, set the result to
                        # None
                        _result = None
                elif agg == 'vecavg':
                    # only applicable to vectors, so we need to be prepared to
                    # handle an AttributeError if we have a scalar obs
                    # Try to get the applicable attribute, which attribute is
                    # used depends on the aggregate period. Note that unit
                    # conversion is needed.
                    try:
                        if aggregate_period == 'day':
                            # we are after a 'day' value, so we need the
                            # mag property of the day_vec_avg property of the
                            # vector buffer
                            _res = getattr(self.buffer[source], 'day_vec_avg').mag
                        else:
                            # we are after some other aggregate period so look
                            # in our buffers history by calling the
                            # history_vec_avg() function with the aggregate
                            # period as an argument
                            _res = getattr(self.buffer[source], 'history_vec_avg')(int(aggregate_period)).mag
                        _res_vt = ValueTuple(_res,
                                             self.packet_unit_dict[source]['units'],
                                             self.packet_unit_dict[source]['group'])
                        # convert to the output units
                        _result = convert(_res_vt, result_units).value
                    except (AttributeError, TypeError):
                        # either the attribute does not exist or we have an
                        # unsupported aggregate period, either set the result
                        # to None
                        _result = None
                elif agg == 'vecdir':
                    # only applicable to vectors, so we need to be prepared to
                    # handle an AttributeError if we have a scalar obs
                    # as the result is a direction (or None) there is no need
                    # for unit conversion
                    try:
                        if aggregate_period == 'day':
                            # we are after a 'day' value so we need the
                            # dir property of the day_vec_avg property of the
                            # vector buffer
                            _result = getattr(self.buffer[source], 'day_vec_avg').dir
                        else:
                            # we are after some other aggregate period so look
                            # in our buffers history by calling the
                            # history_vec_avg() function with the aggregate
                            # period as an argument
                            _result = getattr(self.buffer[source], 'history_vec_avg')(int(aggregate_period)).dir
                    except (AttributeError, TypeError):
                        # either the attribute does not exist or we have an
                        # unsupported aggregate period, either set the result
                        # to None
                        _result = None
                elif agg in ('min', 'max', 'last', 'sum'):
                    # these aggregates may need unit conversion so obtain a
                    # ValueTuple and convert as required
                    _result_vt = ValueTuple(getattr(self.buffer[source], agg),
                                            self.packet_unit_dict[source]['units'],
                                            self.packet_unit_dict[source]['group'])
                    # convert to the output units
                    _result = convert(_result_vt, result_units).value
                elif agg in ('mintime', 'maxtime', 'lasttime'):
                    # it's a time so get the time as a localtime
                    _result = time.localtime(getattr(self.buffer[source], agg))
                elif agg == 'count':
                    # it's a count so just get the value
                    _result = getattr(self.buffer[source], agg)
            else:
                # there is no aggregate so just get the value from the packet
                # and convert as required
                if source in packet:
                    # the data is in the packet so get it as a ValueTuple
                    # because we will be converting it
                    _raw_vt = as_value_tuple(packet, source)
                    # obtain the converted value
                    _result = convert(_raw_vt, result_units).value
                else:
                    # the data is not in the packet, so use None
                    _result = None
            if _result is not None:
                # we have a non-None result so just format it
                # if we have an aggregate that returned a 'time' it needs
                # special treatment
                if agg in ('mintime', 'maxtime', 'lasttime'):
                    result = time.strftime(this_field_map['format'], _result)
                else:
                    result = this_field_map['format'] % _result
            else:
                # we have a None result, look for a default
                if 'default' in this_field_map:
                    # we have a default, defaults are already a ValueTuple so we can just use it as is
                    _conv_default = weewx.units.convert(this_field_map['default'],
                                                        result_units).value
                    result = this_field_map['format'] % _conv_default
                else:
                    # we do not have a default so use None
                    result = None
        return result

    @staticmethod
    def get_unit_group(obs_type, agg_type=None):
        """Determine the unit group of an observation and aggregation type.

        WeeWX provides a similar function, but it does not support all
        aggregates used by RTGD. Check for and handle these aggregates
        separately, otherwise call the WeeWX function for everything else.
        """

        if agg_type == 'maxdir':
            return 'group_direction'
        else:
            return weewx.units.getUnitGroup(obs_type, agg_type)

    def get_packet_units(self, packet):
        """Given a packet obtain unit details for each field map source."""

        packet_unit_dict = {}
        packet_unit_system = packet['usUnits']
        for field, field_map in self.field_map.items():
            source = field_map['source']
            if source not in packet_unit_dict:
                (units, unit_group) = getStandardUnitType(packet_unit_system,
                                                          source)
                packet_unit_dict[source] = {'units': units,
                                            'group': unit_group}
        # add in units and group details for fields windSpeed and rain to
        # facilitate non-field map based field calculations
        for source in ('windSpeed', 'rain'):
            if source not in packet_unit_dict:
                (units, unit_group) = getStandardUnitType(packet_unit_system,
                                                          source)
                packet_unit_dict[source] = {'units': units,
                                            'group': unit_group}
        return packet_unit_dict

    def calculate(self, packet):
        """Construct a data dict for gauge-data.txt.

        Input:
            packet: loop data packet

        Returns:
            Dictionary of gauge-data.txt data elements.
        """

        # obtain the timestamp for the current packet
        ts = packet['dateTime']
        # obtain a dict of units and unit group for each source in the field map
        self.packet_unit_dict = self.get_packet_units(packet)
        # construct a dict to hold our results
        data = dict()

        # obtain 10-minute average wind direction
        avg_bearing_10 = self.buffer['wind'].history_vec_avg(period=600).dir

        # First we populate all non-field map calculated fields and then
        # iterate over the field map populating the field map based fields.
        # Populating the fields in this order allows the user to override the
        # content of a non-field map based field (eg 'rose').

        # timeUTC - UTC date/time in format YYYY,mm,dd,HH,MM,SS
        data['timeUTC'] = datetime.datetime.utcfromtimestamp(ts).strftime("%Y,%m,%d,%H,%M,%S")
        # date and time - date and time must be space separated
        data['date'] = ' '.join([time.strftime(self.date_format, time.localtime(ts)),
                                 time.strftime(self.time_format, time.localtime(ts))])
        # dateFormat - date format
        data['dateFormat'] = self.date_format.replace('%', '').replace('-', '').lower()
        # SensorContactLost - 1 if the station has lost contact with its remote
        # sensors "Fine Offset only" 0 if contact has been established
        data['SensorContactLost'] = self.flag_format % self.lost_contact_flag
        # tempunit - temperature units - C, F
        data['tempunit'] = UNITS_TEMP[self.group_map['group_temperature']]
        # windunit -wind units - m/s, mph, km/h, kts
        data['windunit'] = UNITS_WIND[self.group_map['group_speed']]
        # pressunit - pressure units - mb, hPa, in
        data['pressunit'] = UNITS_PRES[self.group_map['group_pressure']]
        # rainunit - rain units - mm, in
        data['rainunit'] = UNITS_RAIN[self.group_map['group_rain']]
        # cloudbaseunit - cloud base units - m, ft
        data['cloudbaseunit'] = UNITS_CLOUD[self.group_map['group_altitude']]

        # TODO. pressL and pressH need to be refactored to use a field map
        # pressL - all time low barometer
        if self.min_barometer is not None:
            press_l_vt = ValueTuple(self.min_barometer,
                                    self.packet_unit_dict['barometer']['units'],
                                    self.packet_unit_dict['barometer']['group'])
        else:
            press_l_vt = ValueTuple(850, 'hPa', self.packet_unit_dict['barometer']['group'])
        press_l = convert(press_l_vt, self.group_map['group_pressure']).value
        data['pressL'] = self.format_map[self.group_map['group_pressure']] % press_l
        # pressH - all-time high barometer
        if self.max_barometer is not None:
            press_h_vt = ValueTuple(self.max_barometer,
                                    self.packet_unit_dict['barometer']['units'],
                                    self.packet_unit_dict['barometer']['group'])
        else:
            press_h_vt = ValueTuple(1100, 'hPa', self.packet_unit_dict['barometer']['group'])
        press_h = convert(press_h_vt, self.group_map['group_pressure']).value
        data['pressH'] = self.format_map[self.group_map['group_pressure']] % press_h

        # domwinddir - Today's dominant wind direction as compass point
        dom_dir = self.buffer['wind'].day_vec_avg.dir
        data['domwinddir'] = degree_to_compass(dom_dir)

        # WindRoseData -
        data['WindRoseData'] = self.rose

        # hourlyrainTH - Today's highest hourly rain
        # FIXME. Need to determine hourlyrainTH
        data['hourlyrainTH'] = "0.0"

        # ThourlyrainTH - time of Today's highest hourly rain
        # FIXME. Need to determine ThourlyrainTH
        data['ThourlyrainTH'] = "00:00"

        # LastRainTipISO - date and time of last rainfall
        if self.last_rain_ts is not None:
            _last_rain_tip_iso = time.strftime(' '.join([self.date_format, self.time_format]),
                                               time.localtime(self.last_rain_ts))
        else:
            _last_rain_tip_iso = "1/1/1900 00:00"
        data['LastRainTipISO'] = _last_rain_tip_iso

        # wspeed - wind speed (average)
        # obtain the average wind speed from the buffer
        _speed = self.buffer['windSpeed'].history_avg(ts=ts, age=600)
        _wspeed = _speed if _speed is not None else 0.0
        # put into a ValueTuple so we can convert
        wspeed_vt = ValueTuple(_wspeed,
                               self.packet_unit_dict['windSpeed']['units'],
                               self.packet_unit_dict['windSpeed']['group'])
        # convert to output units
        wspeed = convert(wspeed_vt, self.group_map['group_speed']).value
        # handle None values
        wspeed = wspeed if wspeed is not None else 0.0
        data['wspeed'] = self.format_map[self.group_map['group_speed']] % wspeed

        # wgust - 10 minute high gust
        # first look for max windGust value in the history, if windGust is not
        # in the buffer then use windSpeed, if no windSpeed then use 0.0
        if 'windGust' in self.buffer:
            _gust = self.buffer['windGust'].history_max(ts, age=600)
        elif 'windSpeed' in self.buffer:
            _gust = self.buffer['windSpeed'].history_max(ts, age=600)
        else:
            _gust = ObsTuple(None, None)
        wgust = _gust.value if _gust.value is not None else 0.0
        # put into a ValueTuple so we can convert
        wgust_vt = ValueTuple(wgust,
                              self.packet_unit_dict['windSpeed']['units'],
                              self.packet_unit_dict['windSpeed']['group'])
        # convert to output units
        wgust = convert(wgust_vt, self.group_map['group_speed']).value
        data['wgust'] = self.format_map[self.group_map['group_speed']] % wgust

        # BearingRangeFrom10 - The 'lowest' bearing in the last 10 minutes
        # BearingRangeTo10 - The 'highest' bearing in the last 10 minutes
        # (or as configured using AvgBearingMinutes in cumulus.ini), rounded
        # down to nearest 10 degrees
        if avg_bearing_10 is not None:
            # First obtain a list of wind direction history over the last
            # 10 minutes, but we want the direction to be in -180 to
            # 180 degrees range rather than from 0 to 360 degrees. Also, the
            # values must be relative to the 10-minute average wind direction.
            # Wrap in a try.except just in case.
            try:
                _offset_dir = [self.to_plusminus(obs.value.dir-avg_bearing_10) for obs in self.buffer['wind'].history]
            except (TypeError, ValueError):
                # if we strike an error then return 0 for both results
                bearing_range_from_10 = 0
                bearing_range_to_10 = 0
            # Now find the min and max values and transpose back to the 0 to
            # 360 degrees range relative to North (0 degrees). Wrap in a
            # try..except just in case.
            try:
                bearing_range_from_10 = self.to_threesixty(min(_offset_dir) + avg_bearing_10)
                bearing_range_to_10 = self.to_threesixty(max(_offset_dir) + avg_bearing_10)
            except TypeError:
                # if we strike an error then return 0 for both results
                bearing_range_from_10 = 0
                bearing_range_to_10 = 0
        else:
            bearing_range_from_10 = 0
            bearing_range_to_10 = 0
        # store the formatted results
        data['BearingRangeFrom10'] = self.format_map[self.group_map['group_direction']] % bearing_range_from_10
        data['BearingRangeTo10'] = self.format_map[self.group_map['group_direction']] % bearing_range_to_10

        # forecast - forecast text
        _text = self.scroller_text if self.scroller_text is not None else ''
        # format the forecast string, we might get a UnicodeDecode error, be
        # prepared to catch it
        try:
            data['forecast'] = time.strftime(_text, time.localtime(ts))
        except UnicodeEncodeError:
            # FIXME. Possible unicode/bytes issue
            data['forecast'] = time.strftime(_text.encode('ascii', 'ignore'), time.localtime(ts))
        # version - weather software version
        data['version'] = '%s' % weewx.__version__
        # build -
        data['build'] = ''
        # ver - gauge-data.txt version number
        data['ver'] = self.version
        # month to date rain, only calculate if we have been asked
        # TODO. Check this, particularly usage of buffer['rain'].sum
        if self.mtd_rain:
            if self.month_rain is not None:
                rain_m = convert(self.month_rain, self.group_map['group_rain']).value
                rain_b_vt = ValueTuple(self.buffer['rain'].sum,
                                       self.packet_unit_dict['rain']['units'],
                                       self.packet_unit_dict['rain']['group'])
                rain_b = convert(rain_b_vt, self.group_map['group_rain']).value
                if rain_m is not None and rain_b is not None:
                    rain_m = rain_m + rain_b
                else:
                    rain_m = 0.0
            else:
                rain_m = 0.0
            data['mrfall'] = self.format_map[self.group_map['group_rain']] % rain_m
        # year to date rain, only calculate if we have been asked
        # TODO. Check this, particularly usage of buffer['rain'].sum
        if self.ytd_rain:
            if self.year_rain is not None:
                rain_y = convert(self.year_rain, self.group_map['group_rain']).value
                rain_b_vt = ValueTuple(self.buffer['rain'].sum,
                                       self.packet_unit_dict['rain']['units'],
                                       self.packet_unit_dict['rain']['group'])
                rain_b = convert(rain_b_vt, self.group_map['group_rain']).value
                if rain_y is not None and rain_b is not None:
                    rain_y = rain_y + rain_b
                else:
                    rain_y = 0.0
            else:
                rain_y = 0.0
            data['yrfall'] = self.format_map[self.group_map['group_rain']] % rain_y

        # now populate all fields in the field map
        for field in self.field_map:
            data[field] = self.get_field_value(field, packet)
        return data

    def process_new_archive_record(self, record):
        """Control processing when a new archive record is presented."""

        # set our lost contact flag if applicable
        self.lost_contact_flag = self.get_lost_contact(record, 'archive')
        # save the windSpeed value to use as our archive period average
        if 'windSpeed' in record:
            self.windSpeedAvg_vt = weewx.units.as_value_tuple(record, 'windSpeed')
        else:
            self.windSpeedAvg_vt = ValueTuple(None, 'km_per_hour', 'group_speed')

    def calc_last_rain_stamp(self):
        """Calculate the timestamp of the last rain.

        Searching a large archive for the last rainfall could be
        time-consuming, so first search the daily summaries for the day of last
        rain and then search that day for the actual timestamp.
        """

        _row = self.db_manager.getSql("SELECT MAX(dateTime) FROM archive_day_rain WHERE sum > 0")
        last_rain_ts = _row[0]
        # now limit our search on the archive to the day concerned, wrap in a
        # try statement just in case
        if last_rain_ts is not None:
            # We have a day so get a TimeSpan for the day containing
            # last_rain_ts. last_rain_ts will be set to midnight at the start
            # of a day (daily summary requirement) but in the archive this ts
            # would belong to the previous day, so add 1 second and obtain the
            # TimeSpan for the archive day containing that ts.
            last_rain_tspan = weeutil.weeutil.archiveDaySpan(last_rain_ts+1)
            try:
                _row = self.db_manager.getSql("SELECT MAX(dateTime) FROM archive "
                                              "WHERE rain > 0 AND dateTime > ? AND dateTime <= ?",
                                              last_rain_tspan)
                last_rain_ts = _row[0]
            except (IndexError, TypeError):
                last_rain_ts = None
        return last_rain_ts

    def get_lost_contact(self, rec, packet_type):
        """Determine is station has lost contact with sensors."""

        # default to lost contact = False
        result = False
        # if we are not ignoring the lost contact test do the check
        if not self.ignore_lost_contact:
            if ((packet_type == 'loop' and self.station_type in LOOP_STATIONS) or
                    (packet_type == 'archive' and self.station_type in ARCHIVE_STATIONS)):
                _v = STATION_LOST_CONTACT[self.station_type]['value']
                try:
                    result = rec[STATION_LOST_CONTACT[self.station_type]['field']] == _v
                except KeyError:
                    log.debug("KeyError: Could not determine sensor contact state")
                    result = True
        return result

    @staticmethod
    def to_plusminus(val):
        """Map a 0 to 360 degree direction to -180 to +180 degrees."""

        if val is not None and val > 180:
            return val - 360
        else:
            return val

    @staticmethod
    def to_threesixty(val):
        """Map a -180 to +180 degrees direction to 0 to 360 degrees."""

        if val is not None and val < 0:
            return val + 360
        else:
            return val


# ============================================================================
#                           class ObsBuffer
# ============================================================================

class ObsBuffer(object):
    """Base class to buffer an obs."""

    def __init__(self, stats, units=None, history=False):
        self.units = units
        self.last = None
        self.lasttime = None
        if history:
            self.use_history = True
            self.history_full = False
            self.history = []
        else:
            self.use_history = False

    def add_value(self, val, ts, hilo=True):
        """Add a value to my hilo and history stats as required."""

        pass

    def day_reset(self):
        """Reset the vector obs buffer."""

        pass

    def trim_history(self, ts):
        """Trim any old data from the history list."""

        # calc ts of the oldest sample we want to retain
        oldest_ts = ts - MAX_AGE
        # set history_full property
        self.history_full = min([a.ts for a in self.history if a.ts is not None]) <= oldest_ts
        # remove any values older than oldest_ts
        self.history = [s for s in self.history if s.ts > oldest_ts]

    def history_max(self, ts, age=MAX_AGE):
        """Return the max value in my history.

        Search the last age seconds of my history for the max value and the
        corresponding timestamp.

        Inputs:
            ts:  the timestamp to start searching back from
            age: the max age of the records being searched

        Returns:
            An object of type ObsTuple where value is a 3 way tuple of
            (value, x component, y component) and ts is the timestamp when
            it occurred.
        """

        born = ts - age
        snapshot = [a for a in self.history if a.ts >= born]
        if len(snapshot) > 0:
            _max = max(snapshot, key=itemgetter(1))
            return ObsTuple(_max[0], _max[1])
        else:
            return ObsTuple(None, None)

    def history_avg(self, ts, age=MAX_AGE):
        """Return the average value in my history.

        Search the last age seconds of my history for the max value and the
        corresponding timestamp.

        Inputs:
            ts:  the timestamp to start searching back from
            age: the max age of the records being searched

        Returns:
            An object of type ObsTuple where value is a 3 way tuple of
            (value, x component, y component) and ts is the timestamp when
            it occurred.
        """

        born = ts - age
        snapshot = [a.value for a in self.history if a.ts >= born]
        if len(snapshot) > 0:
            return float(sum(snapshot)/len(snapshot))
        else:
            return None


# ============================================================================
#                             class VectorBuffer
# ============================================================================

class VectorBuffer(ObsBuffer):
    """Class to buffer vector obs."""

    default_init = (None, None, None, None, None, 0.0, 0.0, 0.0, 0.0, 0)

    def __init__(self, stats, units=None, history=False):
        # initialize my superclass
        super(VectorBuffer, self).__init__(stats, units=units, history=history)

        if stats:
            self.min = stats.min
            self.mintime = stats.mintime
            self.max = stats.max
            self.maxdir = stats.max_dir
            self.maxtime = stats.maxtime
            self.sum = stats.sum
            self.xsum = stats.xsum
            self.ysum = stats.ysum
            self.sumtime = stats.sumtime
            self.count = stats.count
        else:
            (self.min, self.mintime,
             self.max, self.maxdir,
             self.maxtime, self.sum,
             self.xsum, self.ysum,
             self.sumtime, self.count) = VectorBuffer.default_init

    def add_value(self, val, ts, hilo=True):
        """Add a value to my hilo and history stats as required."""

        if val.mag is not None:
            if hilo:
                if self.min is None or val.mag < self.min:
                    self.min = val.mag
                    self.mintime = ts
                if self.max is None or val.mag > self.max:
                    self.max = val.mag
                    self.maxdir = val.dir
                    self.maxtime = ts
            self.sum += val.mag
            if self.lasttime:
                self.sumtime += ts - self.lasttime
            if val.dir is not None:
                self.xsum += val.mag * math.cos(math.radians(90.0 - val.dir))
                self.ysum += val.mag * math.sin(math.radians(90.0 - val.dir))
            if self.lasttime is None or ts >= self.lasttime:
                self.last = val
                self.lasttime = ts
            self.count += 1
            if self.use_history and val.dir is not None:
                self.history.append(ObsTuple(val, ts))
                self.trim_history(ts)

    def day_reset(self):
        """Reset the vector obs buffer."""

        (self.min, self.mintime,
         self.max, self.maxdir,
         self.maxtime, self.sum,
         self.xsum, self.ysum,
         self.sumtime, self.count) = VectorBuffer.default_init

    @property
    def day_vec_avg(self):
        """The day average vector.

        Returns a VectorTuple. Direction is in the range >=0 to <360 degrees.
        """

        try:
            _magnitude = math.sqrt((self.xsum**2 + self.ysum**2) / self.sumtime**2)
        except ZeroDivisionError:
            return VectorTuple(0.0, 0.0)
        _direction = 90.0 - math.degrees(math.atan2(self.ysum, self.xsum))
        _direction = _direction if _direction >= 0.0 else _direction + 360.0
        return VectorTuple(_magnitude, _direction)

    def history_vec_avg(self, period=0):
        """The history average vector.

        The period over which the average is calculated is the history
        retention period (nominally 10 minutes).
        """

        # TODO. Check the maths here, time ?
        result = VectorTuple(None, None)
        if self.use_history:
            since_ts = time.time() - period
            history_vec = [ob for ob in self.history if ob.ts > since_ts]
            if len(history_vec) > 0:
                xy = [(ob.value.mag * math.cos(math.radians(90.0 - ob.value.dir)),
                       ob.value.mag * math.sin(math.radians(90.0 - ob.value.dir))) for ob in history_vec]
                xsum = sum(x for x, y in xy)
                ysum = sum(y for x, y in xy)
                oldest_ts = min(ob.ts for ob in history_vec)
                _magnitude = math.sqrt((xsum**2 + ysum**2) / (time.time() - oldest_ts)**2)
                _direction = 90.0 - math.degrees(math.atan2(ysum, xsum))
                _direction = _direction if _direction >= 0.0 else _direction + 360.0
                result = VectorTuple(_magnitude, _direction)
        return result


# ============================================================================
#                             class ScalarBuffer
# ============================================================================

class ScalarBuffer(ObsBuffer):
    """Class to buffer scalar obs."""

    default_init = (None, None, None, None, 0.0, 0)

    def __init__(self, stats, units=None, history=False):
        # initialize my superclass
        super(ScalarBuffer, self).__init__(stats, units=units, history=history)

        if stats:
            self.min = stats.min
            self.mintime = stats.mintime
            self.max = stats.max
            self.maxtime = stats.maxtime
            self.sum = stats.sum
            self.count = stats.count
        else:
            (self.min, self.mintime,
             self.max, self.maxtime,
             self.sum, self.count) = ScalarBuffer.default_init

    def add_value(self, val, ts, hilo=True):
        """Add a value to my stats as required."""

        if val is not None:
            if hilo:
                if self.min is None or val < self.min:
                    self.min = val
                    self.mintime = ts
                if self.max is None or val > self.max:
                    self.max = val
                    self.maxtime = ts
            self.sum += val
            if self.lasttime is None or ts >= self.lasttime:
                self.last = val
                self.lasttime = ts
            self.count += 1
            if self.use_history:
                self.history.append(ObsTuple(val, ts))
                self.trim_history(ts)

    def day_reset(self):
        """Reset the scalar obs buffer."""

        (self.min, self.mintime,
         self.max, self.maxtime,
         self.sum, self.count) = ScalarBuffer.default_init


# ============================================================================
#                               class Buffer
# ============================================================================

class Buffer(dict):
    """Class to buffer various loop packet obs.

    If archive based stats are an efficient means of getting stats for today.
    However, their use would mean that any daily stat (eg today's max outTemp)
    that 'occurs' after the most recent archive record but before the next
    archive record is written to archive will not be captured. For this reason
    selected loop data is buffered to ensure that such stats are correctly
    reflected.
    """

    def __init__(self, manifest, day_stats, additional_day_stats):
        """Initialise an instance of our class."""

        self.manifest = manifest
        # seed our buffer objects from day_stats
        for obs in [f for f in day_stats if f in self.manifest]:
            seed_func = seed_functions.get(obs, Buffer.seed_scalar)
            seed_func(self, day_stats, obs, history=obs in HIST_MANIFEST)
        # seed our buffer objects from additional_day_stats
        if additional_day_stats:
            for obs in [f for f in additional_day_stats if f in self.manifest]:
                if obs not in self:
                    seed_func = seed_functions.get(obs, Buffer.seed_scalar)
                    seed_func(self, additional_day_stats, obs,
                              history=obs in HIST_MANIFEST)
        # timestamp of the last packet containing windSpeed, used for windrun
        # calcs
        self.last_windSpeed_ts = None

    def seed_scalar(self, stats, obs_type, history):
        """Seed a scalar buffer."""

        self[obs_type] = init_dict.get(obs_type, ScalarBuffer)(stats=stats[obs_type],
                                                               units=stats.unit_system,
                                                               history=history)

    def seed_vector(self, stats, obs_type, history):
        """Seed a vector buffer."""

        self[obs_type] = init_dict.get(obs_type, VectorBuffer)(stats=stats[obs_type],
                                                               units=stats.unit_system,
                                                               history=history)

    def add_packet(self, packet):
        """Add a packet to the buffer."""

        if packet['dateTime'] is not None:
            for obs in [f for f in packet if f in self.manifest]:
                add_func = add_functions.get(obs, Buffer.add_value)
                add_func(self, packet, obs)

    def add_value(self, packet, obs):
        """Add a value to the buffer."""

        # if we haven't seen this obs before add it to our buffer
        if obs not in self:
            self[obs] = init_dict.get(obs, ScalarBuffer)(stats=None,
                                                         units=packet['usUnits'],
                                                         history=obs in HIST_MANIFEST)
        if self[obs].units == packet['usUnits']:
            _value = packet[obs]
        else:
            (unit, group) = getStandardUnitType(packet['usUnits'], obs)
            _vt = ValueTuple(packet[obs], unit, group)
            _value = weewx.units.convertStd(_vt, self[obs].units).value
        self[obs].add_value(_value, packet['dateTime'])

    def add_wind_value(self, packet, obs):
        """Add a wind value to the buffer."""

        # first add it as a scalar
        self.add_value(packet, obs)

        # if there is no windrun in the packet and if obs is windSpeed then we
        # can use windSpeed to update windrun
        if 'windrun' not in packet and obs == 'windSpeed':
            # has windrun been seen before, if not add it to the Buffer
            if 'windrun' not in self:
                self['windrun'] = init_dict.get(obs, ScalarBuffer)(stats=None,
                                                                   units=packet['usUnits'],
                                                                   history=obs in HIST_MANIFEST)
            # to calculate windrun we need a speed over a period of time, are
            # we able to calculate the length of the time period?
            if self.last_windSpeed_ts is not None:
                windrun = self.calc_windrun(packet)
                self['windrun'].add_value(windrun, packet['dateTime'])
            self.last_windSpeed_ts = packet['dateTime']

        # now add it as the special vector 'wind'
        if obs == 'windSpeed':
            if 'wind' not in self:
                self['wind'] = VectorBuffer(stats=None, units=packet['usUnits'])
            if self['wind'].units == packet['usUnits']:
                _value = packet['windSpeed']
            else:
                (unit, group) = getStandardUnitType(packet['usUnits'], 'windSpeed')
                _vt = ValueTuple(packet['windSpeed'], unit, group)
                _value = weewx.units.convertStd(_vt, self['wind'].units).value
            self['wind'].add_value(VectorTuple(_value, packet.get('windDir')),
                                   packet['dateTime'])

    def start_of_day_reset(self):
        """Reset our buffer stats at the end of an archive period.

        Reset our hi/lo data but don't touch the history, it might need to be
        kept longer than the end of the archive period.
        """

        for obs in self.manifest:
            self[obs].day_reset()

    def calc_windrun(self, packet):
        """Calculate windrun given windSpeed."""

        val = None
        if packet['usUnits'] == weewx.US:
            val = packet['windSpeed'] * (packet['dateTime'] - self.last_windSpeed_ts) / 3600.0
            unit = 'mile'
        elif packet['usUnits'] == weewx.METRIC:
            val = packet['windSpeed'] * (packet['dateTime'] - self.last_windSpeed_ts) / 3600.0
            unit = 'km'
        elif packet['usUnits'] == weewx.METRICWX:
            val = packet['windSpeed'] * (packet['dateTime'] - self.last_windSpeed_ts)
            unit = 'meter'
        if self['windrun'].units == packet['usUnits']:
            return val
        else:
            _vt = ValueTuple(val, unit, 'group_distance')
            return weewx.units.convertStd(_vt, self['windrun'].units).value


# ============================================================================
#                            Configuration dictionaries
# ============================================================================

init_dict = ListOfDicts({'wind': VectorBuffer})
add_functions = ListOfDicts({'windSpeed': Buffer.add_wind_value})
seed_functions = ListOfDicts({'wind': Buffer.seed_vector})


# ============================================================================
#                              class ObsTuple
# ============================================================================

# An observation during some period can be represented by the value of the
# observation and the time at which it was observed. This can be represented
# in a 2 way tuple called an obs tuple. An obs tuple is useful because its
# contents can be accessed using named attributes.
#
# Item   attribute   Meaning
#    0    value      The observed value eg 19.5
#    1    ts         The epoch timestamp that the value was observed
#                    eg 1488245400
#
# It is valid to have an observed value of None.
#
# It is also valid to have a ts of None (meaning there is no information about
# the time the observation was observed).

class ObsTuple(tuple):

    def __new__(cls, *args):
        return tuple.__new__(cls, args)

    @property
    def value(self):
        return self[0]

    @property
    def ts(self):
        return self[1]


# ============================================================================
#                              class VectorTuple
# ============================================================================

# A vector value can be represented as a magnitude and direction. This can be
# represented in a 2 way tuple called a vector tuple. A vector tuple is useful
# because its contents can be accessed using named attributes.
#
# Item   attribute   Meaning
#    0    mag        The magnitude of the vector
#    1    dir        The direction of the vector in degrees
#
# mag and dir may be None

class VectorTuple(tuple):

    def __new__(cls, *args):
        return tuple.__new__(cls, args)

    @property
    def mag(self):
        return self[0]

    @property
    def dir(self):
        return self[1]


# ============================================================================
#                            Class CachedPacket
# ============================================================================

class CachedPacket(object):
    """Class to cache loop packets.

    The purpose of the cache is to ensure that necessary fields for the
    generation of gauge-data.txt are continuously available on systems whose
    station emits partial packets. The key requirement is that the field
    exists, the value (numerical or None) is handled by method calculate().
    Method calculate() could be refactored to deal with missing fields, but
    this would either result in the gauges dials oscillating when a loop packet
    is missing an essential field, or overly complex code in method calculate()
    if field caching was to occur.

    The cache consists of a dictionary of value, timestamp pairs where
    timestamp is the timestamp of the packet when obs was last seen and value
    is the value of the obs at that time. None values may be cached.

    A cached loop packet may be obtained by calling the get_packet() method.
    """

    # These fields must be available in every loop packet read from the
    # cache.
    OBS = ["cloudbase", "windDir", "windrun", "inHumidity", "outHumidity",
           "barometer", "radiation", "rain", "rainRate", "windSpeed",
           "appTemp", "dewpoint", "heatindex", "humidex", "inTemp",
           "outTemp", "windchill", "UV", "maxSolarRad"]

    def __init__(self, rec):
        """Initialise our cache object.

        The cache needs to be initialised to include all fields required by the
        calculate() method. We could initialise all field values to None
        (calculate() will interpret the None values to be '0' in most cases).
        The result on the gauge display may be misleading. We can get
        ballpark values for all fields by priming them with values from the
        last archive record. As the archive may have many more fields than rtgd
        requires, only prime those fields that rtgd requires.

        This approach does have the drawback that in situations where the
        archive unit system is different to the loop packet unit system the
        entire loop packet will be converted each time the cache is updated.
        This is inefficient.
        """

        self.cache = dict()
        # if we have a dateTime field in our record block use that otherwise
        # use the current system time
        _ts = rec['dateTime'] if 'dateTime' in rec else int(time.time() + 0.5)
        # only prime those fields in CachedPacket.OBS
        for _obs in CachedPacket.OBS:
            if _obs in rec and 'usUnits' in rec:
                # only add a value if it exists and we know what units its in
                self.cache[_obs] = {'value': rec[_obs], 'ts': _ts}
            else:
                # otherwise set it to None
                self.cache[_obs] = {'value': None, 'ts': _ts}
        # set the cache unit system if known
        self.unit_system = rec['usUnits'] if 'usUnits' in rec else None

    def update(self, packet, ts):
        """Update the cache from a loop packet.

        If the loop packet uses a different unit system to that of the cache
        then convert the loop packet before adding it to the cache. Update any
        previously seen cache fields and add any loop fields that have not been
        seen before.
        """

        if self.unit_system is None:
            self.unit_system = packet['usUnits']
        elif self.unit_system != packet['usUnits']:
            packet = weewx.units.to_std_system(packet, self.unit_system)
        for obs in [x for x in packet if x not in ['dateTime', 'usUnits']]:
            if packet[obs] is not None:
                self.cache[obs] = {'value': packet[obs], 'ts': ts}

    def get_value(self, obs, ts, max_age):
        """Get an obs value from the cache.

        Return a value for a given obs from the cache. If the value is older
        than max_age then None is returned.
        """

        if obs in self.cache and ts - self.cache[obs]['ts'] <= max_age:
            return self.cache[obs]['value']
        return None

    def get_packet(self, ts=None, max_age=600):
        """Get a loop packet from the cache.

        Resulting packet may contain None values.
        """

        if ts is None:
            ts = int(time.time() + 0.5)
        packet = {'dateTime': ts, 'usUnits': self.unit_system}
        for obs in self.cache:
            packet[obs] = self.get_value(obs, ts, max_age)
        return packet


# ============================================================================
#                            Utility Functions
# ============================================================================

def degree_to_compass(x):
    """Convert degrees to ordinal compass point.

    Input:
        x: degrees

    Returns:
        Corresponding ordinal compass point from COMPASS_POINTS. Can return
        None.
    """

    if x is None:
        return None
    idx = int((x + 11.25) / 22.5)
    return COMPASS_POINTS[idx]


def calc_trend(obs_type, now_vt, target_units, db_manager, then_ts, grace=0):
    """ Calculate change in an observation over a specified period.

    Inputs:
        obs_type:     database field name of observation concerned
        now_vt:       value of observation now (ie the finishing value)
        target_units: units our returned value must be in
        db_manager:   manager to be used
        then_ts:      timestamp of start of trend period
        grace:        the largest difference in time when finding the then_ts
                      record that is acceptable

    Returns:
        Change in value over trend period. Can be positive, 0, negative or
        None. Result will be in 'target_units' units.
    """

    # if the 'now' value is None return None
    if now_vt.value is None:
        return None
    # get the 'then' record
    then_record = db_manager.getRecord(then_ts, grace)
    # if there is no 'then' record return None
    if then_record is None:
        return None
    else:
        # return None if obs_type is not in the 'then' record, or if it is in
        # the 'then' record but it is None
        if then_record.get(obs_type) is None:
            return None
        else:
            # otherwise calculate the difference between the 'now' and 'then'
            # values but make sure the correct units are used
            then_vt = weewx.units.as_value_tuple(then_record, obs_type)
            now = convert(now_vt, target_units).value
            then = convert(then_vt, target_units).value
            return now - then


def calc_windrose(now, db_manager, period, points):
    """Calculate a SteelSeries Weather Gauges' windrose array.

    Calculate an array representing the 'amount of wind' from each of the 8 or
    16 compass points. The value for each compass point is determined by
    summing the archive windSpeed values for wind from that compass point over
    the period concerned. Resulting values are rounded to one decimal point.

    Inputs:
        db_manager: A manager object for the database to be used.
        period:     Calculate the windrose using the last period (in
                    seconds) of data in the archive.
        points:     The number of compass points to use, normally 8 or 16.

    Return:
        List containing windrose data with 'points' elements.
    """

    # initialise our result
    rose = [0.0 for x in range(points)]
    # get the earliest ts we will use
    ts = now - period
    # determine the factor to be used to divide numerical windDir into
    # cardinal/ordinal compass points
    angle = 360.0/points
    # create an interpolation dict for our query
    inter_dict = {'table_name': db_manager.table_name,
                  'ts': ts,
                  'angle': angle}
    # the query to be used
    windrose_sql = "SELECT ROUND(windDir/%(angle)s),sum(windSpeed) "\
                   "FROM %(table_name)s WHERE dateTime>%(ts)s "\
                   "GROUP BY ROUND(windDir/%(angle)s)"

    # we expect at least 'points' rows in our result so use genSql
    for _row in db_manager.genSql(windrose_sql % inter_dict):
        # for windDir==None we expect some results with None, we can ignore
        # those
        if _row is None or None in _row:
            pass
        else:
            # Because of the structure of the compass and the limitations in
            # SQL maths our 'North' result will be returned in 2 parts. It will
            # be the sum of the '0' group and the 'points' group.
            if int(_row[0]) != int(points):
                rose[int(_row[0])] += _row[1]
            else:
                rose[0] += _row[1]
    # now  round our results and return
    return [round(x, 1) for x in rose]


# ============================================================================
#                           class ThreadedSource
# ============================================================================

class ThreadedSource(threading.Thread):
    """Base class for a threaded scroller text block.

    ThreadedSource constructor parameters:

        control_queue:       A Queue object used by our parent to control 
                             (shutdown) this thread.
        result_queue:        A Queue object used to pass forecast data to the
                             destination
        engine:              an instance of weewx.engine.StdEngine
        config_dict:         A WeeWX config dictionary.

    ThreadedSource methods:

        run.            Thread entry point, controls data fetching, parsing and
                        dispatch. Monitors the control queue.
        get_data.       Obtain the raw scroller text data. This method must be 
                        written for each child class.
        parse_data.     Parse the raw scroller text data and return the final 
                        format data. This method must be written for each child 
                        class.
    """
    
    def __init__(self, control_queue, result_queue, engine, config_dict):

        # Initialize my superclass
        threading.Thread.__init__(self)

        # set up a some thread things
        self.setDaemon(True)
        # thread name needs to be set in the child class __init__() eg:
        #   self.setName('RtgdDarkskyThread')

        # save the queues we will use
        self.control_queue = control_queue
        self.result_queue = result_queue

    def run(self):
        """Entry point for the thread."""

        self.setup()
        # since we are in a thread some additional try..except clauses will
        # help give additional output in case of an error rather than having
        # the thread die silently
        try:
            # Run a continuous loop, obtaining API data as required and
            # monitoring the control queue for the shutdown signal. Only break
            # out if we receive the shutdown signal (None) from our parent.
            while True:
                # run an inner loop querying the API and checking for the
                # shutdown signal
                # first up query the API
                _response = self.get_response()
                # if we have a non-None response then we have data from Darksky,
                # parse the response, gather the required data and put it in
                # the result queue
                if _response is not None:
                    # parse the API response and extract the forecast text
                    _data = self.parse_response(_response)
                    # if we have some data then place it in the result queue
                    if _data is not None:
                        # construct our data dict for the queue
                        _package = {'type': 'forecast',
                                    'payload': _data}
                        self.result_queue.put(_package)
                # now check to see if we have a shutdown signal
                try:
                    # Try to get data from the queue, block for up to 60
                    # seconds. If nothing is there an empty queue exception
                    # will be thrown after 60 seconds
                    _package = self.control_queue.get(block=True, timeout=60)
                except queue.Empty:
                    # nothing in the queue so continue
                    pass
                else:
                    # something was in the queue, if it is the shutdown signal
                    # then return otherwise continue
                    if _package is None:
                        # we have a shutdown signal so return to exit
                        return
        except Exception as e:
            # Some unknown exception occurred. This is probably a serious
            # problem. Exit with some notification.
            log.critical("Unexpected exception of type %s" % (type(e), ))
            weeutil.logger.log_traceback(log.critical, 'rtgd: **** ')
            log.critical("Thread exiting. Reason: %s" % (e, ))
    
    def setup(self):
        """Perform any post post-__init__() setup.
        
        This method is executed as the very first thing in the thread run() 
        method. It must be defined if required for each child class.
        """

        pass

    def get_response(self):
        """Obtain the raw block data.
        
        This method must be defined for each child class.
        """

        return None
        
    def parse_response(self, response):
        """Parse the block response and return the required data.
        
        This method must be defined if the raw data from the block must be 
        further processed to extract the final scroller text.
        """

        return response


# ============================================================================
#                             class Source
# ============================================================================

class Source(object):
    """base class for a non-threaded scroller text block."""

    def __init__(self, control_queue, result_queue, engine, config_dict):
        
        # since we are not running in a thread we only need keep track of the 
        # result queue
        self.result_queue = result_queue

    def start(self):
        """Our entry point.
        
        Unlike most other block class Source does not run in a thread but 
        rather is a simple non-threaded class that provides a result once and 
        then does nothing else. The start() method has been defined as the 
        entry point, so we can be 'started' just like a threading.Thread
        object.
        """

        # get the scroller text string
        _text = self.get_data()
        # construct our data dict for the queue
        _package = {'type': 'forecast',
                    'payload': _text}
        # now add it to the queue
        self.result_queue.put(_package)

    def get_data(self):
        """Get scroller user specified scroller text string.
        
        This method must be defined for each child class.
        """

        return ''


# ============================================================================
#                              class WUSource
# ============================================================================

class WUSource(ThreadedSource):
    """Thread that obtains WU API forecast text and places it in a queue.

    The WUThread class queries the WU API and places selected forecast text in
    JSON format in a queue used by the data consumer. The WU API is called at a
    user selectable frequency. The thread listens for a shutdown signal from
    its parent.

    WUThread constructor parameters:

        control_queue:  A Queue object used by our parent to control (shutdown)
                        this thread.
        result_queue:   A Queue object used to pass forecast data to the
                        destination
        engine:         An instance of class weewx.weewx.Engine
        config_dict:    A WeeWX config dictionary.

    WUThread methods:

        run.               Control querying of the API and monitor the control
                           queue.
        query_wu.          Query the API and put selected forecast data in the
                           result queue.
        parse_wu_response. Parse a WU API response and return selected data.
    """

    VALID_FORECASTS = ('3day', '5day', '7day', '10day', '15day')
    VALID_NARRATIVES = ('day', 'day-night')
    VALID_LOCATORS = ('geocode', 'iataCode', 'icaoCode', 'placeid', 'postalKey')
    VALID_UNITS = ('e', 'm', 's', 'h')
    VALID_LANGUAGES = ('ar-AE', 'az-AZ', 'bg-BG', 'bn-BD', 'bn-IN', 'bs-BA',
                       'ca-ES', 'cs-CZ', 'da-DK', 'de-DE', 'el-GR', 'en-GB',
                       'en-IN', 'en-US', 'es-AR', 'es-ES', 'es-LA', 'es-MX',
                       'es-UN', 'es-US', 'et-EE', 'fa-IR', 'fi-FI', 'fr-CA',
                       'fr-FR', 'gu-IN', 'he-IL', 'hi-IN', 'hr-HR', 'hu-HU',
                       'in-ID', 'is-IS', 'it-IT', 'iw-IL', 'ja-JP', 'jv-ID',
                       'ka-GE', 'kk-KZ', 'kn-IN', 'ko-KR', 'lt-LT', 'lv-LV',
                       'mk-MK', 'mn-MN', 'ms-MY', 'nl-NL', 'no-NO', 'pl-PL',
                       'pt-BR', 'pt-PT', 'ro-RO', 'ru-RU', 'si-LK', 'sk-SK',
                       'sl-SI', 'sq-AL', 'sr-BA', 'sr-ME', 'sr-RS', 'sv-SE',
                       'sw-KE', 'ta-IN', 'ta-LK', 'te-IN', 'tg-TJ', 'th-TH',
                       'tk-TM', 'tl-PH', 'tr-TR', 'uk-UA', 'ur-PK', 'uz-UZ',
                       'vi-VN', 'zh-CN', 'zh-HK', 'zh-TW')
    VALID_FORMATS = ('json', )

    def __init__(self, control_queue, result_queue, engine, config_dict):

        # initialize my base class
        super(WUSource, self).__init__(control_queue, result_queue, 
                                       engine, config_dict)

        # set thread name
        self.setName('RtgdWuThread')

        # get the WU config dict
        _rtgd_config_dict = config_dict.get("RealtimeGaugeData")
        wu_config_dict = _rtgd_config_dict.get("WU", dict())
        
        # interval between API calls
        self.interval = to_int(wu_config_dict.get('interval', 1800))
        # max no of tries we will make in any one attempt to contact WU via API
        self.max_tries = to_int(wu_config_dict.get('max_tries', 3))
        # Get API call lockout period. This is the minimum period between API
        # calls for the same feature. This prevents an error condition making
        # multiple rapid API calls and thus breach the API usage conditions.
        self.lockout_period = to_int(wu_config_dict.get('api_lockout_period',
                                                        60))
        # initialise container for timestamp of last WU api call
        self.last_call_ts = None

        # Get our API key from weewx.conf, first look in [RealtimeGaugeData]
        # [[WU]] and if no luck try [Forecast] if it exists. Wrap in a
        # try..except loop to catch exceptions (ie one or both don't exist).
        try:
            if wu_config_dict.get('api_key') is not None:
                api_key = wu_config_dict.get('api_key')
            elif config_dict['Forecast']['WU'].get('api_key', None) is not None:
                api_key = config_dict['Forecast']['WU'].get('api_key')
            else:
                raise MissingApiKey("Cannot find valid Weather Underground API key")
        except KeyError:
            raise MissingApiKey("Cannot find Weather Underground API key")

        # get the forecast type
        _forecast = wu_config_dict.get('forecast_type', '5day').lower()
        # validate units
        self.forecast = _forecast if _forecast in self.VALID_FORECASTS else '5day'

        # get the forecast text to display
        _narrative = wu_config_dict.get('forecast_text', 'day-night').lower()
        self.forecast_text = _narrative if _narrative in self.VALID_NARRATIVES else 'day-night'

        # FIXME, Not sure the logic is correct should we get a delinquent location setting
        # get the locator type and location argument to use for the forecast
        # first get the
        _location = wu_config_dict.get('location', 'geocode').split(',', 1)
        _location_list = [a.strip() for a in _location]
        # validate the locator type
        self.locator = _location_list[0] if _location_list[0] in self.VALID_LOCATORS else 'geocode'
        if len(_location_list) == 2:
            self.location = _location_list[1]
        else:
            self.locator = 'geocode'
            self.location = '%s,%s' % (engine.stn_info.latitude_f,
                                       engine.stn_info.longitude_f)

        # get units to be used in forecast text
        _units = wu_config_dict.get('units', 'm').lower()
        # validate units
        self.units = _units if _units in self.VALID_UNITS else 'm'

        # get language to be used in forecast text
        _language = wu_config_dict.get('language', 'en-GB')
        # validate language
        self.language = _language if _language in self.VALID_LANGUAGES else 'en-GB'

        # get format of the API response
        _format = wu_config_dict.get('format', 'json').lower()
        # validate format
        self.format = _format if _format in self.VALID_FORMATS else 'json'

        # get a WeatherUndergroundAPI object to handle the API calls
        self.api = WeatherUndergroundAPIForecast(api_key)

        # log what we will do
        log.info("RealTimeGaugeData scroller text will use Weather Underground forecast data")

    def get_response(self):
        """If required query the WU API and return the response.

        Checks to see if it is time to query the API, if so queries the API
        and returns the raw response in JSON format. To prevent the user
        exceeding their API call limit the query is only made if at least
        self.lockout_period seconds have elapsed since the last call.

        Inputs:
            None.

        Returns:
            The raw WU API response in JSON format.
        """

        # get the current time
        now = time.time()
        if weewx.debug == 2:
            log.debug("Last Weather Underground API call at %s" % self.last_call_ts)

        # has the lockout period passed since the last call
        if self.last_call_ts is None or ((now + 1 - self.lockout_period) >= self.last_call_ts):
            # If we haven't made an API call previously or if its been too long
            # since the last call then make the call
            if (self.last_call_ts is None) or ((now + 1 - self.interval) >= self.last_call_ts):
                # Make the call, wrap in a try..except just in case
                try:
                    _response = self.api.forecast_request(forecast=self.forecast,
                                                          locator=self.locator,
                                                          location=self.location,
                                                          units=self.units,
                                                          language=self.language,
                                                          format=self.format,
                                                          max_tries=self.max_tries)
                    log.debug("Downloaded updated Weather Underground forecast information")
                except Exception as e:
                    # Some unknown exception occurred. Set _response to None,
                    # log it and continue.
                    _response = None
                    log.info("Unexpected exception of type %s" % (type(e), ))
                    weeutil.logger.log_traceback(log.info, 'WUThread: **** ')
                    log.info("Unexpected exception of type %s" % (type(e), ))
                    log.info("Weather Underground API forecast query failed")
                # if we got something back then reset our last call timestamp
                if _response is not None:
                    self.last_call_ts = now
                return _response
        else:
            # the API call limiter kicked in so say so
            log.info("Tried to make a WU API call within %d sec of the previous call." % (self.lockout_period, ))
            log.info("        WU API call limit reached. API call skipped.")
        return None

    def parse_response(self, response):
        """ Parse a WU API forecast response and return the forecast text.

        The WU API forecast response contains a number of forecast texts, the
        three main ones are:

        - the full day narrative
        - the day time narrative, and
        - the nighttime narrative.

        WU claims that nighttime is for 7pm to 7am and day time is for 7am to
        7pm though anecdotally it appears that the daytime forecast disappears
        late afternoon and reappears early morning. If day-night forecast text
        is selected we will look for a daytime forecast up until 7pm with a
        fallback to the nighttime forecast. From 7pm to midnight the nighttime
        forecast will be used. If day forecast text is selected then we will
        use the higher level full day forecast text.

        Input:
            response: A WU API response in JSON format.

        Returns:
            The selected forecast text if it exists otherwise None.
        """

        # deserialize the response but be prepared to catch an exception if the
        # response can't be deserialized
        try:
            _response_json = json.loads(response)
        except ValueError:
            # can't deserialize the response so log it and return None
            log.info("Unable to deserialise Weather Underground forecast response")
            return None

        # forecast data has been deserialized so check which forecast narrative
        # we are after and locate the appropriate field.
        if self.forecast_text == 'day':
            # we want the full day narrative, use a try..except in case the
            # response is malformed
            try:
                return _response_json['narrative'][0]
            except KeyError:
                # could not find the narrative so log and return None
                log.debug("Unable to locate 'narrative' field for "
                          "'%s' forecast narrative" % self.forecast_text)
                return None
        else:
            # we want the day time or nighttime narrative, but which, WU
            # starts dropping the day narrative late in the afternoon and it
            # does not return until the early hours of the morning. If possible
            # use day time up until 7pm but be prepared to fall back to night
            # if the day narrative has disappeared. Use night narrative for 7pm
            # to 7am but start looking for day again after midnight.
            # get the current local hour
            _hour = datetime.datetime.now().hour
            # helper string for later logging
            if 7 <= _hour < 19:
                _period_str = 'daytime'
            else:
                _period_str = 'nighttime'
            # day_index is the index of the daytime forecast for today, it
            # will either be 0 (ie the first entry) or None if today's day
            # forecast is not present. If it is None then the nighttime
            # forecast is used. Start by assuming there is no day forecast.
            day_index = None
            if _hour < 19:
                # it's before 7pm so use day time, first check if it exists
                try:
                    day_index = _response_json['daypart'][0]['dayOrNight'].index('D')
                except KeyError:
                    # couldn't find a key for one of the fields, log it and
                    # force use of night index
                    log.info("Unable to locate 'dayOrNight' field "
                             "for %s '%s' forecast narrative" % (_period_str, self.forecast_text))
                    day_index = None
                except ValueError:
                    # could not get an index for 'D', log it and force use of
                    # night index
                    log.info("Unable to locate 'D' index "
                             "for %s '%s' forecast narrative" % (_period_str, self.forecast_text))
                    day_index = None
            # we have a day_index but is it for today or some later day
            if day_index is not None and day_index <= 1:
                # we have a suitable day index so use it
                _index = day_index
            else:
                # no day index for today so try the night index
                try:
                    _index = _response_json['daypart'][0]['dayOrNight'].index('N')
                except KeyError:
                    # couldn't find a key for one of the fields, log it and
                    # return None
                    log.info("Unable to locate 'dayOrNight' field "
                             "for %s '%s' forecast narrative" % (_period_str, self.forecast_text))
                    return None
                except ValueError:
                    # could not get an index for 'N', log it and return None
                    log.info("Unable to locate 'N' index "
                             "for %s '%s' forecast narrative" % (_period_str, self.forecast_text))
                    return None
            # if we made it here we have an index to use so get the required
            # narrative
            try:
                return _response_json['daypart'][0]['narrative'][_index]
            except KeyError:
                # if we can't find a field log the error and return None
                log.info("Unable to locate 'narrative' field "
                         "for '%s' forecast narrative" % self.forecast_text)
            except ValueError:
                # if we can't find an index log the error and return None
                log.info("Unable to locate 'narrative' index "
                         "for '%s' forecast narrative" % self.forecast_text)

            return None


# ============================================================================
#                    class WeatherUndergroundAPIForecast
# ============================================================================

class WeatherUndergroundAPIForecast(object):
    """Obtain a forecast from the Weather Underground API.

    The WU API is accessed by calling one or more features. These features can
    be grouped into two groups, WunderMap layers and data features. This class
    supports access to the API data features only.

    WeatherUndergroundAPI constructor parameters:

        api_key: WeatherUnderground API key to be used.

    WeatherUndergroundAPI methods:

        data_request. Submit a data feature request to the WeatherUnderground
                      API and return the response.
    """

    BASE_URL = 'https://api.weather.com/v3/wx/forecast/daily'

    def __init__(self, api_key):
        # initialise a WeatherUndergroundAPIForecast object

        # save the API key to be used
        self.api_key = api_key

    def forecast_request(self, locator, location, forecast='5day', units='m',
                         language='en-GB', format='json', max_tries=3):
        """Make a forecast request via the API and return the results.

        Construct an API forecast call URL, make the call and return the
        response.

        Parameters:
            forecast:  The type of forecast required. String, must be one of
                       '3day', '5day', '7day', '10day' or '15day'.
            locator:   Type of location used. String. Must be a WU API supported
                       location type.
                       Refer https://docs.google.com/document/d/1RY44O8ujbIA_tjlC4vYKHKzwSwEmNxuGw5sEJ9dYjG4/edit#
            location:  Location argument. String.
            units:     Units to use in the returned data. String, must be one
                       of 'e', 'm', 's' or 'h'.
                       Refer https://docs.google.com/document/d/13HTLgJDpsb39deFzk_YCQ5GoGoZCO_cRYzIxbwvgJLI/edit#heading=h.k9ghwen9fj7l
            language:  Language to return the response in. String, must be one
                       of the WU API supported language_setting codes
                       (eg 'en-US', 'es-MX', 'fr-FR').
                       Refer https://docs.google.com/document/d/13HTLgJDpsb39deFzk_YCQ5GoGoZCO_cRYzIxbwvgJLI/edit#heading=h.9ph8uehobq12
            format:    The output format_setting of the data returned by the WU
                       API. String, must be 'json' (based on WU API
                       documentation JSON is the only confirmed supported
                       format_setting.
            max_tries: The maximum number of attempts to be made to obtain a
                       response from the WU API. Default is 3.

        Returns:
            The WU API forecast response in JSON format_setting.
        """

        # construct the locator setting
        location_setting = '='.join([locator, location])
        # construct the units_setting string
        units_setting = '='.join(['units', units])
        # construct the language_setting string
        language_setting = '='.join(['language', language])
        # construct the format_setting string
        format_setting = '='.join(['format', format])
        # construct API key string
        api_key = '='.join(['apiKey', self.api_key])
        # construct the parameter string
        parameters = '&'.join([location_setting, units_setting,
                               language_setting, format_setting, api_key])

        # construct the base forecast url
        f_url = '/'.join([self.BASE_URL, forecast])

        # finally construct the full URL to use
        url = '?'.join([f_url, parameters])

        # if debug >=1 log the URL used but obfuscate the API key
        if weewx.debug >= 1:
            _obf_api_key = '='.join(['apiKey',
                                     '*'*(len(self.api_key) - 4) + self.api_key[-4:]])
            _obf_parameters = '&'.join([location_setting, units_setting,
                                        language_setting, format_setting,
                                        _obf_api_key])
            _obf_url = '?'.join([f_url, _obf_parameters])
            log.debug("Submitting Weather Underground API call using URL: %s" % (_obf_url, ))
        # we will attempt the call max_tries times
        for count in range(max_tries):
            # attempt the call
            try:
                w = urllib.request.urlopen(url)
                # Get charset used so we can decode the stream correctly.
                # Unfortunately the way to get the charset depends on whether
                # we are running under python2 or python3. Assume python3 but be
                # prepared to catch the error if python2.
                try:
                    char_set = w.headers.get_content_charset()
                except AttributeError:
                    # must be python2
                    char_set = w.headers.getparam('charset')
                # now get the response decoding it appropriately
                response = w.read().decode(char_set)
                w.close()
                return response
            except (urllib.error.URLError, socket.timeout) as e:
                log.error("Failed to get Weather Underground forecast on attempt %d" % (count+1, ))
                log.error("   **** %s" % e)
        else:
            log.error("Failed to get Weather Underground forecast")
        return None


# ============================================================================
#                           class ZambrettiSource
# ============================================================================

class ZambrettiSource(ThreadedSource):
    """Thread that obtains Zambretti forecast text and places it in a queue.

    Requires the WeeWX forecast extension to be installed and configured to
    provide the Zambretti forecast.

    ZambrettiSource constructor parameters:

        control_queue:  A Queue object used by our parent to control (shutdown)
                        this thread.
        result_queue:   A Queue object used to pass forecast data to the
                        destination
        engine:         An instance of class weewx.weewx.Engine
        config_dict:    A WeeWX config dictionary.

    ZambrettiSource methods:

        run.            Control fetching the forecast and monitor the control
                        queue.
    """

    def __init__(self, control_queue, result_queue, engine, config_dict):

        # Initialize my base class
        super(ZambrettiSource, self).__init__(control_queue, result_queue, 
                                              engine, config_dict)

        # set thread name
        self.setName('RtgdZambrettiThread')

        self.config_dict = config_dict
        # get the Zambretti config dict
        _rtgd_config_dict = config_dict.get("RealtimeGaugeData")
        self.zambretti_config_dict = _rtgd_config_dict.get("Zambretti")

        self.zambretti = None

        # log what we will do
        log.info("RealTimeGaugeData scroller text will use Zambretti forecast data")
    
    def setup(self):
        """Get a Zambretti object.
        
        We need to do this here rather than in __init__() due to SQLite thread
        limitations.
        """

        self.zambretti = Zambretti(self.config_dict, 
                                   self.zambretti_config_dict)
        
    def get_response(self):
        """Get the raw Zambretti forecast text."""
        
        _data = self.zambretti.get_data()
        return _data


# ============================================================================
#                              class Zambretti
# ============================================================================

class Zambretti(object):
    """Class to extract Zambretti forecast text.

    Requires the WeeWX forecast extension to be installed and configured to
    provide the Zambretti forecast otherwise 'Forecast not available' will be
    returned.
    """

    DEFAULT_FORECAST_BINDING = 'forecast_binding'
    DEFAULT_BINDING_DICT = {'database': 'forecast_sqlite',
                            'manager': 'weewx.manager.Manager',
                            'table_name': 'archive',
                            'schema': 'user.forecast.schema'}
    UNAVAILABLE_MESSAGE = 'Zambretti forecast unavailable'

    def __init__(self, config_dict, zambretti_config_dict):

        # interval between queries
        self.interval = to_int(zambretti_config_dict.get('interval', 1800))
        # max no of tries we will make in any one attempt to query the db
        self.max_tries = to_int(zambretti_config_dict.get('max_tries', 3))
        # wait time between db query retries
        self.retry_wait = to_int(zambretti_config_dict.get('retry_wait', 3))
        # initialise container for timestamp of last db query
        self.last_query_ts = None
        
        # flag indicating whether the WeeWX forecasting extension is installed
        self.forecasting_installed = False
        
        # Get a db manager for the forecast database and import the Zambretti
        # label lookup dict. If an exception is raised then we can assume the
        # forecast extension is not installed.
        try:
            # create a db manager config dict
            dbm_dict = weewx.manager.get_manager_dict(config_dict['DataBindings'],
                                                      config_dict['Databases'],
                                                      Zambretti.DEFAULT_FORECAST_BINDING,
                                                      default_binding_dict=Zambretti.DEFAULT_BINDING_DICT)
            # get a db manager for the forecast database
            self.dbm = weewx.manager.open_manager(dbm_dict)
            # import the Zambretti forecast text
            from user.forecast import zambretti_label_dict
            self.zambretti_label_dict = zambretti_label_dict
            # if we made it this far the forecast extension is installed and we
            # can do business
            self.forecasting_installed = True
        # TODO. Should catch import error
        except Exception as e:
            # Something went wrong so log the error. Our forecasting_installed 
            # flag will not have been set so it is safe to continue but there 
            # will be no Zambretti text
            log.debug('Error initialising Zambretti forecast, is the forecast extension installed.')
            log.debug('Unexpected exception of type %s' % (type(e), ))
            weeutil.logger.log_traceback(log.debug, "    ****  ")

    def get_data(self):
        """Get scroller user specified scroller text string.

        If Zambretti is not installed or nothing is found then a short 
        informative string is returned.
        """

        # get the current time
        now = time.time()
        if weewx.debug == 2:
            log.debug("Last Zambretti forecast obtained at %s" % self.last_query_ts)
        # If we haven't made a db query previously or if it's been too long
        # since the last query then make the query
        if (self.last_query_ts is None) or ((now + 1 - self.interval) >= self.last_query_ts):
            # if the forecast extension is not installed then return an 
            # appropriate message
            if not self.is_installed:
                return self.UNAVAILABLE_MESSAGE
            # make the query
            # SQL query to get the latest Zambretti forecast code
            sql = "SELECT dateTime,zcode FROM %s "\
                  "WHERE method = 'Zambretti' "\
                  "ORDER BY dateTime DESC LIMIT 1" % self.dbm.table_name
            # execute the query, wrap in try..except just in case
            for count in range(self.max_tries):
                try:
                    record = self.dbm.getSql(sql)
                    if record is not None:
                        # we have a non-None response so save the time of the 
                        # query and return the decoded forecast text
                        self.last_query_ts = now
                        return self.zambretti_label_dict[record[1]]
                except Exception as e:
                    log.error('get zambretti failed (attempt %d of %d): %s' %
                              ((count + 1), self.max_tries, e))
                    log.debug('waiting %d seconds before retry' % self.retry_wait)
                    time.sleep(self.retry_wait)
            # if we made it here we have been unable to get a response from the
            # forecast db so return a suitable message
            return self.UNAVAILABLE_MESSAGE
        else:
            return None

    @property
    def is_installed(self):
        """Is the forecasting extension installed."""

        return self.forecasting_installed


# ============================================================================
#                           class DarkskyThread
# ============================================================================

class DarkskySource(ThreadedSource):
    """Thread that obtains Darksky forecast data and places it in a queue.

    The DarkskyThread class queries the Darksky API and places selected 
    forecast data in JSON format in a queue used by the data consumer. The 
    Darksky API is called at a user selectable frequency. The thread listens 
    for a shutdown signal from its parent.

    DarkskyThread constructor parameters:

        control_queue:       A Queue object used by our parent to control 
                             (shutdown) this thread.
        result_queue:        A Queue object used to pass forecast data to the
                             destination
        engine:              A weewx.engine.StdEngine object
        conf_dict:           A WeeWX config dictionary.

    DarkskyThread methods:

        run.            Control querying of the API and monitor the control
                        queue.
        get_response.   Query the API and put selected forecast data in the
                        result queue.
        parse_response. Parse a Darksky API response and return selected data.
    """

    VALID_UNITS = ['auto', 'ca', 'uk2', 'us', 'si']

    VALID_LANGUAGES = ('ar', 'az', 'be', 'bg', 'bs', 'ca', 'cs', 'da', 'de',
                       'el', 'en', 'es', 'et', 'fi', 'fr', 'hr', 'hu', 'id',
                       'is', 'it', 'ja', 'ka', 'ko', 'kw', 'nb', 'nl', 'pl',
                       'pt', 'ro', 'ru', 'sk', 'sl', 'sr', 'sv', 'tet', 'tr',
                       'uk', 'x-pig-latin', 'zh', 'zh-tw')

    DEFAULT_BLOCK = 'hourly'

    def __init__(self, control_queue, result_queue, engine, config_dict):

        # initialize my base class:
        super(DarkskySource, self).__init__(control_queue, result_queue, 
                                            engine, config_dict)

        # set thread name
        self.setName('RtgdDarkskyThread')

        # get the darksky config dict
        _rtgd_config_dict = config_dict.get("RealtimeGaugeData")
        darksky_config_dict = _rtgd_config_dict.get("DS", dict())

        # Dark Sky uses lat, long to 'locate' the forecast. Check if lat and
        # long are specified in the darksky_config_dict, if not use station lat
        # and long.
        latitude = darksky_config_dict.get("latitude", engine.stn_info.latitude_f)
        longitude = darksky_config_dict.get("longitude", engine.stn_info.longitude_f)

        # interval between API calls
        self.interval = to_int(darksky_config_dict.get('interval', 1800))
        # max no of tries we will make in any one attempt to contact the API
        self.max_tries = to_int(darksky_config_dict.get('max_tries', 3))
        # Get API call lockout period. This is the minimum period between API
        # calls for the same feature. This prevents an error condition making
        # multiple rapid API calls and thus breach the API usage conditions.
        self.lockout_period = to_int(darksky_config_dict.get('api_lockout_period',
                                                             60))
        # initialise container for timestamp of last API call
        self.last_call_ts = None
        # Get our API key from weewx.conf, first look in [RealtimeGaugeData]
        # [[WU]] and if no luck try [Forecast] if it exists. Wrap in a
        # try..except loop to catch exceptions (ie one or both don't exist).
        key = darksky_config_dict.get('api_key', None)
        if key is None:
            raise MissingApiKey("Cannot find valid Darksky key")
        # get a DarkskyForecastAPI object to handle the API calls
        self.api = DarkskyForecastAPI(key, latitude, longitude)
        # get units to be used in forecast text
        _units = darksky_config_dict.get('units', 'ca').lower()
        # validate units
        self.units = _units if _units in self.VALID_UNITS else 'ca'
        # get language to be used in forecast text
        _language = darksky_config_dict.get('language', 'en').lower()
        # validate language
        self.language = _language if _language in self.VALID_LANGUAGES else 'en'
        # get the Darksky block to be used, default to our default
        self.block = darksky_config_dict.get('block', self.DEFAULT_BLOCK).lower()

        # log what we will do
        log.info("RealTimeGaugeData scroller text will use Darksky forecast data")

    def get_response(self):
        """If required query the Darksky API and return the JSON response.

        Checks to see if it is time to query the API, if so queries the API
        and returns the raw response in JSON format. To prevent the user
        exceeding their API call limit the query is only made if at least
        self.lockout_period seconds have elapsed since the last call.

        Inputs:
            None.

        Returns:
            The Darksky API response in JSON format or None if no/invalid 
            response was obtained.
        """

        # get the current time
        now = time.time()
        if weewx.debug == 2:
            log.debug("Last Darksky API call at %s" % self.last_call_ts)
        # has the lockout period passed since the last call
        if self.last_call_ts is None or ((now + 1 - self.lockout_period) >= self.last_call_ts):
            # If we haven't made an API call previously or if it's been too long
            # since the last call then make the call
            if (self.last_call_ts is None) or ((now + 1 - self.interval) >= self.last_call_ts):
                # Make the call, wrap in a try..except just in case
                try:
                    _response = self.api.get_data(block=self.block,
                                                  language=self.language,
                                                  units=self.units,
                                                  max_tries=self.max_tries)
                    log.debug("Downloaded updated Darksky forecast")
                except Exception as e:
                    # Some unknown exception occurred. Set _response to None,
                    # log it and continue.
                    _response = None
                    log.info("Unexpected exception of type %s" % (type(e), ))
                    weeutil.logger.log_traceback(log.info, 'rtgd: **** ')
                    log.info("Unexpected exception of type %s" % (type(e), ))
                    log.info("Darksky forecast API query failed")
                # if we got something back then reset our last call timestamp
                if _response is not None:
                    self.last_call_ts = now
                return _response
        else:
            # the API call limiter kicked in so say so
            log.info("Tried to make an Darksky API call within %d sec of the previous call." % (self.lockout_period, ))
            log.info("Darksky API call limit reached. API call skipped.")
        return None

    def parse_response(self, response):
        """Parse a Darksky forecast response.

        Take a Darksky forecast response, check for (Darksky defined) errors 
        then extract and return the required summary text.

        Input:
            response: A Darksky forecast API response in JSON format.

        Returns:
            Summary text or None.
        """

        # There is not too much validation of the data we can do other than 
        # looking at the 'flags' object
        if 'flags' in response:
            if 'darksky-unavailable' in response['flags']:
                log.info("Darksky data for this location temporarily unavailable")
                return None
        else:
            log.debug("No flag object in Darksky API response.")

        # get the summary data to be used
        # is our block available, can't assume it is
        if self.block in response:
            # we have our block, but is the summary there
            if 'summary' in response[self.block]:
                # we have a summary field
                summary = response[self.block]['summary']
                return summary
            else:
                # we have no summary field, so log it and return None
                log.debug("Summary data not available for '%s' forecast" % (self.block,))
                return None
        else:
            log.debug('Dark Sky %s block not available' % self.block)
            return 'Dark Sky %s block not available' % self.block


# ============================================================================
#                         class DarkskyForecastAPI
# ============================================================================

class DarkskyForecastAPI(object):
    """Query the Darksky API and return the API response.

    DarkskyForecastAPI constructor parameters:

        darksky_config_dict: Dictionary containing the following keys:
            key:       Darksky secret key to be used
            latitude:  Latitude of the location concerned 
            longitude: Longitude of the location concerned 

    DarkskyForecastAPI methods:

        get_data. Submit a data request to the Darksky API and return the 
                  response.

        _build_optional: Build a string containing the optional parameters to 
                         submitted as part of the API request URL.
        
        _hit_api: Submit the API request and capture the response.

        obfuscated_key: Property to return an obfuscated secret key.
    """

    # base URL from which to construct an API call URL
    BASE_URL = 'https://api.darksky.net/forecast'
    # blocks we may want to exclude
    BLOCKS = ('currently', 'minutely', 'hourly', 'daily', 'alerts')

    def __init__(self, key, latitude, longitude):
        # initialise a DarkskyForecastAPI object

        # save the secret key to be used
        self.key = key
        # save lat and long
        self.latitude = latitude
        self.longitude = longitude

    def get_data(self, block='hourly', language='en', units='auto',
                 max_tries=3):
        """Make a data request via the API and return the response.

        Construct an API call URL, make the call and return the response.

        Parameters:
            block:    Darksky block to be used. None or list of strings, default is None.
            language:  The language to be used in any response text. Refer to
                       the optional parameter 'language' at 
                       https://darksky.net/dev/docs. String, default is 'en'.
            units:     The units to be used in the response. Refer to the 
                       optional parameter 'units' at https://darksky.net/dev/docs.
                       String, default is 'auto'.
            max_tries: The maximum number of attempts to be made to obtain a
                       response from the API. Number, default is 3.

        Returns:
            The Darksky API response in JSON format.
        """

        # start constructing the API call URL to be used
        url = '/'.join([self.BASE_URL,
                        self.key,
                        '%s,%s' % (self.latitude, self.longitude)])
        
        # now build the optional parameters string
        optional_string = self._build_optional(block=block,
                                               language=language,
                                               units=units)
        # if it has any content then add it to the URL
        if len(optional_string) > 0:
            url = '?'.join([url, optional_string])

        # if debug >=1 log the URL used but obfuscate the key
        if weewx.debug >= 1:
            _obfuscated_url = '/'.join([self.BASE_URL,
                                        self.obfuscated_key,
                                        '%s,%s' % (self.latitude, self.longitude)])
            _obfuscated_url = '?'.join([_obfuscated_url, optional_string])
            log.debug("Submitting API call using URL: %s" % (_obfuscated_url, ))
        # make the API call
        _response = self._hit_api(url, max_tries)
        # if we have a response we need to deserialise it
        json_response = json.loads(_response) if _response is not None else None
        # return the response
        return json_response

    def _build_optional(self, block='hourly', language='en', units='auto'):
        """Build the optional parameters string."""

        # initialise a list of non-None optional parameters and their values
        opt_params_list = []
        # exclude all but our block
        _blocks = [b for b in self.BLOCKS if b != block]
        opt_params_list.append('exclude=%s' % ','.join(_blocks))
        # language
        if language is not None:
            opt_params_list.append('lang=%s' % language)
        # units
        if units is not None:
            opt_params_list.append('units=%s' % units)
        # now if we have any parameters concatenate them separating each with 
        # an ampersand
        opt_params = "&".join(opt_params_list)
        # return the resulting string
        return opt_params

    @staticmethod
    def _hit_api(url, max_tries=3):
        """Make the API call and return the result."""

        # we will attempt the call max_tries times
        for count in range(max_tries):
            # attempt the call
            try:
                w = urllib.request.urlopen(url)
                # Get charset used so we can decode the stream correctly.
                # Unfortunately the way to get the charset depends on whether
                # we are running under python2 or python3. Assume python3 but be
                # prepared to catch the error if python2.
                try:
                    char_set = w.headers.get_content_charset()
                except AttributeError:
                    # must be python2
                    char_set = w.headers.getparam('charset')
                # now get the response decoding it appropriately
                response = w.read().decode(char_set)
                w.close()
                return response
            except (urllib.error.URLError, socket.timeout) as e:
                log.error("Failed to get API response on attempt %d" % (count+1, ))
                log.error("   **** %s" % e)
        else:
            log.error("Failed to get API response")
        return None

    @property
    def obfuscated_key(self):
        """Produce and obfuscated copy of the key."""

        # replace all characters in the key with an asterisk except for the 
        # last 4
        return '*'*(len(self.key) - 4) + self.key[-4:]


# ============================================================================
#                             class FileSource
# ============================================================================

class FileSource(ThreadedSource):
    """Thread to return a single line of text from a file.

    FileSource constructor parameters:

        control_queue:  A Queue object used by our parent to control (shutdown)
                        this thread.
        result_queue:   A Queue object used to pass forecast data to the
                        destination
        engine:         An instance of class weewx.weewx.Engine
        config_dict:    A WeeWX config dictionary.

    FileSource methods:

        run.               Control fetching the text and monitor the control
                           queue.
    """

    def __init__(self, control_queue, result_queue, engine, config_dict):

        # initialize my base class
        super(FileSource, self).__init__(control_queue, result_queue, engine, 
                                         config_dict)

        # set thread name
        self.setName('RtgdFileThread')

        # get the File config dict
        _rtgd_config_dict = config_dict.get("RealtimeGaugeData")
        file_config_dict = _rtgd_config_dict.get("File", dict())
        
        # interval between file reads
        self.interval = to_int(file_config_dict.get('interval', 1800))
        # get block file, check it refers to a file
        self.scroller_file = file_config_dict.get('file')
        if self.scroller_file is None or not os.path.isfile(self.scroller_file):
            log.debug("File block not specified or not a valid path/file")
            self.scroller_file = None

        # initialise the time of last file read
        self.last_read_ts = None
        
        # log what we will do
        if self.scroller_file is not None:
            log.info("RealTimeGaugeData scroller text will use text from file '%s'" % self.scroller_file)
    
    def get_response(self):
        """Get a single line of text from a file.

        Checks to see if it is time to read the file, if so the file is read 
        and the stripped raw text returned.

        Inputs:
            None.

        Returns:
            The first line of text from the file.
        """

        # get the current time
        now = time.time()
        if weewx.debug == 2:
            log.debug("Last File read at %s" % self.last_read_ts)
        if (self.last_read_ts is None) or ((now + 1 - self.interval) >= self.last_read_ts):
            # read the file, wrap in a try..except just in case
            _data = None
            try:
                if self.scroller_file is not None:
                    with open(self.scroller_file, 'r') as f:
                        _data = f.readline().strip()
                log.debug("File read")
            except Exception as e:
                # Some unknown exception occurred. Set _data to None,
                # log it and continue.
                _data = None
                log.info("Unexpected exception of type %s" % (type(e), ))
                weeutil.logger.log_traceback(log.info, 'rtgd: **** ')
                log.info("Unexpected exception of type %s" % (type(e), ))
                log.info("File read failed")
            # we got something so reset our last read timestamp
            if _data is not None:
                self.last_read_ts = now
            # and finally return the read data 
            return _data
        return None


# ============================================================================
#                             class TextSource
# ============================================================================

class TextSource(Source):
    """Class to return user specified text string."""

    def __init__(self, control_queue, result_queue, engine, config_dict):
        
        # Initialize my base class
        super(TextSource, self).__init__(control_queue, result_queue, engine, 
                                         config_dict)
        
        # since we are not running in a thread we only need keep track of our
        # config dict
        _rtgd_config_dict = config_dict.get("RealtimeGaugeData")
        self.text_config_dict = _rtgd_config_dict.get("Text", dict())

        # log what we will do
        log.info("RealTimeGaugeData scroller text will use a fixed string")

    def get_data(self):
        """Get scroller user specified scroller text string.

        If nothing is found then a zero length string is returned.
        """

        # get scroller text from weewx.conf [RealtimeGaugeData]
        _text = self.text_config_dict.get('text')
        return _text


# available scroller text block classes
SCROLLER_SOURCES = {'text': TextSource,
                    'file': FileSource,
                    'weatherunderground': WUSource,
                    'darksky': DarkskySource,
                    'zambretti': ZambrettiSource}

# available scroller text block classes
EXPORTERS = {'httppost': HttpPostExport,
             'rsync': RsyncExport}
