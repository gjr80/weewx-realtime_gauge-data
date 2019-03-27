"""
rtgd.py

A weeWX service to generate a loop based gauge-data.txt.

Copyright (C) 2017-2019 Gary Roderick             gjroderick<at>gmail.com

This program is free software: you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free Software
Foundation, either version 3 of the License, or (at your option) any later
version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY
WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
PARTICULAR PURPOSE.  See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with
this program.  If not, see http://www.gnu.org/licenses/.

  Version: 0.3.6                                      Date: 28 March 2019

  Revision History
    7 March 2019        v0.3.6
        - added support for new weather.com based WU API
        - removed support for old api.wunderground.com based WU API
        - updated to gauge-data.txt version 14 through addition of inTemp
          max/min and times fields (intempTH, intempTL, TintempTH and TintempTL)
        - minor reformatting of some RealtimeGaugeDataThread __init__ logging
        - reformatted up front comments
        - fixed incorrect rtgd.py version number
    1 January 2019      v0.3.5
        - added support for Darksky forecast API
        - added support for Zambretti forecast text (subject to weeWX
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
        - changed a syslog entry to indicate 'rtgd' as the block not 'engine'
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
          0 - standard weeWX output, no debug info
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
          respectively due to weeWX or SteelSeries Gauges not understanding the
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
        - now runs in a thread to eliminate blocking impact on weeWX
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


A weeWX service to generate a loop based gauge-data.txt.

Used to update the SteelSeries Weather Gauges in near real time.

Inspired by crt.py v0.5 by Matthew Wall, a WeeWX service to emit loop data to
file in Cumulus realtime format. Refer http://wiki.sandaysoft.com/a/Realtime.txt

Use of HTTP POST to send gauge-data.txt content to a remote URL inspired by
work by Alec Bennett. Refer https://github.com/wrybread/weewx-realtime_gauge-data.

Abbreviated instructions for use:

1.  Install the SteelSeries Weather Gauges for weeWX and confirm correct
operation of the gauges with weeWX. Refer to
https://github.com/mcrossley/SteelSeries-Weather-Gauges/tree/master/weather_server/WeeWX

2.  Put this file in $BIN_ROOT/user.

3.  Add the following stanza to weewx.conf:

[RealtimeGaugeData]
    # Date format to be used in gauge-data.txt. Default is %Y.%m.%d %H:%M
    date_format = %Y.%m.%d %H:%M

    # Path to gauge-data.txt. Relative paths are relative to HTML_ROOT. If
    # empty default is HTML_ROOT. If setting omitted altogether default is
    # /var/tmp
    rtgd_path = /home/weewx/public_html

    # File name (only) of file produced by rtgd. Optional, default is
    # gauge-data.txt.
    rtgd_file_name = gauge-data.txt

    # Remote URL to which the gauge-data.txt data will be posted via HTTP POST.
    # Optional, omit to disable HTTP POST.
    remote_server_url = http://remote/address

    # timeout in seconds for remote URL posts. Optional, default is 2
    timeout = 1

    # Text returned from remote URL indicating success. Optional, default is no
    # response text.
    response_text = success

    # Minimum interval (seconds) between file generation. Ideally
    # gauge-data.txt would be generated on receipt of every loop packet (there
    # is no point in generating more frequently than this); however, in some
    # cases the user may wish to generate gauge-data.txt less frequently. The
    # min_interval option sets the minimum time between successive
    # gauge-data.txt generations. Generation will be skipped on arrival of a
    # loop packet if min_interval seconds have NOT elapsed since the last
    # generation. If min_interval is 0 or omitted generation will occur on
    # every loop packet (as will be the case if min_interval < station loop
    # period). Optional, default is 0.
    min_interval =

    # Number of compass points to include in WindRoseData, normally
    # 8 or 16. Optional, default 16.
    windrose_points = 16

    # Period over which to calculate WindRoseData in seconds. Optional, default
    # is 86400 (24 hours).
    windrose_period = 86400

    # Binding to use for appTemp data. Optional, default 'wx_binding'.
    apptemp_binding = wx_binding

    # The SteelSeries Weather Gauges displays the content of the gauge-data.txt
    # 'forecast' field in the scrolling text display. The RTGD service can
    # populate the 'forecast' field from a number of sources. The available 
    # sources are:
    #
    # 1. a user specified text
    # 2. the first line of a text file
    # 3. Weather Underground forecast from the Weather Underground API
    # 4. Darksky forecast from the Darksky API
    # 5. Zambretti forecast from the weeWX forecast extension
    #
    # The block to be used is specified using the scroller_source config 
    # option. The scroller_source should be set to one of the following strings 
    # to use the indicated block:
    # 1. text - to use user specified text
    # 2. file - to user the first line of a text file
    # 3. Weather Underground - to use a Weather Underground forecast
    # 4. Darksky - to use a Darksky forecast
    # 5. Zambretti - to use a Zambretti forecast
    # 
    # The scroller_source config option is case insensitive. A corresponding
    # second level config section (ie [[ ]]) is required for the block to be 
    # used. Refer to step 4 below for details. If the scroller_source config 
    # option is omitted or left blank the 'forecast' filed will be blank and no 
    # scroller text will be displayed.
    scroller_source = text|file|WU|DS|Zambretti

    # Update windrun value each loop period or just on each archive period.
    # Optional, default is False.
    windrun_loop = false

    # Stations that provide partial packets are supported through a cache that
    # caches packet data. max_cache_age is the maximum age  in seconds for
    # which cached data is retained. Optional, default is 600 seconds.
    max_cache_age = 600

    # It is possible to ignore the sensor contact check result for the station
    # and always set the gauge-data.txt SensorContactLost field to 0 (sensor
    # contact not lost). This option should be used with care as it may mask a
    # legitimate sensor lost contact state. Optional, default is False.
    ignore_lost_contact = False

    # Parameters used in/required by rtgd calculations
    [[Calculate]]
        # Atmospheric transmission coefficient [0.7-0.91]. Optional, default
        # is 0.8
        atc = 0.8
        # Atmospheric turbidity (2=clear, 4-5=smoggy). Optional, default is 2.
        nfac = 2
        [[[Algorithm]]]
            # Theoretical max solar radiation algorithm to use, must be RS or
            # Bras. optional, default is RS
            maxSolarRad = RS

    [[StringFormats]]
        # String formats. Optional.
        degree_C = %.1f
        degree_F = %.1f
        degree_compass = %.0f
        hPa = %.1f
        inHg = %.2f
        inch = %.2f
        inch_per_hour = %.2f
        km_per_hour = %.1f
        km = %.1f
        mbar = %.1f
        meter = %.0f
        meter_per_second = %.1f
        mile_per_hour = %.1f
        mile = %.1f
        mm = %.1f
        mm_per_hour = %.1f
        percent = %.0f
        uv_index = %.1f
        watt_per_meter_squared = %.0f

    [[Groups]]
        # Groups. Optional. Note not all available weeWX units are supported
        # for each group.
        group_altitude = foot        # Options are 'meter' or 'foot'
        group_pressure = hPa         # Options are 'inHg', 'mbar', or 'hPa'
        group_rain = mm              # Options are 'inch' or 'mm'
        group_speed = km_per_hour    # Options are 'mile_per_hour',
                                       'km_per_hour' or 'meter_per_second'
        group_temperature = degree_C # Options are 'degree_F' or 'degree_C'

4.  If the scroller_source config option has been set add a second level config
stanza for the specified block. Config stanzas for each of the supported 
sources are:

    -   user specified text:

        # Specify settings to be used for user specified text block
        [[Text]]
            # user specified text to populate the 'forecast' field
            text = enter text here

    -   first line of text file:

        # Specify settings to be used for first line of text file block
        [[File]]
            # Path and file name of file to use as block for the 'forecast' 
            # field. Must be a text file, first line only of file is read.
            file = path/to/file/file_name

            # Interval (in seconds) between between file reads. Default is 1800.
            interval = 1800

    -   Weather Underground forecast
    
        # Specify settings to be used for Weather Underground forecast block
        [[WU]]
            # WU API key to be used when calling the WU API
            api_key = xxxxxxxxxxxxxxxx

            # Interval (in seconds) between forecast downloads. Default
            # is 1800.
            interval = 1800

            # Minimum period (in seconds) between  API calls. This prevents
            # conditions where a misbehaving program could call the WU API
            # repeatedly thus violating the API usage conditions.
            # Default is 60.
            api_lockout_period = 60

            # Maximum number attempts to obtain an API response. Default is 3.
            max_tries = 3

            # Forecast type to be used. Must be one of the following:
            #   3day - 3 day forecast
            #   5day - 5 day forecast
            #   7day - 7 day forecast
            #   10day - 10 day forecast
            #   15day - 15 day forecast
            # A user's content licensing agreement with The Weather Company
            # will determine which forecasts are available for a given API
            # key. The 5 day forecast is commonly available as a free service
            # for PWS owners. Default is 5day.
            forecast_type = 3day|5day|7day|10day|15day

            # The location to be used for the forecast. Must be one of:
            #   geocode - uses latitude/longitude to source the forecast
            #   iataCode - uses and IATA code to source the forecast
            #   icaoCode - uses an ICAO code to source the forecast
            #   placeid - uses a Place ID to source the forecast
            #   postalKey - uses a post code to source the forecast. Only
            #               supported in US, UK, France, Germany and Italy.
            # The format used for each of the location settings is:
            #   geocode
            #   iataCode, <code>
            #   icaoCode, <code>
            #   placeid, <place ID>
            #   postalKey, <country code>, <postal code>
            # Where:
            #   <code> is the code concerned
            #   <place ID> is the place ID
            #   <country code> is the two letter country code (refer https://docs.google.com/document/d/13HTLgJDpsb39deFzk_YCQ5GoGoZCO_cRYzIxbwvgJLI/edit#heading=h.d5imu8qa7ywg)
            #   <postal code> is the postal code
            # The default is geocode, If gecode is used then the station
            # latitude and longitude are used.
            location = enter location

            # Units to be used in the forecast text. Must be one of the following:
            #   e - English units
            #   m - Metric units
            #   s - SI units
            #   h - Hybrid(UK) units
            # Refer to https://docs.google.com/document/d/13HTLgJDpsb39deFzk_YCQ5GoGoZCO_cRYzIxbwvgJLI/edit#heading=h.ek9jds3g3p9i
            # Default is m.
            units = e|m|s|h

            # Language to be used in the forecast text. Refer to
            # https://docs.google.com/document/d/13HTLgJDpsb39deFzk_YCQ5GoGoZCO_cRYzIxbwvgJLI/edit#heading=h.9ph8uehobq12
            # for available languages and the corresponding language code.
            # Default is en-GB
            language = language code

    -   Darksky forecast

        # Specify settings to be used for Darksky forecast block
        [[DS]]
            # Key used to access Darksky API. String. Mandatory.
            api_key = xxxxxxxxxxxxxxxx

            # Latitude to use for forecast. Decimal degrees, negative for 
            # southern hemisphere. Optional. Default is station latitude.
            latitude = yy.yyyyy

            # Longitude to use for forecast. Decimal degrees, negative for 
            # western hemisphere. Optional. Default is station longitude.
            longitude = zz.zzzz

            # Darksky forecast text to use. String either minutely, hourly or 
            # daily. Optional. Default is hourly. Refer Darksky API 
            # documentation at 
            # https://darksky.net/dev/docs#forecast-request
            block = minutely|hourly|daily

            # Language to use. String. Optional. Default is en (English).
            # Available language codes are listed in the Darksky API
            # documentation at https://darksky.net/dev/docs#forecast-request
            language = en

            # Units to use in forecast text. String either auto, us, si, ca or
            # uk2. Optional. Default is ca. Available units codes are
            # explained in the Darksky API documentation at
            # https://darksky.net/dev/docs#forecast-request
            units = auto|us|si|ca|uk2

            # Interval (in seconds) between forecast downloads. Optional. 
            # Default is 1800.
            interval = 1800

            # Maximum number attempts to obtain an API response. Optional. 
            # Default is 3.
            max_tries = 3

    -   Zambretti forecast

        # Specify settings to be used for Zambretti forecast block
        [[Zambretti]]
            # Interval (in seconds) between forecast updates. Optional. 
            # Default is 1800.
            # Note. In order to use the Zambretti forecast block the weeWX 
            # forecast extension must be installed and the Zambretti forecast
            # enabled. RTGD reads the current Zambretti forecast every interval 
            # seconds. The forecast extension controls how often the Zambretti 
            # forecast is updated.
            interval = 1800
        
            # Maximum number attempts to obtain the forecast. Optional. Default
            # is 3.
            max_tries = 3

            # Time to wait (in seconds) between attempts to read the forecast. 
            # Optional. Default is 3.
            retry_wait = 3

5.  Add the RealtimeGaugeData service to the list of report services under
[Engines] [[WxEngine]] in weewx.conf:

[Engines]
    [[WxEngine]]
        report_services = ..., user.rtgd.RealtimeGaugeData

6.  If you intend to save the realtime generated gauge-data.txt in the same
location as the ss skin generated gauge-data.txt then you must disable the
skin generated gauge-data.txt by commenting out the [[[data]]] entry and all
subordinate settings under [CheetahGenerator] [[ToDate]] in
$SKIN_ROOT/ss/skin.conf:

[CheetahGenerator]
    encoding = html_entities
    [[ToDate]]
        [[[index]]]
            template = index.html.tmpl
        # [[[data]]]
        #     template = gauge-data.txt.tmpl

7.  Edit $SKIN_ROOT/ss/scripts/gauges.js and change the realTimeURL_weewx
setting (circa line 68) to refer to the location of the realtime generated
gauge-data.txt. Change the realtimeInterval setting (circa line 37) to reflect
the update period of the realtime gauge-data.txt in seconds. This setting
controls the count down timer and update frequency of the SteelSeries Weather
Gauges.

8.  Delete the file $HTML_ROOT/ss/scripts/gauges.js.

9.  Stop/start weeWX

10.  Confirm that gauge-data.txt is being generated regularly as per the period
and nth_loop settings under [RealtimeGaugeData] in weewx.conf.

11.  Confirm the SteelSeries Weather Gauges are being updated each time
gauge-data.txt is generated.

To do:
    - hourlyrainTH, ThourlyrainTH and LastRainTipISO. Need to populate these
      fields, presently set to 0.0, 00:00 and 00:00 respectively.
    - Lost contact with station sensors is implemented for Vantage and
      Simulator stations only. Need to extend current code to cater for the
      weeWX supported stations. Current code assume that contact is there
      unless told otherwise.
    - consolidate wind lists into a single list.
    - add windTM to loop packet (a la appTemp in wd.py). windTM is
      calculated as the greater of either (1) max windAv value for the day to
      date (from stats db)or (2) calcFiveMinuteAverageWind which calculates
      average wind speed over the 5 minutes preceding the latest loop packet.
      Should calcFiveMinuteAverageWind produce a max average wind speed then
      this may not be reflected in the stats database as the average wind max
      recorded in stats db is based on archive records only. This is because
      windAv is in an archive record but not in a loop packet. This can be
      remedied by adding the calculated average to the loop packet. weeWX
      normal archive processing will then take care of updating stats db.

Handy things/conditions noted from analysis of SteelSeries Weather Gauges:
    - wind direction is from 1 to 360, 0 is treated as calm ie no wind
    - trend periods are assumed to be one hour except for barometer which is
      taken as three hours
    - wspeed is 10 minute average wind speed (refer to wind speed gauge hover
      and gauges.js
"""

# python imports
import Queue
import datetime
import errno
import httplib
import json
import math
import os
import os.path
import socket
import syslog
import threading
import time
import urllib2

# weeWX imports
import weewx
import weeutil.weeutil
import weewx.units
import weewx.wxformulas
from weewx.engine import StdService
from weewx.units import ValueTuple, convert, getStandardUnitType
from weeutil.weeutil import to_bool, to_int, startOfDay

# version number of this script
RTGD_VERSION = '0.3.6'
# version number (format) of the generated gauge-data.txt
GAUGE_DATA_VERSION = '14'

# ordinal compass points supported
COMPASS_POINTS = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE',
                  'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW', 'N']

# map weeWX unit names to unit names supported by the SteelSeries Weather
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


def logmsg(level, msg):
    syslog.syslog(level, msg)


def logcrit(sid, msg):
    logmsg(syslog.LOG_CRIT, '%s: %s' % (sid, msg))


def logdbg(sid, msg):
    logmsg(syslog.LOG_DEBUG, '%s: %s' % (sid, msg))


def logdbg2(sid, msg):
    if weewx.debug >= 2:
        logmsg(syslog.LOG_DEBUG, '%s: %s' % (sid, msg))


def logdbg3(sid, msg):
    if weewx.debug >= 3:
        logmsg(syslog.LOG_DEBUG, '%s: %s' % (sid, msg))


def loginf(sid, msg):
    logmsg(syslog.LOG_INFO, '%s: %s' % (sid, msg))


def logerr(sid, msg):
    logmsg(syslog.LOG_ERR, '%s: %s' % (sid, msg))


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
    instance of Queue.Queue.
    """

    def __init__(self, engine, config_dict):
        # initialize my superclass
        super(RealtimeGaugeData, self).__init__(engine, config_dict)

        self.rtgd_ctl_queue = Queue.Queue()
        # get our RealtimeGaugeData config dictionary
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
        
        # bind our self to the relevant weeWX events
        self.bind(weewx.NEW_LOOP_PACKET, self.new_loop_packet)
        self.bind(weewx.NEW_ARCHIVE_RECORD, self.new_archive_record)
        self.bind(weewx.END_ARCHIVE_PERIOD, self.end_archive_period)

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
            loginf("rtgd", "Unknown block specified for scroller_text")
            source_class = Source
        # create queues for passing data and controlling our block object
        self.source_ctl_queue = Queue.Queue()
        self.result_queue = Queue.Queue()
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
            logdbg("rtgd",
                   "queued loop packet (%s)" % _package['payload']['dateTime'])
        elif weewx.debug >= 3:
            logdbg("rtgd", "queued loop packet: %s" % _package['payload'])

    def new_archive_record(self, event):
        """Puts archive records in the rtgd queue."""

        # package the archive record in a dict since this is not the only data
        # we send via the queue
        _package = {'type': 'archive',
                    'payload': event.record}
        self.rtgd_ctl_queue.put(_package)
        if weewx.debug == 2:
            logdbg("rtgd",
                   "queued archive record (%s)" % _package['payload']['dateTime'])
        elif weewx.debug >= 3:
            logdbg("rtgd", "queued archive record: %s" % _package['payload'])
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
                logdbg("rtgd", "queued min/max barometer values")
            elif weewx.debug >= 3:
                logdbg("rtgd",
                       "queued min/max barometer values: %s" % _package['payload'])
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
                    logdbg("rtgd", "queued month to date rain")
                elif weewx.debug >= 3:
                    logdbg("rtgd",
                           "queued month to date rain: %s" % _package['payload'])
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
                    logdbg("rtgd", "queued year to date rain")
                elif weewx.debug >= 3:
                    logdbg("rtgd",
                           "queued year to date rain: %s" % _package['payload'])
    
    def end_archive_period(self, event):
        """Puts END_ARCHIVE_PERIOD event in the rtgd queue."""

        # package the event in a dict since this is not the only data we send
        # via the queue
        _package = {'type': 'event',
                    'payload': weewx.END_ARCHIVE_PERIOD}
        self.rtgd_ctl_queue.put(_package)
        logdbg2("rtgd", "queued weewx.END_ARCHIVE_PERIOD event")

    def shutDown(self):
        """Shut down any threads.

        Would normally do all of a given threads actions in one go but since
        we may have more than one thread and so that we don't have sequential
        (potential) waits of up to 15 seconds we send each thread a shutdown
        signal and then go and check that each has indeed shutdown.
        """

        if hasattr(self, 'rtgd_ctl_queue') and hasattr(self, 'rtgd_thread'):
            if self.rtgd_ctl_queue and self.rtgd_thread.isAlive():
                # Put a None in the rtgd_ctl_queue to signal the thread to
                # shutdown
                self.rtgd_ctl_queue.put(None)
        if hasattr(self, 'source_ctl_queue') and hasattr(self, 'source_thread'):
            if self.source_ctl_queue and self.source_thread.isAlive():
                # Put a None in the source_ctl_queue to signal the thread to
                # shutdown
                self.source_ctl_queue.put(None)
        if hasattr(self, 'rtgd_thread') and self.rtgd_thread.isAlive():
            # Wait up to 15 seconds for the thread to exit:
            self.rtgd_thread.join(15.0)
            if self.rtgd_thread.isAlive():
                logerr("rtgd",
                       "Unable to shut down %s thread" % self.rtgd_thread.name)
            else:
                logdbg("rtgd", "Shut down %s thread." % self.rtgd_thread.name)
        if hasattr(self, 'source_thread') and self.source_thread.isAlive():
            # Wait up to 15 seconds for the thread to exit:
            self.source_thread.join(15.0)
            if self.source_thread.isAlive():
                logerr("rtgd",
                       "Unable to shut down %s thread" % self.source_thread.name)
            else:
                logdbg("rtgd", "Shut down %s thread." % self.source_thread.name)

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
#                       class RealtimeGaugeDataThread
# ============================================================================


class RealtimeGaugeDataThread(threading.Thread):
    """Thread that generates gauge-data.txt in near realtime."""

    def __init__(self, control_queue, result_queue, config_dict, manager_dict,
                 latitude, longitude, altitude):
        # Initialize my superclass:
        threading.Thread.__init__(self)

        # setup a few thread things
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

        # get the remote server URL if it exists, if it doesn't set it to None
        self.remote_server_url = rtgd_config_dict.get('remote_server_url', None)
        # timeout to be used for remote URL posts
        self.timeout = to_int(rtgd_config_dict.get('timeout', 2))
        # response text from remote URL if post was successful
        self.response = rtgd_config_dict.get('response_text', None)

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

        # setup max solar rad calcs
        # do we have any?
        calc_dict = config_dict.get('Calculate', {})
        # algorithm
        algo_dict = calc_dict.get('Algorithm', {})
        self.solar_algorithm = algo_dict.get('maxSolarRad', 'RS')
        # atmospheric transmission coefficient [0.7-0.91]
        self.atc = float(calc_dict.get('atc', 0.8))
        # Fail hard if out of range:
        if not 0.7 <= self.atc <= 0.91:
            raise weewx.ViolatedPrecondition("Atmospheric transmission "
                                             "coefficient (%f) out of "
                                             "range [.7-.91]" % self.atc)
        # atmospheric turbidity (2=clear, 4-5=smoggy)
        self.nfac = float(calc_dict.get('nfac', 2))
        # Fail hard if out of range:
        if not 2 <= self.nfac <= 5:
            raise weewx.ViolatedPrecondition("Atmospheric turbidity (%d) "
                                             "out of range (2-5)" % self.nfac)

        # Get our groups and format strings
        self.date_format = rtgd_config_dict.get('date_format',
                                                '%Y.%m.%d %H:%M')
        self.time_format = '%H:%M'
        self.temp_group = rtgd_config_dict['Groups'].get('group_temperature',
                                                         'degree_C')
        self.temp_format = rtgd_config_dict['StringFormats'].get(self.temp_group,
                                                                 '%.1f')
        self.hum_group = 'percent'
        self.hum_format = rtgd_config_dict['StringFormats'].get(self.hum_group,
                                                                '%.0f')
        self.pres_group = rtgd_config_dict['Groups'].get('group_pressure',
                                                         'hPa')
        # SteelSeries Weather Gauges don't understand mmHg so default to hPa
        # if we have been told to use mmHg
        if self.pres_group == 'mmHg':
            self.pres_group = 'hPa'
        self.pres_format = rtgd_config_dict['StringFormats'].get(self.pres_group,
                                                                 '%.1f')
        self.wind_group = rtgd_config_dict['Groups'].get('group_speed',
                                                         'km_per_hour')
        # Since the SteelSeries Weather Gauges derives distance units from wind
        # speed units we cannot use knots because weeWX does not know how to
        # use distance in nautical miles. If we have been told to use knot then
        # default to mile_per_hour.
        if self.wind_group == 'knot':
            self.wind_group = 'mile_per_hour'
        self.wind_format = rtgd_config_dict['StringFormats'].get(self.wind_group,
                                                                 '%.1f')
        self.rain_group = rtgd_config_dict['Groups'].get('group_rain',
                                                         'mm')
        # SteelSeries Weather Gauges don't understand cm so default to mm if we
        # have been told to use cm
        if self.rain_group == 'cm':
            self.rain_group = 'mm'
        self.rain_format = rtgd_config_dict['StringFormats'].get(self.rain_group,
                                                                 '%.1f')
        # SteelSeries Weather gauges derives rain rate units from rain units,
        # so must we
        self.rainrate_group = ''.join([self.rain_group, '_per_hour'])
        self.rainrate_format = rtgd_config_dict['StringFormats'].get(self.rainrate_group,
                                                                     '%.1f')
        self.dir_group = 'degree_compass'
        self.dir_format = rtgd_config_dict['StringFormats'].get(self.dir_group,
                                                                '%.1f')
        self.rad_group = 'watt_per_meter_squared'
        self.rad_format = rtgd_config_dict['StringFormats'].get(self.rad_group,
                                                                '%.0f')
        self.uv_group = 'uv_index'
        self.uv_format = rtgd_config_dict['StringFormats'].get(self.uv_group,
                                                               '%.1f')
        # SteelSeries Weather gauges derives windrun units from wind speed
        # units, so must we
        self.dist_group = GROUP_DIST[self.wind_group]
        self.dist_format = rtgd_config_dict['StringFormats'].get(self.dist_group,
                                                                 '%.1f')
        self.alt_group = rtgd_config_dict['Groups'].get('group_altitude',
                                                        'meter')
        self.alt_format = rtgd_config_dict['StringFormats'].get(self.alt_group,
                                                                '%.1f')
        self.flag_format = '%.0f'

        # what units are incoming packets using
        self.packet_units = None

        # get max cache age
        self.max_cache_age = rtgd_config_dict.get('max_cache_age', 600)

        # initialise last wind directions for use when respective direction is
        # None. We need latest and average
        self.last_latest_dir = 0
        self.last_average_dir = 0

        # Are we updating windrun using archive data only or archive and loop
        # data?
        self.windrun_loop = to_bool(rtgd_config_dict.get('windrun_loop',
                                                         False))

        # weeWX does not normally archive appTemp so day stats are not usually
        # available; however, if the user does have appTemp in a database then
        # if we have a binding we can use it. Check if an appTemp binding was
        # specified, if so use it, otherwise default to 'wx_binding'. We will
        # check for data existence before using it.
        self.apptemp_binding = rtgd_config_dict.get('apptemp_binding',
                                                    'wx_binding')

        # create a RtgdBuffer object to hold our loop 'stats'
        self.buffer = RtgdBuffer()

        # Lost contact
        # do we ignore the lost contact 'calculation'
        self.ignore_lost_contact = to_bool(rtgd_config_dict.get('ignore_lost_contact',
                                                                False))
        # set the lost contact flag, assume we start off with contact
        self.lost_contact_flag = False

        # initialise some properties used to hold archive period wind data
        self.windSpeedAvg_vt = ValueTuple(None, 'km_per_hour', 'group_speed')
        self.windDirAvg = None
        self.min_barometer = None
        self.max_barometer = None

        self.db_manager = None
        self.apptemp_manager = None
        self.day_stats = None
        self.apptemp_day_stats = None

        self.packet_cache = None

        # initialise packet obs types and unit groups
        self.p_temp_type = None
        self.p_temp_group = None
        self.p_wind_type = None
        self.p_wind_group = None
        self.p_baro_type = None
        self.p_baro_group = None
        self.p_rain_type = None
        self.p_rain_group = None
        self.p_rainr_type = None
        self.p_rainr_group = None
        self.p_alt_type = None
        self.p_alt_group = None

        self.rose = None

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
        loginf("rtgdthread", _msg)
        # lost contact
        if self.ignore_lost_contact:
            loginf("rtgdthread", "Sensor contact state will be ignored")

    def run(self):
        """Collect packets from the rtgd queue and manage their processing.

        Now that we are in a thread get a manager for our db so we can
        initialise our forecast and day stats. Once this is done we wait for
        something in the rtgd queue.
        """

        # would normally do this in our objects __init__ but since we are are
        # running in a thread we need to wait until the thread is actually
        # running before getting db managers

        # get a db manager
        self.db_manager = weewx.manager.open_manager(self.manager_dict)
        # get a db manager for appTemp
        self.apptemp_manager = weewx.manager.open_manager_with_config(self.config_dict,
                                                                      self.apptemp_binding)
        # initialise our day stats
        self.day_stats = self.db_manager._get_day_summary(time.time())
        # initialise our day stats from our appTemp block
        self.apptemp_day_stats = self.apptemp_manager._get_day_summary(time.time())
        # get a windrose to start with since it is only on receipt of an
        # archive record
        self.rose = calc_windrose(int(time.time()),
                                  self.db_manager,
                                  self.wr_period,
                                  self.wr_points)
        if weewx.debug == 2:
            logdbg("rtgdthread", "windrose data calculated")
        elif weewx.debug >= 3:
            logdbg("rtgdthread", "windrose data calculated: %s" % (self.rose,))
        # setup our loop cache and set some starting wind values
        _ts = self.db_manager.lastGoodStamp()
        if _ts is not None:
            _rec = self.db_manager.getRecord(_ts)
        else:
            _rec = {'usUnits': None}
        # get a CachedPacket object as our loop packet cache and prime it with
        # values from the last good archive record if available
        self.packet_cache = CachedPacket(_rec)
        logdbg2("rtgdthread", "loop packet cache initialised")
        # save the windSpeed value to use as our archive period average, this
        # needs to be a ValueTuple since we may need to convert units
        if 'windSpeed' in _rec:
            self.windSpeedAvg_vt = weewx.units.as_value_tuple(_rec, 'windSpeed')
        # save the windDir value to use as our archive period average
        if 'windDir' in _rec:
            self.windDirAvg = _rec['windDir']

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
                    except Queue.Empty:
                        # nothing in the queue so continue
                        pass
                    else:
                        # we did get something in the queue but was it a
                        # 'forecast' package
                        if isinstance(_package, dict):
                            if 'type' in _package and _package['type'] == 'forecast':
                                # we have forecast text so log and save it
                                logdbg2("rtgdthread",
                                        "received forecast text: %s" % _package['payload'])
                                self.scroller_text = _package['payload']
                # now deal with the control queue
                try:
                    # block for one second waiting for package, if nothing
                    # received throw Queue.Empty
                    _package = self.control_queue.get(True, 1.0)
                except Queue.Empty:
                    # nothing in the queue so continue
                    pass
                else:
                    # a None record is our signal to exit
                    if _package is None:
                        return
                    elif _package['type'] == 'archive':
                        if weewx.debug == 2:
                            logdbg("rtgdthread",
                                   "received archive record (%s)" % _package['payload']['dateTime'])
                        elif weewx.debug >= 3:
                            logdbg("rtgdthread",
                                   "received archive record: %s" % _package['payload'])
                        self.new_archive_record(_package['payload'])
                        self.rose = calc_windrose(_package['payload']['dateTime'],
                                                  self.db_manager,
                                                  self.wr_period,
                                                  self.wr_points)
                        if weewx.debug == 2:
                            logdbg("rtgdthread", "windrose data calculated")
                        elif weewx.debug >= 3:
                            logdbg("rtgdthread",
                                   "windrose data calculated: %s" % (self.rose,))
                        continue
                    elif _package['type'] == 'event':
                        if _package['payload'] == weewx.END_ARCHIVE_PERIOD:
                            logdbg2("rtgdthread",
                                    "received event - END_ARCHIVE_PERIOD")
                            self.end_archive_period()
                        continue
                    elif _package['type'] == 'stats':
                        if weewx.debug == 2:
                            logdbg("rtgdthread",
                                   "received stats package")
                        elif weewx.debug >= 3:
                            logdbg("rtgdthread",
                                   "received stats package: %s" % _package['payload'])
                        self.process_stats(_package['payload'])
                        continue
                    elif _package['type'] == 'loop':
                        # we now have a packet to process, wrap in a
                        # try..except so we can catch any errors
                        try:
                            if weewx.debug == 2:
                                logdbg("rtgdthread",
                                       "received loop packet (%s)" % _package['payload']['dateTime'])
                            elif weewx.debug >= 3:
                                logdbg("rtgdthread",
                                       "received loop packet: %s" % _package['payload'])
                            self.process_packet(_package['payload'])
                            continue
                        except Exception, e:
                            # Some unknown exception occurred. This is probably
                            # a serious problem. Exit.
                            logcrit("rtgdthread",
                                    "Unexpected exception of type %s" % (type(e), ))
                            weeutil.weeutil.log_traceback('*** ',
                                                          syslog.LOG_DEBUG)
                            logcrit("rtgdthread",
                                    "Thread exiting. Reason: %s" % (e, ))
                            return
                # if packets have backed up in the control queue, trim it until
                # it's no bigger than the max allowed backlog
                while self.control_queue.qsize() > 5:
                    self.control_queue.get()

    def process_packet(self, packet):
        """Process incoming loop packets and generate gauge-data.txt.

        Input:
            packet: dict containing the loop packet to be processed
        """

        # get time for debug timing
        t1 = time.time()
        # update the packet cache with this packet
        self.packet_cache.update(packet, packet['dateTime'])
        # do those things that must be done with every loop packet
        # ie update our lows and highs and our 5 and 10 min wind lists
        self.buffer.set_lows_and_highs(packet)
        # generate if we have no minimum interval setting or if minimum
        # interval seconds have elapsed since our last generation
        if self.min_interval is None or (self.last_write + float(self.min_interval)) < time.time():
            # TODO. Could this try..except be reduced in scope
            try:
                # get a cached packet
                cached_packet = self.packet_cache.get_packet(packet['dateTime'],
                                                             self.max_cache_age)
                if weewx.debug == 2:
                    logdbg("rtgdthread",
                           "created cached loop packet (%s)" % cached_packet['dateTime'])
                elif weewx.debug >= 3:
                    logdbg("rtgdthread",
                           "created cached loop packet: %s" % (cached_packet,))
                # set our lost contact flag if applicable
                self.lost_contact_flag = self.get_lost_contact(cached_packet, 'loop')
                # get a data dict from which to construct our file
                data = self.calculate(cached_packet)
                # write to our file
                self.write_data(data)
                # set our write time
                self.last_write = time.time()
                # if required send the data to a remote URL via HTTP POST
                if self.remote_server_url is not None:
                    # post the data
                    self.post_data(data)
                # log the generation
                logdbg2("rtgdthread",
                        "gauge-data.txt (%s) generated in %.5f seconds" % (cached_packet['dateTime'],
                                                                           (self.last_write-t1)))
            except Exception, e:
                weeutil.weeutil.log_traceback('rtgdthread: **** ')
        else:
            # we skipped this packet so log it
            logdbg2("rtgdthread", "packet (%s) skipped" % packet['dateTime'])

    def process_stats(self, package):
        """Process a stats package.

        Input:
            package: dict containing the stats data to process
        """

        if package is not None:
            for key, value in package.iteritems():
                setattr(self, key, value)

    def post_data(self, data):
        """Post data to a remote URL via HTTP POST.

        This code is modelled on the weeWX restFUL API, but rather then
        retrying a failed post the failure is logged and then ignored. If
        remote posts are not working then the user should set debug=1 and
        restart weeWX to see what the log says.

        The data to be posted is sent as a JSON string.

        Inputs:
            data: dict to sent as JSON string
        """

        # get a Request object
        req = urllib2.Request(self.remote_server_url)
        # set our content type to json
        req.add_header('Content-Type', 'application/json')
        # POST the data but wrap in a try..except so we can trap any errors
        try:
            response = self.post_request(req, json.dumps(data,
                                                         separators=(',', ':'),
                                                         sort_keys=True))
            if 200 <= response.code <= 299:
                # No exception thrown and we got a good response code, but did
                # we get self.response back in a return message? Check for
                # self.response, if its there then we can return. If it's
                # not there then log it and return.
                if self.response is not None:
                    if self.response in response:
                        # did get 'success' so log it and continue
                        logdbg2("rtgdthread", "Successfully posted data")
                    else:
                        # didn't get 'success' so log it and continue
                        logdbg("rtgdthread",
                               "Failed to post data: Unexpected response")
                return
            # we received a bad response code, log it and continue
            logdbg("rtgdthread",
                   "Failed to post data: Code %s" % response.code())
        except (urllib2.URLError, socket.error,
                httplib.BadStatusLine, httplib.IncompleteRead), e:
            # an exception was thrown, log it and continue
            logdbg("rtgdthread", "Failed to post data: %s" % e)

    def post_request(self, request, payload):
        """Post a Request object.

        Inputs:
            request: urllib2 Request object
            payload: the data to sent

        Returns:
            The urllib2.urlopen() response
        """

        try:
            # Python 2.5 and earlier do not have a "timeout" parameter.
            # Including one could cause a TypeError exception. Be prepared
            # to catch it.
            _response = urllib2.urlopen(request,
                                        data=payload,
                                        timeout=self.timeout)
        except TypeError:
            # Must be Python 2.5 or early. Use a simple, unadorned request
            _response = urllib2.urlopen(request, data=payload)
        return _response

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

    def calculate(self, packet):
        """Construct a data dict for gauge-data.txt.

        Input:
            packet: loop data packet

        Returns:
            Dictionary of gauge-data.txt data elements.
        """

        packet_d = dict(packet)
        ts = packet_d['dateTime']
        if self.packet_units is None or self.packet_units != packet_d['usUnits']:
            self.packet_units = packet_d['usUnits']
            (self.p_temp_type, self.p_temp_group) = getStandardUnitType(self.packet_units,
                                                                        'outTemp')
            (self.p_wind_type, self.p_wind_group) = getStandardUnitType(self.packet_units,
                                                                        'windSpeed')
            (self.p_baro_type, self.p_baro_group) = getStandardUnitType(self.packet_units,
                                                                        'barometer')
            (self.p_rain_type, self.p_rain_group) = getStandardUnitType(self.packet_units,
                                                                        'rain')
            (self.p_rainr_type, self.p_rainr_group) = getStandardUnitType(self.packet_units,
                                                                          'rainRate')
            (self.p_alt_type, self.p_alt_group) = getStandardUnitType(self.packet_units,
                                                                      'altitude')
        data = dict()
        # timeUTC - UTC date/time in format YYYY,mm,dd,HH,MM,SS
        data['timeUTC'] = datetime.datetime.utcfromtimestamp(ts).strftime("%Y,%m,%d,%H,%M,%S")
        # date - date in (default) format Y.m.d HH:MM
        data['date'] = time.strftime(self.date_format, time.localtime(ts))
        # dateFormat - date format
        data['dateFormat'] = self.date_format.replace('%', '')
        # SensorContactLost - 1 if the station has lost contact with its remote
        # sensors "Fine Offset only" 0 if contact has been established
        data['SensorContactLost'] = self.flag_format % self.lost_contact_flag
        # tempunit - temperature units - C, F
        data['tempunit'] = UNITS_TEMP[self.temp_group]
        # windunit -wind units - m/s, mph, km/h, kts
        data['windunit'] = UNITS_WIND[self.wind_group]
        # pressunit - pressure units - mb, hPa, in
        data['pressunit'] = UNITS_PRES[self.pres_group]
        # rainunit - rain units - mm, in
        data['rainunit'] = UNITS_RAIN[self.rain_group]
        # cloudbaseunit - cloud base units - m, ft
        data['cloudbaseunit'] = UNITS_CLOUD[self.alt_group]
        # temp - outside temperature
        temp_vt = ValueTuple(packet_d['outTemp'],
                             self.p_temp_type,
                             self.p_temp_group)
        temp = convert(temp_vt, self.temp_group).value
        temp = temp if temp is not None else convert(ValueTuple(0.0, 'degree_C', 'group_temperature'),
                                                     self.temp_group).value
        data['temp'] = self.temp_format % temp
        # tempTL - today's low temperature
        temp_tl_vt = ValueTuple(self.day_stats['outTemp'].min,
                                self.p_temp_type,
                                self.p_temp_group)
        temp_tl = convert(temp_tl_vt, self.temp_group).value
        temp_tl_loop_vt = ValueTuple(self.buffer.tempL_loop[0],
                                     self.p_temp_type,
                                     self.p_temp_group)
        temp_l_loop = convert(temp_tl_loop_vt, self.temp_group).value
        temp_tl = weeutil.weeutil.min_with_none([temp_l_loop, temp_tl])
        temp_tl = temp_tl if temp_tl is not None else temp
        data['tempTL'] = self.temp_format % temp_tl
        # tempTH - today's high temperature
        temp_th_vt = ValueTuple(self.day_stats['outTemp'].max,
                                self.p_temp_type,
                                self.p_temp_group)
        temp_th = convert(temp_th_vt, self.temp_group).value
        temp_th_loop_vt = ValueTuple(self.buffer.tempH_loop[0],
                                     self.p_temp_type,
                                     self.p_temp_group)
        temp_h_loop = convert(temp_th_loop_vt, self.temp_group).value
        temp_th = max(temp_h_loop, temp_th)
        temp_th = temp_th if temp_th is not None else temp
        data['tempTH'] = self.temp_format % temp_th
        # TtempTL - time of today's low temp (hh:mm)
        ttemp_tl = time.localtime(self.day_stats['outTemp'].mintime) if temp_l_loop >= temp_tl else \
            time.localtime(self.buffer.tempL_loop[1])
        data['TtempTL'] = time.strftime(self.time_format, ttemp_tl)
        # TtempTH - time of today's high temp (hh:mm)
        ttemp_th = time.localtime(self.day_stats['outTemp'].maxtime) if temp_h_loop <= temp_th else \
            time.localtime(self.buffer.tempH_loop[1])
        data['TtempTH'] = time.strftime(self.time_format, ttemp_th)
        # temptrend - temperature trend value
        _temp_trend_val = calc_trend('outTemp', temp_vt, self.temp_group,
                                     self.db_manager, ts - 3600, 300)
        temp_trend = _temp_trend_val if _temp_trend_val is not None else 0.0
        data['temptrend'] = self.temp_format % temp_trend
        # intemp - inside temperature
        intemp_vt = ValueTuple(packet_d['inTemp'],
                               self.p_temp_type,
                               self.p_temp_group)
        intemp = convert(intemp_vt, self.temp_group).value
        intemp = intemp if intemp is not None else 0.0
        data['intemp'] = self.temp_format % intemp
        # intempTL - today's low inside temperature
        intemp_tl_vt = ValueTuple(self.day_stats['inTemp'].min,
                                  self.p_temp_type,
                                  self.p_temp_group)
        intemp_tl = convert(intemp_tl_vt, self.temp_group).value
        intemp_tl_loop_vt = ValueTuple(self.buffer.tempL_loop[0],
                                       self.p_temp_type,
                                       self.p_temp_group)
        intemp_l_loop = convert(intemp_tl_loop_vt, self.temp_group).value
        intemp_tl = weeutil.weeutil.min_with_none([intemp_l_loop, intemp_tl])
        intemp_tl = intemp_tl if intemp_tl is not None else temp
        data['intempTL'] = self.temp_format % intemp_tl
        # intempTH - today's high inside temperature
        intemp_th_vt = ValueTuple(self.day_stats['inTemp'].max,
                                  self.p_temp_type,
                                  self.p_temp_group)
        intemp_th = convert(intemp_th_vt, self.temp_group).value
        intemp_th_loop_vt = ValueTuple(self.buffer.intempH_loop[0],
                                       self.p_temp_type,
                                       self.p_temp_group)
        intemp_h_loop = convert(intemp_th_loop_vt, self.temp_group).value
        intemp_th = max(intemp_h_loop, intemp_th)
        intemp_th = intemp_th if intemp_th is not None else temp
        data['tempTH'] = self.temp_format % intemp_th
        # TintempTL - time of today's low inside temp (hh:mm)
        tintemp_tl = time.localtime(self.day_stats['inTemp'].mintime) if intemp_l_loop >= intemp_tl else \
            time.localtime(self.buffer.intempL_loop[1])
        data['TintempTL'] = time.strftime(self.time_format, tintemp_tl)
        # TintempTH - time of today's high inside temp (hh:mm)
        tintemp_th = time.localtime(self.day_stats['inTemp'].maxtime) if intemp_h_loop <= intemp_th else \
            time.localtime(self.buffer.intempH_loop[1])
        data['TtempTH'] = time.strftime(self.time_format, tintemp_th)
        # hum - relative humidity
        hum = packet_d['outHumidity'] if packet_d['outHumidity'] is not None else 0.0
        data['hum'] = self.hum_format % hum
        # humTL - today's low relative humidity
        hum_tl = weeutil.weeutil.min_with_none([self.buffer.humL_loop[0],
                                               self.day_stats['outHumidity'].min])
        hum_tl = hum_tl if hum_tl is not None else hum
        data['humTL'] = self.hum_format % hum_tl
        # humTH - today's high relative humidity
        hum_th = max(self.buffer.humH_loop[0], self.day_stats['outHumidity'].max, 0.0)
        hum_th = hum_th if hum_th is not None else hum
        data['humTH'] = self.hum_format % hum_th
        # ThumTL - time of today's low relative humidity (hh:mm)
        thum_tl = time.localtime(self.day_stats['outHumidity'].mintime) if self.buffer.humL_loop[0] >= hum_tl else \
            time.localtime(self.buffer.humL_loop[1])
        data['ThumTL'] = time.strftime(self.time_format, thum_tl)
        # ThumTH - time of today's high relative humidity (hh:mm)
        thum_th = time.localtime(self.day_stats['outHumidity'].maxtime) if self.buffer.humH_loop[0] <= hum_th else \
            time.localtime(self.buffer.humH_loop[1])
        data['ThumTH'] = time.strftime(self.time_format, thum_th)
        # inhum - inside humidity
        if 'inHumidity' not in packet_d:
            data['inhum'] = self.hum_format % 0.0
        else:
            inhum = packet_d['inHumidity'] if packet_d['inHumidity'] is not None else 0.0
            data['inhum'] = self.hum_format % inhum
        # dew - dew point
        dew_vt = ValueTuple(packet_d['dewpoint'],
                            self.p_temp_type,
                            self.p_temp_group)
        dew = convert(dew_vt, self.temp_group).value
        dew = dew if dew is not None else convert(ValueTuple(0.0, 'degree_C', 'group_temperature'),
                                                  self.temp_group).value
        data['dew'] = self.temp_format % dew
        # dewpointTL - today's low dew point
        dewpoint_tl_vt = ValueTuple(self.day_stats['dewpoint'].min,
                                    self.p_temp_type,
                                    self.p_temp_group)
        dewpoint_tl = convert(dewpoint_tl_vt, self.temp_group).value
        dewpoint_tl_loop_vt = ValueTuple(self.buffer.dewpointL_loop[0],
                                         self.p_temp_type,
                                         self.p_temp_group)
        dewpoint_l_loop = convert(dewpoint_tl_loop_vt, self.temp_group).value
        dewpoint_tl = weeutil.weeutil.min_with_none([dewpoint_l_loop, dewpoint_tl])
        dewpoint_tl = dewpoint_tl if dewpoint_tl is not None else dew
        data['dewpointTL'] = self.temp_format % dewpoint_tl
        # dewpointTH - today's high dew point
        dewpoint_th_vt = ValueTuple(self.day_stats['dewpoint'].max,
                                    self.p_temp_type,
                                    self.p_temp_group)
        dewpoint_th = convert(dewpoint_th_vt, self.temp_group).value
        dewpoint_th_loop_vt = ValueTuple(self.buffer.dewpointH_loop[0],
                                         self.p_temp_type,
                                         self.p_temp_group)
        dewpoint_h_loop = convert(dewpoint_th_loop_vt, self.temp_group).value
        dewpoint_th = max(dewpoint_h_loop, dewpoint_th)
        dewpoint_th = dewpoint_th if dewpoint_th is not None else dew
        data['dewpointTH'] = self.temp_format % dewpoint_th
        # TdewpointTL - time of today's low dew point (hh:mm)
        tdewpoint_tl = time.localtime(self.day_stats['dewpoint'].mintime) if dewpoint_l_loop >= dewpoint_tl else \
            time.localtime(self.buffer.dewpointL_loop[1])
        data['TdewpointTL'] = time.strftime(self.time_format, tdewpoint_tl)
        # TdewpointTH - time of today's high dew point (hh:mm)
        tdewpoint_th = time.localtime(self.day_stats['dewpoint'].maxtime) if dewpoint_h_loop <= dewpoint_th else \
            time.localtime(self.buffer.dewpointH_loop[1])
        data['TdewpointTH'] = time.strftime(self.time_format, tdewpoint_th)
        # wchill - wind chill
        wchill_vt = ValueTuple(packet_d['windchill'],
                               self.p_temp_type,
                               self.p_temp_group)
        wchill = convert(wchill_vt, self.temp_group).value
        wchill = wchill if wchill is not None else convert(ValueTuple(0.0, 'degree_C', 'group_temperature'),
                                                           self.temp_group).value
        data['wchill'] = self.temp_format % wchill
        # wchillTL - today's low wind chill
        wchill_tl_vt = ValueTuple(self.day_stats['windchill'].min,
                                  self.p_temp_type,
                                  self.p_temp_group)
        wchill_tl = convert(wchill_tl_vt, self.temp_group).value
        wchill_tl_loop_vt = ValueTuple(self.buffer.wchillL_loop[0],
                                       self.p_temp_type,
                                       self.p_temp_group)
        wchill_l_loop = convert(wchill_tl_loop_vt, self.temp_group).value
        wchill_tl = weeutil.weeutil.min_with_none([wchill_l_loop, wchill_tl])
        wchill_tl = wchill_tl if wchill_tl is not None else wchill
        data['wchillTL'] = self.temp_format % wchill_tl
        # TwchillTL - time of today's low wind chill (hh:mm)
        twchill_tl = time.localtime(self.day_stats['windchill'].mintime) if wchill_l_loop >= wchill_tl else \
            time.localtime(self.buffer.wchillL_loop[1])
        data['TwchillTL'] = time.strftime(self.time_format, twchill_tl)
        # heatindex - heat index
        heatindex_vt = ValueTuple(packet_d['heatindex'],
                                  self.p_temp_type,
                                  self.p_temp_group)
        heatindex = convert(heatindex_vt, self.temp_group).value
        heatindex = heatindex if heatindex is not None else convert(ValueTuple(0.0, 'degree_C', 'group_temperature'),
                                                                    self.temp_group).value
        data['heatindex'] = self.temp_format % heatindex
        # heatindexTH - today's high heat index
        heatindex_th_vt = ValueTuple(self.day_stats['heatindex'].max,
                                     self.p_temp_type,
                                     self.p_temp_group)
        heatindex_th = convert(heatindex_th_vt, self.temp_group).value
        heatindex_th_loop_vt = ValueTuple(self.buffer.heatindexH_loop[0],
                                          self.p_temp_type,
                                          self.p_temp_group)
        heatindex_h_loop = convert(heatindex_th_loop_vt, self.temp_group).value
        heatindex_th = max(heatindex_h_loop, heatindex_th)
        heatindex_th = heatindex_th if heatindex_th is not None else heatindex
        data['heatindexTH'] = self.temp_format % heatindex_th
        # TheatindexTH - time of today's high heat index (hh:mm)
        theatindex_th = time.localtime(self.day_stats['heatindex'].maxtime) if heatindex_h_loop >= heatindex_th else \
            time.localtime(self.buffer.heatindexH_loop[1])
        data['TheatindexTH'] = time.strftime(self.time_format, theatindex_th)
        # apptemp - apparent temperature
        if 'appTemp' in packet_d:
            # appTemp has been calculated for us so use it
            apptemp_vt = ValueTuple(packet_d['appTemp'],
                                    self.p_temp_type,
                                    self.p_temp_group)
        else:
            # apptemp not available so calculate it
            # first get the arguments for the calculation
            temp_c = convert(temp_vt, 'degree_C').value
            windspeed_vt = ValueTuple(packet_d['windSpeed'],
                                      self.p_wind_type,
                                      self.p_wind_group)
            windspeed_ms = convert(windspeed_vt, 'meter_per_second').value
            # now calculate it
            apptemp_c = weewx.wxformulas.apptempC(temp_c,
                                                  packet_d['outHumidity'],
                                                  windspeed_ms)
            apptemp_vt = ValueTuple(apptemp_c, 'degree_C', 'group_temperature')
        apptemp = convert(apptemp_vt, self.temp_group).value
        apptemp = apptemp if apptemp is not None else convert(ValueTuple(0.0, 'degree_C', 'group_temperature'),
                                                              self.temp_group).value
        data['apptemp'] = self.temp_format % apptemp
        # apptempTL - today's low apparent temperature
        # apptempTH - today's high apparent temperature
        # TapptempTL - time of today's low apparent temperature (hh:mm)
        # TapptempTH - time of today's high apparent temperature (hh:mm)
        if 'appTemp' in self.apptemp_day_stats:
            # we have day stats for appTemp
            apptemp_tl_vt = ValueTuple(self.apptemp_day_stats['appTemp'].min,
                                       self.p_temp_type,
                                       self.p_temp_group)
            apptemp_tl = convert(apptemp_tl_vt, self.temp_group).value
            apptemp_tl_loop_vt = ValueTuple(self.buffer.apptempL_loop[0],
                                            self.p_temp_type,
                                            self.p_temp_group)
            apptemp_l_loop = convert(apptemp_tl_loop_vt, self.temp_group).value
            apptemp_tl = weeutil.weeutil.min_with_none([apptemp_l_loop, apptemp_tl])
            apptemp_th_vt = ValueTuple(self.apptemp_day_stats['appTemp'].max,
                                       self.p_temp_type,
                                       self.p_temp_group)
            apptemp_th = convert(apptemp_th_vt, self.temp_group).value
            apptemp_th_loop_vt = ValueTuple(self.buffer.apptempH_loop[0],
                                            self.p_temp_type,
                                            self.p_temp_group)
            apptemp_h_loop = convert(apptemp_th_loop_vt, self.temp_group).value
            apptemp_th = max(apptemp_h_loop, apptemp_th)
            tapptemp_tl = time.localtime(self.apptemp_day_stats['appTemp'].mintime) if \
                apptemp_l_loop >= apptemp_tl else \
                time.localtime(self.buffer.apptempL_loop[1])
            tapptemp_th = time.localtime(self.apptemp_day_stats['appTemp'].maxtime) if \
                apptemp_h_loop <= apptemp_th else \
                time.localtime(self.buffer.apptempH_loop[1])
        else:
            # There are no appTemp day stats. Normally we would return None but
            # the SteelSeries Gauges do not like None/null. Return the current
            # appTemp value so as to not upset the gauge auto scaling. The day
            # apptemp range wedge will not show, and the mouse-over low/highs
            # will be wrong but it is the best we can do.
            apptemp_tl = apptemp
            apptemp_th = apptemp
            tapptemp_tl = datetime.date.today().timetuple()
            tapptemp_th = datetime.date.today().timetuple()
        apptemp_tl = apptemp_tl if apptemp_tl is not None else \
            convert(ValueTuple(0.0, 'degree_C', 'group_temperature'), self.temp_group).value
        data['apptempTL'] = self.temp_format % apptemp_tl
        apptemp_th = apptemp_th if apptemp_th is not None else \
            convert(ValueTuple(0.0, 'degree_C', 'group_temperature'), self.temp_group).value
        data['apptempTH'] = self.temp_format % apptemp_th
        data['TapptempTL'] = time.strftime(self.time_format, tapptemp_tl)
        data['TapptempTH'] = time.strftime(self.time_format, tapptemp_th)
        # humidex - humidex
        if 'humidex' in packet_d:
            # humidex is in the packet so use it
            humidex_vt = ValueTuple(packet_d['humidex'],
                                    self.p_temp_type,
                                    self.p_temp_group)
            humidex = convert(humidex_vt, self.temp_group).value
        else:   # No humidex in our loop packet so all we can do is calculate it.
            # humidex is not in the packet so calculate it
            temp_c = convert(temp_vt, 'degree_C').value
            humidex_c = weewx.wxformulas.humidexC(temp_c,
                                                  packet_d['outHumidity'])
            humidex_vt = ValueTuple(humidex_c, 'degree_C', 'group_temperature')
            humidex = convert(humidex_vt, self.temp_group).value
        humidex = humidex if humidex is not None else \
            convert(ValueTuple(0.0, 'degree_C', 'group_temperature'), self.temp_group).value
        data['humidex'] = self.temp_format % humidex
        # press - barometer
        press_vt = ValueTuple(packet_d['barometer'],
                              self.p_baro_type,
                              self.p_baro_group)
        press = convert(press_vt, self.pres_group).value
        press = press if press is not None else 0.0
        data['press'] = self.pres_format % press
        # pressTL - today's low barometer
        # pressTH - today's high barometer
        # TpressTL - time of today's low barometer (hh:mm)
        # TpressTH - time of today's high barometer (hh:mm)
        if 'barometer' in self.day_stats:
            press_tl_vt = ValueTuple(self.day_stats['barometer'].min,
                                     self.p_baro_type,
                                     self.p_baro_group)
            press_tl = convert(press_tl_vt, self.pres_group).value
            press_l_loop_vt = ValueTuple(self.buffer.pressL_loop[0],
                                         self.p_baro_type,
                                         self.p_baro_group)
            press_l_loop = convert(press_l_loop_vt, self.pres_group).value
            press_tl = weeutil.weeutil.min_with_none([press_l_loop, press_tl])
            press_tl = press_tl if press_tl is not None else press
            data['pressTL'] = self.pres_format % press_tl
            press_th_vt = ValueTuple(self.day_stats['barometer'].max,
                                     self.p_baro_type,
                                     self.p_baro_group)
            press_th = convert(press_th_vt, self.pres_group).value
            press_h_loop_vt = ValueTuple(self.buffer.pressH_loop[0],
                                         self.p_baro_type,
                                         self.p_baro_group)
            press_h_loop = convert(press_h_loop_vt, self.pres_group).value
            press_th = max(press_h_loop, press_th, 0.0)
            data['pressTH'] = self.pres_format % press_th
            tpress_tl = time.localtime(self.day_stats['barometer'].mintime) if press_l_loop >= press_tl else \
                time.localtime(self.buffer.pressL_loop[1])
            data['TpressTL'] = time.strftime(self.time_format, tpress_tl)
            tpress_th = time.localtime(self.day_stats['barometer'].maxtime) if press_h_loop <= press_th else \
                time.localtime(self.buffer.pressH_loop[1])
            data['TpressTH'] = time.strftime(self.time_format, tpress_th)
        else:
            data['pressTL'] = self.pres_format % 0.0
            data['pressTH'] = self.pres_format % 0.0
            data['TpressTL'] = None
            data['TpressTH'] = None
        # pressL - all time low barometer
        if self.min_barometer is not None:
            press_l_vt = ValueTuple(self.min_barometer,
                                    self.p_baro_type,
                                    self.p_baro_group)
        else:
            press_l_vt = ValueTuple(850, 'hPa', self.p_baro_group)
        press_l = convert(press_l_vt, self.pres_group).value
        data['pressL'] = self.pres_format % press_l
        # pressH - all time high barometer
        if self.max_barometer is not None:
            press_h_vt = ValueTuple(self.max_barometer,
                                    self.p_baro_type,
                                    self.p_baro_group)
        else:
            press_h_vt = ValueTuple(1100, 'hPa', self.p_baro_group)
        press_h = convert(press_h_vt, self.pres_group).value
        data['pressH'] = self.pres_format % press_h
        # presstrendval -  pressure trend value
        _p_trend_val = calc_trend('barometer', press_vt, self.pres_group,
                                  self.db_manager, ts - 3600, 300)
        presstrendval = _p_trend_val if _p_trend_val is not None else 0.0
        data['presstrendval'] = self.pres_format % presstrendval
        # rfall - rain today
        rain_day = self.day_stats['rain'].sum + self.buffer.rainsum
        rain_t_vt = ValueTuple(rain_day, self.p_rain_type, self.p_rain_group)
        rain_t = convert(rain_t_vt, self.rain_group).value
        rain_t = rain_t if rain_t is not None else 0.0
        data['rfall'] = self.rain_format % rain_t
        # rrate - current rain rate (per hour)
        if 'rainRate' in packet_d:
            rrate_vt = ValueTuple(packet_d['rainRate'],
                                  self.p_rainr_type,
                                  self.p_rainr_group)
            rrate = convert(rrate_vt, self.rainrate_group).value if rrate_vt.value is not None else 0.0
        else:
            rrate = 0.0
        data['rrate'] = self.rainrate_format % rrate
        # rrateTM - today's maximum rain rate (per hour)
        if 'rainRate' in self.day_stats:
            rrate_tm_vt = ValueTuple(self.day_stats['rainRate'].max,
                                     self.p_rainr_type,
                                     self.p_rainr_group)
            rrate_tm = convert(rrate_tm_vt, self.rainrate_group).value
        else:
            rrate_tm = 0
        rrate_tm_loop_vt = ValueTuple(self.buffer.rrateH_loop[0], self.p_rainr_type, self.p_rainr_group)
        rrate_h_loop = convert(rrate_tm_loop_vt, self.rainrate_group).value
        rrate_tm = max(rrate_h_loop, rrate_tm, rrate, 0.0)
        data['rrateTM'] = self.rainrate_format % rrate_tm
        # TrrateTM - time of today's maximum rain rate (per hour)
        if 'rainRate' not in self.day_stats:
            data['TrrateTM'] = '00:00'
        else:
            trrate_tm = time.localtime(self.day_stats['rainRate'].maxtime) if rrate_h_loop <= rrate_tm else \
                time.localtime(self.buffer.rrateH_loop[1])
            data['TrrateTM'] = time.strftime(self.time_format, trrate_tm)
        # hourlyrainTH - Today's highest hourly rain
        # FIXME. Need to determine hourlyrainTH
        data['hourlyrainTH'] = "0.0"
        # ThourlyrainTH - time of Today's highest hourly rain
        # FIXME. Need to determine ThourlyrainTH
        data['ThourlyrainTH'] = "00:00"
        # LastRainTipISO -
        # FIXME. Need to determine LastRainTipISO
        data['LastRainTipISO'] = "00:00"
        # wlatest - latest wind speed reading
        wlatest_vt = ValueTuple(packet_d['windSpeed'],
                                self.p_wind_type,
                                self.p_wind_group)
        wlatest = convert(wlatest_vt, self.wind_group).value if wlatest_vt.value is not None else 0.0
        data['wlatest'] = self.wind_format % wlatest
        # wspeed - wind speed (average)
        wspeed = convert(self.windSpeedAvg_vt, self.wind_group).value
        wspeed = wspeed if wspeed is not None else 0.0
        data['wspeed'] = self.wind_format % wspeed
        # windTM - today's high wind speed (average)
        wind_tm_vt = ValueTuple(self.day_stats['windSpeed'].max,
                                self.p_wind_type,
                                self.p_wind_group)
        wind_tm = convert(wind_tm_vt, self.wind_group).value
        wind_tm_loop_vt = ValueTuple(self.buffer.windM_loop[0],
                                     self.p_wind_type,
                                     self.p_wind_group)
        wind_m_loop = convert(wind_tm_loop_vt, self.wind_group).value
        wind_tm = max(wind_m_loop, wind_tm, 0.0)
        data['windTM'] = self.wind_format % wind_tm
        # wgust - 10 minute high gust
        wgust = self.buffer.ten_minute_wind_gust()
        wgust_vt = ValueTuple(wgust, self.p_wind_type, self.p_wind_group)
        wgust = convert(wgust_vt, self.wind_group).value
        wgust = wgust if wgust is not None else 0.0
        data['wgust'] = self.wind_format % wgust
        # wgustTM - today's high wind gust
        wgust_tm_vt = ValueTuple(self.day_stats['wind'].max,
                                 self.p_wind_type,
                                 self.p_wind_group)
        wgust_tm = convert(wgust_tm_vt, self.wind_group).value
        wgust_m_loop_vt = ValueTuple(self.buffer.wgustM_loop[0],
                                     self.p_wind_type,
                                     self.p_wind_group)
        wgust_m_loop = convert(wgust_m_loop_vt, self.wind_group).value
        wgust_tm = max(wgust_m_loop, wgust_tm, 0.0)
        data['wgustTM'] = self.wind_format % wgust_tm
        # TwgustTM - time of today's high wind gust (hh:mm)
        twgust_tm = time.localtime(self.day_stats['wind'].maxtime) if wgust_m_loop <= wgust_tm else \
            time.localtime(self.buffer.wgustM_loop[2])
        data['TwgustTM'] = time.strftime(self.time_format, twgust_tm)
        # bearing - wind bearing (degrees)
        bearing = packet_d['windDir'] if packet_d['windDir'] is not None else self.last_latest_dir
        self.last_latest_dir = bearing
        data['bearing'] = self.dir_format % bearing
        # avgbearing - 10-minute average wind bearing (degrees)
        avg_bearing = self.windDirAvg if self.windDirAvg is not None else self.last_average_dir
        self.last_average_dir = avg_bearing
        data['avgbearing'] = self.dir_format % avg_bearing
        # bearingTM - The wind bearing at the time of today's high gust
        # As our self.day_stats is really a weeWX accumulator filled with the
        # relevant days stats we need to use .max_dir rather than .gustdir
        # to get the gust direction for the day.
        bearing_tm = self.day_stats['wind'].max_dir if self.day_stats['wind'].max_dir is not None else 0
        bearing_tm = self.buffer.wgustM_loop[1] if wgust_tm == wgust_m_loop else bearing_tm
        data['bearingTM'] = self.dir_format % bearing_tm
        # BearingRangeFrom10 - The 'lowest' bearing in the last 10 minutes
        # (or as configured using AvgBearingMinutes in cumulus.ini), rounded
        # down to nearest 10 degrees
        if self.windDirAvg is not None:
            try:
                from_bearing = max((self.windDirAvg-d) if ((d-self.windDirAvg) < 0 < s) else
                                   None for x, y, s, d, t in self.buffer.wind_dir_list)
            except (TypeError, ValueError):
                from_bearing = None
            bearing_range_from10 = self.windDirAvg - from_bearing if from_bearing is not None else 0.0
            if bearing_range_from10 < 0:
                bearing_range_from10 += 360
            elif bearing_range_from10 > 360:
                bearing_range_from10 -= 360
        else:
            bearing_range_from10 = 0.0
        data['BearingRangeFrom10'] = self.dir_format % bearing_range_from10
        # BearingRangeTo10 - The 'highest' bearing in the last 10 minutes
        # (or as configured using AvgBearingMinutes in cumulus.ini), rounded
        # up to the nearest 10 degrees
        if self.windDirAvg is not None:
            try:
                to_bearing = max((d-self.windDirAvg) if ((d-self.windDirAvg) > 0 and s > 0) else
                                 None for x, y, s, d, t in self.buffer.wind_dir_list)
            except (TypeError, ValueError):
                to_bearing = None
            bearing_range_to10 = self.windDirAvg + to_bearing if to_bearing is not None else 0.0
            if bearing_range_to10 < 0:
                bearing_range_to10 += 360
            elif bearing_range_to10 > 360:
                bearing_range_to10 -= 360
        else:
            bearing_range_to10 = 0.0
        data['BearingRangeTo10'] = self.dir_format % bearing_range_to10
        # domwinddir - Today's dominant wind direction as compass point
        deg = 90.0 - math.degrees(math.atan2(self.day_stats['wind'].ysum,
                                  self.day_stats['wind'].xsum))
        dom_dir = deg if deg >= 0 else deg + 360.0
        data['domwinddir'] = degree_to_compass(dom_dir)
        # WindRoseData -
        data['WindRoseData'] = self.rose
        # windrun - wind run (today)
        last_ts = self.db_manager.lastGoodStamp()
        try:
            wind_sum_vt = ValueTuple(self.day_stats['wind'].sum,
                                     self.p_wind_type,
                                     self.p_wind_group)
            windrun_day_average = (last_ts - startOfDay(ts))/3600.0 * \
                convert(wind_sum_vt, self.wind_group).value/self.day_stats['wind'].count
        except (ValueError, TypeError, ZeroDivisionError):
            windrun_day_average = 0.0
        if self.windrun_loop:   # is loop/realtime estimate
            loop_hours = (ts - last_ts)/3600.0
            try:
                windrun = windrun_day_average + loop_hours * convert((self.buffer.windsum,
                                                                      self.p_wind_type,
                                                                      self.p_wind_group),
                                                                     self.wind_group).value/self.buffer.windcount
            except (ValueError, TypeError):
                windrun = windrun_day_average
        else:
            windrun = windrun_day_average
        data['windrun'] = self.dist_format % windrun
        # Tbeaufort - wind speed (Beaufort)
        if packet_d['windSpeed'] is not None:
            data['Tbeaufort'] = str(weewx.wxformulas.beaufort(convert(wlatest_vt,
                                                                      'knot').value))
        else:
            data['Tbeaufort'] = "0"
        # UV - UV index
        if 'UV' not in packet_d:
            uv = 0.0
        else:
            uv = packet_d['UV'] if packet_d['UV'] is not None else 0.0
        data['UV'] = self.uv_format % uv
        # UVTH - today's high UV index
        if 'UV' not in self.day_stats:
            uv_th = uv
        else:
            uv_th = self.day_stats['UV'].max
        uv_th = max(self.buffer.UVH_loop[0], uv_th, uv, 0.0)
        data['UVTH'] = self.uv_format % uv_th
        # SolarRad - solar radiation W/m2
        if 'radiation' not in packet_d:
            solar_rad = 0.0
        else:
            solar_rad = packet_d['radiation']
        solar_rad = solar_rad if solar_rad is not None else 0.0
        data['SolarRad'] = self.rad_format % solar_rad
        # SolarTM - today's maximum solar radiation W/m2
        if 'radiation' not in self.day_stats:
            solar_tm = 0.0
        else:
            solar_tm = self.day_stats['radiation'].max
        solar_tm = max(self.buffer.SolarH_loop[0], solar_tm, solar_rad, 0.0)
        data['SolarTM'] = self.rad_format % solar_tm
        # CurrentSolarMax - Current theoretical maximum solar radiation
        if self.solar_algorithm == 'Bras':
            curr_solar_max = weewx.wxformulas.solar_rad_Bras(self.latitude,
                                                             self.longitude,
                                                             self.altitude_m,
                                                             ts,
                                                             self.nfac)
        else:
            curr_solar_max = weewx.wxformulas.solar_rad_RS(self.latitude,
                                                           self.longitude,
                                                           self.altitude_m,
                                                           ts,
                                                           self.atc)
        curr_solar_max = curr_solar_max if curr_solar_max is not None else 0.0
        data['CurrentSolarMax'] = self.rad_format % curr_solar_max
        if 'cloudbase' in packet_d:
            cb = packet_d['cloudbase']
            cb_vt = ValueTuple(cb, self.p_alt_type, self.p_alt_group)
        else:
            temp_c = convert(temp_vt, 'degree_C').value
            cb = weewx.wxformulas.cloudbase_Metric(temp_c,
                                                   packet_d['outHumidity'],
                                                   self.altitude_m)
            cb_vt = ValueTuple(cb, 'meter', self.p_alt_group)
        cloudbase = convert(cb_vt, self.alt_group).value
        cloudbase = cloudbase if cloudbase is not None else 0.0
        data['cloudbasevalue'] = self.alt_format % cloudbase
        # forecast - forecast text
        _text = self.scroller_text if self.scroller_text is not None else ''
        data['forecast'] = time.strftime(_text, time.localtime(ts))
        # version - weather software version
        data['version'] = '%s' % weewx.__version__
        # build -
        data['build'] = ''
        # ver - gauge-data.txt version number
        data['ver'] = self.version
        # month to date rain, only calculate if we have been asked
        if self.mtd_rain:
            if self.month_rain is not None:
                rain_m = convert(self.month_rain, self.rain_group).value
                rain_b_vt = ValueTuple(self.buffer.rainsum, self.p_rain_type, self.p_rain_group)
                rain_b = convert(rain_b_vt, self.rain_group).value
                if rain_m is not None and rain_b is not None:
                    rain_m = rain_m + rain_b
                else:
                    rain_m = 0.0
            else:
                rain_m = 0.0
            data['mrfall'] = self.rain_format % rain_m
        # year to date rain, only calculate if we have been asked
        if self.ytd_rain:
            if self.year_rain is not None:
                rain_y = convert(self.year_rain, self.rain_group).value
                rain_b_vt = ValueTuple(self.buffer.rainsum, self.p_rain_type, self.p_rain_group)
                rain_b = convert(rain_b_vt, self.rain_group).value
                if rain_y is not None and rain_b is not None:
                    rain_y = rain_y + rain_b
                else:
                    rain_y = 0.0
            else:
                rain_y = 0.0
            data['yrfall'] = self.rain_format % rain_y
        return data

    def new_archive_record(self, record):
        """Control processing when new a archive record is presented."""

        # set our lost contact flag if applicable
        self.lost_contact_flag = self.get_lost_contact(record, 'archive')
        # save the windSpeed value to use as our archive period average
        if 'windSpeed' in record:
            self.windSpeedAvg_vt = weewx.units.as_value_tuple(record, 'windSpeed')
        else:
            self.windSpeedAvg_vt = ValueTuple(None, 'km_per_hour', 'group_speed')
        # save the windDir value to use as our archive period average
        if 'windDir' in record:
            self.windDirAvg = record['windDir']
        else:
            self.windDirAvg = None
        # refresh our day (archive record based) stats to date in case we have
        # jumped to the next day
        self.day_stats = self.db_manager._get_day_summary(record['dateTime'])
        self.apptemp_day_stats = self.apptemp_manager._get_day_summary(record['dateTime'])

    def end_archive_period(self):
        """Control processing at the end of each archive period."""

        # Reset our loop stats.
        self.buffer.reset_loop_stats()

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
                    logdbg("rtgd",
                           "KeyError: Could not determine sensor contact state")
                    result = True
        return result


# ============================================================================
#                             class RtgdBuffer
# ============================================================================


class RtgdBuffer(object):
    """Class to buffer various loop packet obs.

    If archive based stats are an efficient means of getting stats for today.
    However, their use would mean that any daily stat (eg today's max outTemp)
    that 'occurs' after the most recent archive record but before the next
    archive record is written to archive will not be captured. For this reason
    selected loop data is buffered to ensure that such stats are correctly
    reflected.
    """

    def __init__(self):
        """Initialise an instance of our class."""

        # Initialise min/max for loop data received since last archive record
        # and sum/counter for windrun calculator
        # initialise sum/counter for windrun calculator and sum for rain
        self.windsum = 0
        self.windcount = 0
        self.rainsum = 0

        # initialise loop period low/high/max stats
        self.tempL_loop = [None, None]
        self.tempH_loop = [None, None]
        self.intempL_loop = [None, None]
        self.intempH_loop = [None, None]
        self.dewpointL_loop = [None, None]
        self.dewpointH_loop = [None, None]
        self.apptempL_loop = [None, None]
        self.apptempH_loop = [None, None]
        self.wchillL_loop = [None, None]
        self.heatindexH_loop = [None, None]
        self.wgustM_loop = [None, None, None]
        self.pressL_loop = [None, None]
        self.pressH_loop = [None, None]
        self.rrateH_loop = [None, None]
        self.humL_loop = [None, None]
        self.humH_loop = [None, None]
        self.windM_loop = [None, None]
        self.UVH_loop = [None, None]
        self.SolarH_loop = [None, None]

        # Setup lists/flags for 5 and 10 minute wind stats
        self.wind_list = []
        self.wind_dir_list = []

        # set length of time to retain wind obs
        self.wind_period = 600

    def reset_loop_stats(self):
        """Reset loop windrun sum/count and loop low/high/max stats.

        Normally performed when the class is initialised and at the end of each
        archive period.
        """

        # reset sum/counter for windrun calculator and sum for rain
        self.windsum = 0
        self.windcount = 0
        self.rainsum = 0

        # reset loop period low/high/max stats
        self.tempL_loop = [None, None]
        self.tempH_loop = [None, None]
        self.intempL_loop = [None, None]
        self.intempH_loop = [None, None]
        self.dewpointL_loop = [None, None]
        self.dewpointH_loop = [None, None]
        self.apptempL_loop = [None, None]
        self.apptempH_loop = [None, None]
        self.wchillL_loop = [None, None]
        self.heatindexH_loop = [None, None]
        self.wgustM_loop = [None, None, None]
        self.pressL_loop = [None, None]
        self.pressH_loop = [None, None]
        self.rrateH_loop = [None, None]
        self.humL_loop = [None, None]
        self.humH_loop = [None, None]
        self.windM_loop = [None, None]
        self.UVH_loop = [None, None]
        self.SolarH_loop = [None, None]

    def average_wind(self):
        """ Calculate average wind speed over an archive interval period.

        Archive stats are defined on fixed 'archive interval' boundaries.
        gauge-data.txt requires the average wind speed over the last
        'archive interval' seconds. This means calculating over the last
        'archive interval' seconds ending on the current loop period. This is
        achieved by keeping a list of last 'archive interval' of loop wind
        speed data and calculating a simple average.
        Units used are loop data units so unit conversion of the result may be
        required.
        Result is only considered valid if a full 'archive interval' of loop
        wind data is held.

        Inputs:
            Nothing

        Returns:
            Average wind speed over the last 'archive interval' seconds
        """

        if len(self.wind_list) > 0:
            average = sum(w for w, _ in self.wind_list)/float(len(self.wind_list))
        else:
            average = 0.0
        return average

    def ten_minute_average_wind_dir(self):
        """ Calculate average wind direction over the last 10 minutes.

        Takes list of last 10 minutes of loop wind speed and direction data and
        calculates a vector average direction.
        Result is only considered valid if a full 10 minutes of loop wind data
        is held.

        Inputs:
            Nothing

        Returns:
            10 minute vector average wind direction
        """

        if len(self.wind_dir_list) > 0:
            avg_dir = 90.0 - math.degrees(math.atan2(sum(y for x, y, s, d, t in self.wind_dir_list),
                                                     sum(x for x, y, s, d, t in self.wind_dir_list)))
            avg_dir = avg_dir if avg_dir > 0 else avg_dir + 360.0
        else:
            avg_dir = None
        return avg_dir

    def ten_minute_wind_gust(self):
        """ Calculate 10 minute wind gust.

        Takes list of last 10 minutes of loop wind speed data and finds the max
        value.  Units used are loop data units so unit conversion of the result
        may be required.
        Result is only considered valid if a full 10 minutes of loop wind data
        is held.

        Inputs:
            Nothing

        Returns:
            10 minute wind gust
        """

        gust = None
        if len(self.wind_list) > 0:
            gust = max(s for s, t in self.wind_list)
        return gust

    def set_lows_and_highs(self, packet):
        """ Update loop highs and lows with new loop data.

        Almost operates as a mini weeWX accumulator but wind data is stored in
        lists to allow samples to be added at one end and old samples dropped
        at the other end.

        -   Look at each loop packet and update lows and highs as required.
        -   Add wind speed/direction data to archive_interval and 10 minute
            lists used for average and 10 minute wind stats

        Inputs:
            packet: loop data packet

        Returns:
            Nothing but updates various low/high stats and 'archive interval'
            and 10 minute wind data lists
        """

        packet_d = dict(packet)
        ts = packet_d['dateTime']

        # process outside temp
        out_temp = packet_d.get('outTemp', None)
        if out_temp is not None:
            self.tempL_loop = [out_temp, ts] if (out_temp < self.tempL_loop[0] or self.tempL_loop[0] is None) else \
                self.tempL_loop
            self.tempH_loop = [out_temp, ts] if out_temp > self.tempH_loop[0] else self.tempH_loop

        # process inside temp
        in_temp = packet_d.get('inTemp', None)
        if in_temp is not None:
            self.intempL_loop = [in_temp, ts] if (in_temp < self.intempL_loop[0] or self.intempL_loop[0] is None) else \
                self.intempL_loop
            self.intempH_loop = [in_temp, ts] if in_temp > self.intempH_loop[0] else self.intempH_loop

        # process dewpoint
        dewpoint = packet_d.get('dewpoint', None)
        if dewpoint is not None:
            self.dewpointL_loop = [dewpoint, ts] if \
                (dewpoint < self.dewpointL_loop[0] or self.dewpointL_loop[0] is None) else \
                self.dewpointL_loop
            self.dewpointH_loop = [dewpoint, ts] if dewpoint > self.dewpointH_loop[0] else self.dewpointH_loop

        # process appTemp
        app_temp = packet_d.get('appTemp', None)
        if app_temp is not None:
            self.apptempL_loop = [app_temp, ts] if \
                (app_temp < self.apptempL_loop[0] or self.apptempL_loop[0] is None) else \
                self.apptempL_loop
            self.apptempH_loop = [app_temp, ts] if app_temp > self.apptempH_loop[0] else self.apptempH_loop

        # process windchill
        windchill = packet_d.get('windchill', None)
        if windchill is not None:
            self.wchillL_loop = [windchill, ts] if \
                (windchill < self.wchillL_loop[0] or self.wchillL_loop[0] is None) else \
                self.wchillL_loop

        # process heatindex
        heatindex = packet_d.get('heatindex', None)
        if heatindex is not None:
            self.heatindexH_loop = [heatindex, ts] if heatindex > self.heatindexH_loop[0] else self.heatindexH_loop

        # process barometer
        barometer = packet_d.get('barometer', None)
        if barometer is not None:
            self.pressL_loop = [barometer, ts] if \
                (barometer < self.pressL_loop[0] or self.pressL_loop[0] is None) else \
                self.pressL_loop
            self.pressH_loop = [barometer, ts] if barometer > self.pressH_loop[0] else self.pressH_loop

        # process rain
        rain = packet_d.get('rain', None)
        self.rainsum += rain if rain is not None else self.rainsum

        # process rainRate
        rain_rate = packet_d.get('rainRate', None)
        if rain_rate is not None:
            self.rrateH_loop = [rain_rate, ts] if rain_rate > self.rrateH_loop[0] else self.rrateH_loop

        # process humidity
        out_humidity = packet_d.get('outHumidity', None)
        if out_humidity is not None:
            self.humL_loop = [out_humidity, ts] if \
                (out_humidity < self.humL_loop[0] or self.humL_loop[0] is None) else \
                self.humL_loop
            self.humH_loop = [out_humidity, ts] if out_humidity > self.humH_loop[0] else self.humH_loop

        # process UV
        uv = packet_d.get('UV', None)
        if uv is not None:
            self.UVH_loop = [uv, ts] if uv > self.UVH_loop[0] else self.UVH_loop

        # process radiation
        radiation = packet_d.get('radiation', None)
        if radiation is not None:
            self.SolarH_loop = [radiation, ts] if radiation > self.SolarH_loop[0] else self.SolarH_loop

        # process windSpeed/windDir
        # if windDir exists then get it, if it does not exist get None
        wind_dir = packet_d.get('windDir', None)
        # if windSpeed exists get it, if it does not exist or is None then
        # get 0.0
        wind_speed = packet_d.get('windSpeed', 0.0)
        wind_speed = 0.0 if wind_speed is None else wind_speed
        self.windsum += wind_speed
        self.windcount += 1
        # Have we seen a new high gust? If so update self.wgustM_loop but only
        # if we have a corresponding wind direction
        if wind_speed > self.wgustM_loop[0] and wind_dir is not None:
            self.wgustM_loop = [wind_speed, wind_dir, ts]
        # average wind speed
        self.wind_list.append([wind_speed, ts])
        # if we have samples in our list then delete any too old
        if len(self.wind_list) > 0:
            # calc ts of oldest sample we want to retain
            old_ts = ts - self.wind_period
            # Remove any samples older than 5 minutes
            self.wind_list = [s for s in self.wind_list if s[1] > old_ts]
        # get our latest (archive_interval) average wind
        wind_m_loop = self.average_wind()
        # have we seen a new high (archive_interval) avg wind? if so update
        # self.windM_loop
        self.windM_loop = [wind_m_loop, ts] if wind_m_loop > self.windM_loop[0] else self.windM_loop
        # Update the 10 minute wind direction list, but only if windDir is not
        # None
        if wind_dir is not None:
            self.wind_dir_list.append([wind_speed * math.cos(math.radians(90.0 - wind_dir)),
                                      wind_speed * math.sin(math.radians(90.0 - wind_dir)),
                                      wind_speed, wind_dir, ts])
        # if we have samples in our list then delete any too old
        if len(self.wind_dir_list) > 0:
            # calc ts of oldest sample we want to retain
            old_ts = ts - self.wind_period
            # Remove any samples older than 10 minutes
            self.wind_dir_list = [s for s in self.wind_dir_list if s[4] > old_ts]


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
           "outTemp", "windchill", "UV"]

    def __init__(self, rec):
        """Initialise our cache object.

        The cache needs to be initialised to include all of the fields required
        by method calculate(). We could initialise all field values to None
        (method calculate() will interpret the None values to be '0' in most
        cases). The result on the gauge display may be misleading. We can get
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


def calc_trend(obs_type, now_vt, group, db_manager, then_ts, grace=0):
    """ Calculate change in an observation over a specified period.

    Inputs:
        obs_type:   database field name of observation concerned
        now_vt:     value of observation now (ie the finishing value)
        group:      group our returned value must be in
        db_manager: manager to be used
        then_ts:    timestamp of start of trend period
        grace:      the largest difference in time when finding the then_ts
                    record that is acceptable

    Returns:
        Change in value over trend period. Can be positive, 0, negative or
        None. Result will be in 'group' units.
    """

    if now_vt.value is None:
        return None
    then_record = db_manager.getRecord(then_ts, grace)
    if then_record is None:
        return None
    else:
        if obs_type not in then_record:
            return None
        else:
            then_vt = weewx.units.as_value_tuple(then_record, obs_type)
            now = convert(now_vt, group).value
            then = convert(then_vt, group).value
            return now - then


def calc_windrose(now, db_manager, period, points):
    """Calculate a SteelSeries Weather Gauges windrose array.

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
        config_dict:         A weeWX config dictionary.

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

        # setup a some thread things
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
                except Queue.Empty:
                    # nothing in the queue so continue
                    pass
                else:
                    # something was in the queue, if it is the shutdown signal
                    # then return otherwise continue
                    if _package is None:
                        # we have a shutdown signal so return to exit
                        return
        except Exception, e:
            # Some unknown exception occurred. This is probably a serious
            # problem. Exit with some notification.
            logcrit("rtgd", "Unexpected exception of type %s" % (type(e), ))
            weeutil.weeutil.log_traceback('rtgd: **** ')
            logcrit("rtgd", "Thread exiting. Reason: %s" % (e, ))
    
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
        entry point so we can be 'started' just like a threading.Thread object.
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
        config_dict:    A weeWX config dictionary.

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
        # multiple rapid API calls and thus breac the API usage conditions.
        self.lockout_period = to_int(wu_config_dict.get('api_lockout_period',
                                                        60))
        # initialise container for timestamp of last WU api call
        self.last_call_ts = None

        # Get our API key from weewx.conf, first look in [RealtimeGaugeData]
        # [[WU]] and if no luck try [Forecast] if it exists. Wrap in a
        # try..except loop to catch exceptions (ie one or both don't exist.
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
            self.locator == 'geocode'
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
        loginf("rtgd",
               "RealTimeGaugeData scroller text will use Weather Underground forecast data")

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
        logdbg2("rtgd",
                "Last Weather Underground API call at %s" % self.last_call_ts)

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
                    logdbg("rtgd",
                           "Downloaded updated Weather Underground forecast information")
                except Exception, e:
                    # Some unknown exception occurred. Set _response to None,
                    # log it and continue.
                    _response = None
                    loginf("rtgd",
                           "Unexpected exception of type %s" % (type(e), ))
                    weeutil.weeutil.log_traceback('WUThread: **** ')
                    loginf("rtgd",
                           "Unexpected exception of type %s" % (type(e), ))
                    loginf("rtgd",
                           "Weather Underground API forecast query failed")
                # if we got something back then reset our last call timestamp
                if _response is not None:
                    self.last_call_ts = now
                return _response
        else:
            # API call limiter kicked in so say so
            loginf("rtgd",
                   "Tried to make a WU API call within %d sec of the previous call." % (self.lockout_period, ))
            loginf("        ",
                   "WU API call limit reached. API call skipped.")
        return None

    def parse_response(self, response):
        """ Parse a WU API forecast response and return the forecast text.

        The WU API forecast response contains a number of forecast texts, the
        three main ones are:

        - the full day narrative
        - the day time narrative, and
        - the night time narrative.

        WU claims that night time is for 7pm to 7am and day time is for 7am to
        7pm. We will vary that slightly and use daytime for all times up until
        7pm and thence night time - expect the night time forecast applies to
        the end of the day not the start of the day (ie after 7pm and up until
        7am the next day so it does not cover say 1am today - that is in
        yesterday's forecast which is no longer available).

        Input:
            response: A WU API response in JSON format.

        Returns:
            The selected forecast text if it exists otherwise None.
        """

        # deserialize the response but be prepared to catch an exception if the
        # response can't be parsed
        try:
            _response_json = json.loads(response)
        except ValueError:
            # can't deserialize the response so log it and return None
            loginf("rtgd",
                   "Unable to deserialise Weather Underground forecast response")
            return None

        # We have deserialized forecast data so return the data we want. Wrap
        # in a try..except so we can catch any errors if the data is malformed.
        try:
            # Check which forecast narrative we are after and locate the
            # appropriate field.
            if self.forecast_text == 'day':
                # we want the full day narrative
                return _response_json['narrative'][0]
            else:
                # we want the day time or night time narrative, but which, use
                # day time for 7am to 7pm otherwise use night time
                _hour = datetime.datetime.now().hour
                if _hour < 19:
                    # it's before 7pm so use day time
                    _index = _response_json['daypart'][0]['daypartName'].index('Today')
                else:
                    # otherwise night time
                    _index = _response_json['daypart'][0]['daypartName'].index('Tonight')
                return _response_json['daypart'][0]['narrative'][_index]
        except KeyError:
            # if we can'f find a field log the error and return None
            loginf("rtgd",
                   "Unable to locate field for '%s' forecast narrative" % self.forecast_text)
            return None
        except ValueError:
            # if we can'f find an index log the error and return None
            loginf("rtgd",
                   "Unable to locate index '%d' for '%s' forecast narrative" % (_index, self.forecast_text))
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
                       of 'e', 'm', 's' or'h'.
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
            logdbg("rtgd",
                   "Submitting Weather Underground API call using URL: %s" % (_obf_url, ))
        # we will attempt the call max_tries times
        for count in range(max_tries):
            # attempt the call
            try:
                w = urllib2.urlopen(url)
                _response = w.read()
                w.close()
                return _response
            except (urllib2.URLError, socket.timeout), e:
                logerr("rtgd",
                       "Failed to get Weather Underground forecast on attempt %d" % (count+1, ))
                logerr("weatherundergroundapiforecast", "   **** %s" % e)
        else:
            logerr("rtgd", "Failed to get Weather Underground forecast")
        return None


# ============================================================================
#                           class ZambrettiSource
# ============================================================================


class ZambrettiSource(ThreadedSource):
    """Thread that obtains Zambretti forecast text and places it in a queue.

    Requires the weeWX forecast extension to be installed and configured to
    provide the Zambretti forecast.

    ZambrettiSource constructor parameters:

        control_queue:  A Queue object used by our parent to control (shutdown)
                        this thread.
        result_queue:   A Queue object used to pass forecast data to the
                        destination
        engine:         An instance of class weewx.weewx.Engine
        config_dict:    A weeWX config dictionary.

    ZambrettiSource methods:

        run.               Control fetching the forecast and monitor the control
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
        loginf("rtgd",
               "RealTimeGaugeData scroller text will use Zambretti forecast data")
    
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

    Requires the weeWX forecast extension to be installed and configured to
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
        
        # flag as to whether the weeWX forecasting extension is installed
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
        except Exception, e:
            # Something went wrong so log the error. Our forecasting_installed 
            # flag will not have been set so it is safe to continue but there 
            # will be no Zambretti text
            logdbg('rtgd',
                   'Error initialising Zambretti forecast, is the forecast extension installed.')
            logdbg('rtgd',
                   'Unexpected exception of type %s' % (type(e), ))
            weeutil.weeutil.log_traceback('rtgd: **** ',
                                          loglevel=syslog.LOG_DEBUG)

    def get_data(self):
        """Get scroller user specified scroller text string.

        If Zambretti is not installed or nothing is found then a short 
        informative string is returned.
        """

        # get the current time
        now = time.time()
        logdbg2("rtgd",
                "Last Zambretti forecast obtained at %s" % self.last_query_ts)
        # If we haven't made a db query previously or if its been too long 
        # since the last query then make the query
        if (self.last_query_ts is None) or ((now + 1 - self.interval) >= self.last_query_ts):
            # if the forecast extension is not installed then return an 
            # appropriate message
            if not self.is_installed:
                return self.UNAVAILABLE_MESSAGE
            # make the query
            # SQL query to get the latest Zambretti forecast code
            sql = "SELECT dateTime,zcode FROM %s WHERE method = 'Zambretti' ORDER BY dateTime DESC LIMIT 1" % self.dbm.table_name
            # execute the query, wrap in try..except just in case
            for count in range(self.max_tries):
                try:
                    record = self.dbm.getSql(sql)
                    if record is not None:
                        # we have a non-None response so save the time of the 
                        # query and return the decoded forecast text
                        self.last_query_ts = now
                        return self.zambretti_label_dict[record[1]]
                except Exception, e:
                    logerr('rtgd', 'get zambretti failed (attempt %d of %d): %s' %
                           ((count + 1), self.max_tries, e))
                    logdbg('rtgd', 'waiting %d seconds before retry' %
                           self.retry_wait)
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
        conf_dict:           A weeWX config dictionary.

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
        # multiple rapid API calls and thus breac the API usage conditions.
        self.lockout_period = to_int(darksky_config_dict.get('api_lockout_period',
                                                             60))
        # initialise container for timestamp of last API call
        self.last_call_ts = None
        # Get our API key from weewx.conf, first look in [RealtimeGaugeData]
        # [[WU]] and if no luck try [Forecast] if it exists. Wrap in a
        # try..except loop to catch exceptions (ie one or both don't exist.
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
        loginf("rtgd",
               "RealTimeGaugeData scroller text will use Darksky forecast data")

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
        logdbg2("rtgd",
                "Last Darksky API call at %s" % self.last_call_ts)
        # has the lockout period passed since the last call
        if self.last_call_ts is None or ((now + 1 - self.lockout_period) >= self.last_call_ts):
            # If we haven't made an API call previously or if its been too long
            # since the last call then make the call
            if (self.last_call_ts is None) or ((now + 1 - self.interval) >= self.last_call_ts):
                # Make the call, wrap in a try..except just in case
                try:
                    _response = self.api.get_data(block=self.block,
                                                  language=self.language,
                                                  units=self.units,
                                                  max_tries=self.max_tries)
                    logdbg("rtgd",
                           "Downloaded updated Darksky forecast")
                except Exception, e:
                    # Some unknown exception occurred. Set _response to None,
                    # log it and continue.
                    _response = None
                    loginf("rtgd",
                           "Unexpected exception of type %s" % (type(e), ))
                    weeutil.weeutil.log_traceback('rtgd: **** ')
                    loginf("rtgd",
                           "Unexpected exception of type %s" % (type(e), ))
                    loginf("rtgd", "Darksky forecast API query failed")
                # if we got something back then reset our last call timestamp
                if _response is not None:
                    self.last_call_ts = now
                return _response
        else:
            # API call limiter kicked in so say so
            loginf("rtgd",
                   "Tried to make an Darksky API call within %d sec of the previous call." % (self.lockout_period, ))
            loginf("        ",
                   "Darksky API call limit reached. API call skipped.")
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
                loginf("rtgd",
                       "Darksky data for this location temporarily unavailable")
                return None
        else:
            logdbg("rtgd", "No flag object in Darksky API response.")

        # get the summary data to be used
        # is our block available, can't assume it is
        if self.block in response:
            # we have our block, but is the summary there
            if 'summary' in response[self.block]:
                # we have a summary field
                summary = response[self.block]['summary'].encode('ascii', 'ignore')
                return summary
            else:
                # we have no summary field, so log it and return None
                logdbg("rtgd",
                       "Summary data not available for '%s' forecast" % (self.block,))
                return None
        else:
            logdbg("rtgd", 'Dark Sky %s block not available' % self.block)
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
            logdbg("darkskyapi",
                   "Submitting API call using URL: %s" % (_obfuscated_url, ))
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
                w = urllib2.urlopen(url)
                response = w.read()
                w.close()
                return response
            except (urllib2.URLError, socket.timeout), e:
                logerr("darkskyapi",
                       "Failed to get API response on attempt %d" % (count+1, ))
                logerr("darkskyapi", "   **** %s" % e)
        else:
            logerr("darkskyapi", "Failed to get API response")
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
        config_dict:    A weeWX config dictionary.

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
            logdbg("rtgd", "File block not specified or not a valid path/file")
            self.scroller_file = None

        # initialise the time of last file read
        self.last_read_ts = None
        
        # log what we will do
        if self.scroller_file is not None:
            loginf("rtgd",
                   "RealTimeGaugeData scroller text will use text from file '%s'" % self.scroller_file)
    
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
        logdbg2("rtgd", "Last File read at %s" % self.last_read_ts)
        if (self.last_read_ts is None) or ((now + 1 - self.interval) >= self.last_read_ts):
            # read the file, wrap in a try..except just in case
            _data = None
            try:
                if self.scroller_file is not None:
                    with open(self.scroller_file, 'r') as f:
                        _data = f.readline().strip()
                logdbg("rtgd", "File read")
            except Exception, e:
                # Some unknown exception occurred. Set _data to None,
                # log it and continue.
                _data = None
                loginf("rtgd",
                       "Unexpected exception of type %s" % (type(e), ))
                weeutil.weeutil.log_traceback('rtgd: **** ')
                loginf("rtgd",
                       "Unexpected exception of type %s" % (type(e), ))
                loginf("rtgd", "File read failed")
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
        loginf("rtgd",
               "RealTimeGaugeData scroller text will use a fixed string")

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

