# rtgd.py
#
# A weeWX service to generate a loop based gauge-data.txt.
#
# Copyright (C) 2017 Gary Roderick                  gjroderick<at>gmail.com
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option) any
# later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program.  If not, see http://www.gnu.org/licenses/.
#
# Version: 0.2.7                                      Date: 23 February 2017
#
# Revision History
#  23 February 2017     v0.2.7  - loop packets are now cached to support
#                                 stations that emit partial packets
#                               - average wind speed and
#  22 February 2017     v0.2.6  - updated docstring config options to reflect
#                                 current library of available options
#                               - 'latest' and 'avgbearing' wind directions now
#                                 return the last non-None wind direction
#                                 respectively when their feeder direction is
#                                 None
#                               - implemented optional scroller_text config
#                                 option allowing fixed scroller text to be
#                                 specified in lieu of Zambretti forecast text
#                               - renamed rtgd thread and queue variables
#                               - no longer reads unit group config options
#                                 that have only one possible unit
#                               - use of mmHg, knot or cm units reverts to hPa,
#                                 mile_per_hour and mm respectively due to
#                                 weeWX or SteelSeries Gauges not understanding
#                                 the unit (or derived unit)
#                               - made gauge-data.txt unit code determination
#                                 more robust
#                               - reworked code that formats gauge-data.txt
#                                 field data to better handle None values
#  21 February 2017     v0.2.5  - fixed error where altitude units could not be
#                                 changed from meter
#                               - rainrate and windrun unit groups are now
#                                 derived from rain and speed units groups
#                                 respectively
#                               - solar calc config options no longer searched
#                                 for in [StdWXCalculate]
#  20 February 2017     v0.2.4  - fixed error where rain units could not be
#                                 changed from mm
#                               - pressures now formats to correct number of
#                                 decimal places
#                               - reworked temp and pressure trend formatting
#  20 February 2017     v0.2.3  - Fixed logic error in windrose calculations.
#                                 Minor tweaking of windrose processing.
#  19 February 2017     v0.2.2  - Added config option apptemp_binding
#                                 specifying a binding containing appTemp data.
#                                 apptempTL and apptempTH default to apptemp if
#                                 binding not specified or it does not contain
#                                 appTemp data.
#  15 February 2017     v0.2.1  - fixed error that resulted in incorrect pressL
#                                 and pressH values
#  24 January 2017      v0.2.0  - now runs in a thread to eliminate blocking
#                                 impact on weeWX
#                               - now calculates WindRoseData
#                               - now calculates pressL and pressH
#                               - frequency of generation is now specified by
#                                 a single config option min_interval
#                               - gauge-data.txt output path is now specified
#                                 by rtgd_path config option
#                               - added config options for windrose period and
#                                 number of compass points to be generated
#  19 January 2017      v0.1.2  - fix error that occurred when stations do not
#                                 emit radiation
#  18 January 2017      v0.1.1  - better handles loop observations that are None
#  3 January 2017       v0.1.0  - initial release
#
"""A weeWX service to generate a loop based gauge-data.txt.

Used to update the SteelSeries Weather Gauges in near real time.

Inspired by crt.py v0.5 by Matthew Wall, a weeWX service to emit loop data to
file in Cumulus realtime format. Refer http://wiki.sandaysoft.com/a/Realtime.txt

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
    # gauge-data.txt
    rtgd_file_name = gauge-data.txt

    # Minimum interval (seconds) between file generation. Ideally
    # gauge-data.txt would be generated on receipt of every loop packet (there
    # is no point in generating more frequently than this); however, in some
    # cases the user may wish to generate gauge-data.txt less frequently. The
    # min_interval option sets the minimum time between successive
    # gauge-data.txt generations. Generation will be skipped on arrival of a
    # loop packet if min_interval seconds have NOT elapsed since the last
    # generation. If min_interval is 0 or omitted generation will occur on
    # every loop packet (as will be the case if min_interval < station loop
    period). Optional, default is 0.
    min_interval =

    # Number of compass points to include in WindRoseData, normally
    # 8 or 16. Optional, default 16.
    windrose_points = 16

    # Period over which to calculate WindRoseData in seconds. Optional, default
    # is 86400 (24 hours).
    windrose_period = 86400

    # Binding to use for appTemp data. Optional, default 'wx_binding'.
    apptemp_binding = wx_binding

    # Text to display on the scroller. Optional, if omitted then forecast text
    # is displayed if available.
    scroller_text = 'some text'

    # Update windrun value each loop period or just on each archive period.
    # Optional, default is False.
    windrun_loop = false

    # Stations that provide partial packets are supported through a cache that
    # caches packet data. max_cache_age is the maximum age  in seconds for
    # which cached data is retained. Optional, default is 600 seconds.
    max_cache_age = 600

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
        inHg = %.3f
        inch = %.2f
        inch_per_hour = %.2f
        km_per_hour = %.0f
        km = %.1f
        mbar = %.1f
        meter = %.0f
        meter_per_second = %.1f
        mile_per_hour = %.0f
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

4.  Add the RealtimeGaugeData service to the list of report services under
[Engines] [[WxEngine]] in weewx.conf:

[Engines]
    [[WxEngine]]
        report_services = ..., user.rtgd.RealtimeGaugeData

5.  If you intend to save the realtime generated gauge-data.txt in the same
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

6.  Edit $SKIN_ROOT/ss/scripts/gauges.js and change the realTimeURL_weewx
setting (circa line 68) to refer to the location of the realtime generated
gauge-data.txt. Change the realtimeInterval setting (circa line 37) to reflect
the update period of the realtime gauge-data.txt in seconds. This setting
controls the count down timer and update frequency of the SteelSeries Weather
Gauges.

7.  Delete the file $HTML_ROOT/ss/scripts/gauges.js.

8.  Stop/start weeWX

9.  Confirm that gauge-data.txt is being generated regularly as per the period
and nth_loop settings under [RealtimeGaugeData] in weewx.conf.

10.  Confirm the SteelSeries Weather Gauges are being updated each time
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
import json
import math
import os.path
import syslog
import threading
import time

# weeWX imports
import weedb
import weewx
import weeutil.weeutil
import weewx.units
import weewx.wxformulas
from weewx.engine import StdService
from weewx.units import ValueTuple, convert, getStandardUnitType
from weeutil.weeutil import to_bool

# version number of this script
RTGD_VERSION = '0.2.7'
# version number (format) of the generated gauge-data.txt
GAUGE_DATA_VERSION = '13'

# ordinal compass points supported
COMPASS_POINTS = ['N','NNE','NE','ENE','E','ESE','SE','SSE',
                  'S','SSW','SW','WSW','W','WNW','NW','NNW','N']

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
STATION_LOST_CONTACT = {'Vantage' : {'field':'rxCheckPercent', 'value': 0},
                        'FineOffsetUSB' : {'field':'status', 'value': 0x40},
                        'Ultimeter' : {'field':'rxCheckPercent', 'value': 0},
                        'WMR100': {'field':'rxCheckPercent', 'value': 0},
                        'WMR200': {'field':'rxCheckPercent', 'value': 0},
                        'WMR9x8': {'field':'rxCheckPercent', 'value': 0},
                        'WS23xx': {'field':'rxCheckPercent', 'value': 0},
                        'WS28xx': {'field':'rxCheckPercent', 'value': 0},
                        'TE923': {'field':'rxCheckPercent', 'value': 0},
                        'WS1': {'field':'rxCheckPercent', 'value': 0},
                        'CC3000': {'field':'rxCheckPercent', 'value': 0}}
# stations supporting lost contact reporting through their archive record
ARCHIVE_STATIONS = ['Vantage']
# stations supporting lost contact reporting through their loop packet
LOOP_STATIONS = ['FineOffsetUSB']


def logmsg(level, msg):
    syslog.syslog(level, msg)


def logcrit(id, msg):
    logmsg(syslog.LOG_CRIT, '%s: %s' % (id, msg))


def logdbg(id, msg):
    logmsg(syslog.LOG_DEBUG, '%s: %s' % (id, msg))


def logdbg2(id, msg):
    if weewx.debug >= 2:
        logmsg(syslog.LOG_DEBUG, '%s: %s' % (id, msg))


def loginf(id, msg):
    logmsg(syslog.LOG_INFO, '%s: %s' % (id, msg))


def logerr(id, msg):
    logmsg(syslog.LOG_ERR, '%s: %s' % (id, msg))


# ============================================================================
#                          class ZambrettiForecast
# ============================================================================


class ZambrettiForecast(object):
    """Class to extract Zambretti forecast text.

    Requires the weeWX forecast extension to be installed and configured to
    provide the Zambretti forecast otherwise 'Forecast not available' will be
    returned."""

    DEFAULT_FORECAST_BINDING = 'forecast_binding'
    DEFAULT_BINDING_DICT = {'database': 'forecast_sqlite',
                            'manager': 'weewx.manager.Manager',
                            'table_name': 'archive',
                            'schema': 'user.forecast.schema'}

    def __init__(self, config_dict):
        """Initialise the ZambrettiForecast object."""

        # flag as to whether the weeWX forecasting extension is installed
        self.forecasting_installed = False
        # set some forecast db access parameters
        self.db_max_tries = 3
        self.db_retry_wait = 3
        # Get a db manager for the forecast database and import the Zambretti
        # label lookup dict. If an exception is raised then we can assume the
        # forecast extension is not installed.
        try:
            # create a db manager config dict
            dbm_dict = weewx.manager.get_manager_dict(config_dict['DataBindings'],
                                                      config_dict['Databases'],
                                                      ZambrettiForecast.DEFAULT_FORECAST_BINDING,
                                                      default_binding_dict=ZambrettiForecast.DEFAULT_BINDING_DICT)
            # get a db manager for the forecast database
            self.dbm = weewx.manager.open_manager(dbm_dict)
            # import the Zambretti forecast text
            from user.forecast import zambretti_label_dict
            self.zambretti_label_dict = zambretti_label_dict
            # if we made it this far the forecast extension is installed and we
            # can do business
            self.forecasting_installed = True
        except (weewx.UnknownBinding, weedb.DatabaseError,
                weewx.UnsupportedFeature, KeyError, ImportError):
            # something went wrong, our forecasting_installed flag will not
            # have been set so we can just continue on
            pass

    def is_installed(self):
        """Is the forecasting extension installed."""

        return self.forecasting_installed

    def get_zambretti_text(self):
        """Return the current Zambretti forecast text."""

        # if the forecast extension is not installed then return an appropriate
        # message
        if not self.forecasting_installed:
            return 'Forecast not available'

        # SQL query to get the latest Zambretti forecast code
        sql = "SELECT dateTime,zcode FROM %s WHERE method = 'Zambretti' ORDER BY dateTime DESC LIMIT 1" % self.dbm.table_name
        # try to execute the query
        for count in range(self.db_max_tries):
            try:
                record = self.dbm.getSql(sql)
                # if we get a non-None response then return the decoded
                # forecast text
                if record is not None:
                    return self.zambretti_label_dict[record[1]]
            except Exception, e:
                logerr('rtgdthread: zambretti:', 'get zambretti failed (attempt %d of %d): %s' %
                       ((count + 1), self.db_max_tries, e))
                logdbg('rtgdthread: zambretti', 'waiting %d seconds before retry' %
                       self.db_retry_wait)
                time.sleep(self.db_retry_wait)
        # if we made it here we have been unable to get a response from the
        # forecast db so return a suitable message
        return 'Forecast not available'


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

        self.rtgd_queue = Queue.Queue()
        manager_dict = weewx.manager.get_manager_dict_from_config(config_dict,
                                                                  'wx_binding')
        self.db_manager = weewx.manager.open_manager(manager_dict)
        # get an instance of class RealtimeGaugeDataThread and start the
        # thread running
        self.rtgd_thread = RealtimeGaugeDataThread(self.rtgd_queue,
                                                   config_dict,
                                                   manager_dict,
                                                   latitude=engine.stn_info.latitude_f,
                                                   longitude=engine.stn_info.longitude_f,
                                                   altitude=convert(engine.stn_info.altitude_vt, 'meter').value)
        self.rtgd_thread.start()
        # bind ourself to the relevant weeWX events
        self.bind(weewx.NEW_LOOP_PACKET, self.new_loop_packet)
        self.bind(weewx.NEW_ARCHIVE_RECORD, self.new_archive_record)
        self.bind(weewx.END_ARCHIVE_PERIOD, self.end_archive_period)

    def new_loop_packet(self, event):
        """Puts new loop packets in the rtgd queue."""

        # package the loop packet in a dict since this is not the only data
        # we send via the queue
        _package = {'type': 'loop',
                    'payload': event.packet}
        self.rtgd_queue.put(_package)
        logdbg2("rtgd", "queued loop packet: %s" %  _package['payload'])

    def new_archive_record(self, event):
        """Puts archive records in the rtgd queue."""

        # package the archive record in a dict since this is not the only data
        # we send via the queue
        _package = {'type': 'archive',
                    'payload': event.record}
        self.rtgd_queue.put(_package)
        logdbg2("rtgd", "queued archive record: %s" %  _package['payload'])
        # get alltime min max baro and put in the queue
        # get the min and max values (incl usUnits)
        _minmax_baro = self.get_minmax_obs('barometer')
        # if we have some data then package it in a dict since this is not the
        # only data we send via the queue
        if _minmax_baro:
            _package = {'type': 'stats',
                        'payload': _minmax_baro}
            self.rtgd_queue.put(_package)
            logdbg2("rtgd", "queued min/max barometer values: %s" %  _package['payload'])

    def end_archive_period(self, event):
        """Puts END_ARCHIVE_PERIOD event in the rtgd queue."""

        # package the event in a dict since this is not the only data we send
        # via the queue
        _package = {'type': 'event',
                    'payload': weewx.END_ARCHIVE_PERIOD}
        self.rtgd_queue.put(_package)
        logdbg2("rtgd", "queued weewx.END_ARCHIVE_PERIOD event")

    def shutDown(self):
        """Shut down any threads."""

        if hasattr(self, 'rtgd_queue') and hasattr(self, 'rtgd_thread'):
            if self.rtgd_queue and self.rtgd_thread.isAlive():
                # Put a None in the rtgd_queue to signal the thread to shutdown
                self.rtgd_queue.put(None)
                # Wait up to 20 seconds for the thread to exit:
                self.rtgd_thread.join(20.0)
                if self.rtgd_thread.isAlive():
                    logerr("rtgd", "Unable to shut down %s thread" % self.rtgd_thread.name)
                else:
                    logdbg("rtgd", "Shut down %s thread." % self.rtgd_thread.name)

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


# ============================================================================
#                       class RealtimeGaugeDataThread
# ============================================================================


class RealtimeGaugeDataThread(threading.Thread):
    """Thread that generates gauge-data.txt in near realtime."""

    def __init__(self, queue, config_dict, manager_dict,
                 latitude, longitude, altitude):
        # Initialize my superclass:
        threading.Thread.__init__(self)

        self.setDaemon(True)
        self.rtgd_queue = queue
        self.config_dict = config_dict
        self.manager_dict = manager_dict

        # get our RealtimeGaugeData config dictionary
        rtgd_config_dict = config_dict.get('RealtimeGaugeData', {})

        # setup every nth record or every n seconds file generation
        self.min_interval = rtgd_config_dict.get('min_interval', None)
        self.last_write = 0 # ts (actual) of last generation

        # get our file paths and names
        _path = rtgd_config_dict.get('rtgd_path', '/var/tmp')
        _html_root = os.path.join(config_dict['WEEWX_ROOT'],
                                  config_dict['StdReport'].get('HTML_ROOT', ''))

        rtgd_path = os.path.join(_html_root, _path)
        self.rtgd_path_file = os.path.join(rtgd_path,
                                           rtgd_config_dict.get('rtgd_file_name',
                                                                'gauge-data.txt'))

        # get scroller text if there is any
        self.scroller_text = rtgd_config_dict.get('scroller_text', None)

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
        self.rainrate_group = ''.join([self.rain_group,'_per_hour'])
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
        # get a CachedPacket object as our loop packet cache
        self.packet_cache = CachedPacket()

        # initialise last wind directions for use when respective direction is
        # None. We need latest and average
        self.last_latest_dir = 0
        self.last_average_dir = 0

        # Are we updating windrun using archive data only or archive and loop
        # data?
        self.windrun_loop = to_bool(rtgd_config_dict.get('windrun_loop',
                                                         'False'))

        # weeWX does not normally archive appTemp so day stats are not usually
        # available; however, if the user does have appTemp in a database then
        # if we have a binding we can use it. Check if an appTemp binding was
        # specified, if so use it, otherwise default to 'wx_binding'. We will
        # check for data existence before using it.
        self.apptemp_binding = rtgd_config_dict.get('apptemp_binding',
                                                    'wx_binding')

        # create a RtgdBuffer object to hold our loop 'stats'
        self.buffer = RtgdBuffer(config_dict)

        # Set our lost contact flag. Assume we start off with contact
        self.lost_contact_flag = False

        # initialise some properties used to hold archive period wind data
        self.windSpeedAvg = None
        self.windDirAvg = None
        self.min_barometer = None
        self.max_barometer = None

        # get some station info
        self.latitude = latitude
        self.longitude = longitude
        self.altitude_m = altitude
        self.station_type = config_dict['Station']['station_type']

        # gauge-data.txt version
        self.version = str(GAUGE_DATA_VERSION)

        if self.min_interval is None:
            _msg = "RealTimeGaugeData will generate gauge-data.txt. "\
                       "min_interval is None"
        elif self.min_interval == 1:
            _msg = "RealTimeGaugeData will generate gauge-data.txt. "\
                       "min_interval is 1 second"
        else:
            _msg = "RealTimeGaugeData will generate gauge-data.txt. min_interval is %s seconds" % self.min_interval
        loginf("engine", _msg)


    def run(self):
        """Collect packets from the rtgd queue and manage their processing.

        Now that we are in a thread get a manager for our db so we can
        initialise our forecast and day stats. Once this is done we wait for
        something in the rtgd queue.
        """

        # get a db manager
        self.db_manager = weewx.manager.open_manager(self.manager_dict)
        # get a db manager for appTemp
        self.apptemp_manager = weewx.manager.open_manager_with_config(self.config_dict,
                                                                      self.apptemp_binding)
        # get a Zambretti forecast objects
        self.forecast = ZambrettiForecast(self.config_dict)
        logdbg("rtgdthread", "Zambretti is installed: %s" % self.forecast.is_installed())
        # initialise our day stats
        self.day_stats = self.db_manager._get_day_summary(time.time())
        # initialise our day stats from our appTemp source
        self.apptemp_day_stats = self.apptemp_manager._get_day_summary(time.time())
        # get a windrose to start with since it is only on receipt of an
        # archive record
        logdbg2("rtgdthread", "calculating windrose data ...")
        self.rose = calc_windrose(int(time.time()),
                                  self.db_manager,
                                  self.wr_period,
                                  self.wr_points)
        logdbg2("rtgdthread", "windrose data calculated")

        # prime our loop cache and set some starting wind values
        _ts = self.db_manager.lastGoodStamp()
        if _ts is not None:
            _rec = self.db_manager.getRecord(_ts)
            # We could leave our cache primed with None values or, if there is
            # at least one record in the archive, we could prime the cache from
            # the latest archive record. This gets us in the ball park.
            self.packet_cache.prime(_rec, _rec['dateTime'])
        else:
            _rec = {}
        # save the windSpeed value to use as our archive period average
        if 'windSpeed' in _rec:
            self.windSpeedAvg = _rec['windSpeed']
        else:
            self.windSpeedAvg = None
        # save the windDir value to use as our archive period average
        if 'windDir' in _rec:
            self.windDirAvg = _rec['windDir']
        else:
            self.windDirAvg = None

        # now run a continuous loop, waiting for records to appear in the rtgd
        # queue then processing them.
        while True:
            while True:
                _package = self.rtgd_queue.get()
                # a None record is our signal to exit
                if _package is None:
                    return
                elif _package['type'] == 'archive':
                    self.new_archive_record(_package['payload'])
                    logdbg2("rtgdthread", "received archive record")
                    logdbg2("rtgdthread", "calculating windrose data ...")
                    self.rose = calc_windrose(_package['payload']['dateTime'],
                                              self.db_manager,
                                              self.wr_period,
                                              self.wr_points)
                    logdbg2("rtgdthread", "windrose data calculated")
                    continue
                elif _package['type'] == 'event':
                    if _package['payload'] == weewx.END_ARCHIVE_PERIOD:
                        logdbg2("rtgdthread",
                                "received event - END_ARCHIVE_PERIOD")
                        self.end_archive_period()
                    continue
                elif _package['type'] == 'stats':
                    logdbg2("rtgdthread",
                            "received stats package payload=%s" % (_package['payload'], ))
                    self.process_stats(_package['payload'])
                    logdbg2("rtgdthread", "processed stats package")
                    continue
                # if packets have backed up in the rtgd queue, trim it until
                # it's no bigger than the max allowed backlog
                if self.rtgd_queue.qsize() <= 5:
                    break

            # we now have a packet to process, wrap in a try..except so we can
            # catch any errors
            try:
                logdbg2("rtgdthread",
                        "received packet: %s" % _package['payload'])
                self.process_packet(_package['payload'])
            except Exception, e:
                # Some unknown exception occurred. This is probably a serious
                # problem. Exit.
                logcrit("rtgdthread",
                        "Unexpected exception of type %s" % (type(e), ))
                weeutil.weeutil.log_traceback('*** ', syslog.LOG_DEBUG)
                logcrit("rtgdthread", "Thread exiting. Reason: %s" % (e, ))
                return

    def process_packet(self, packet):
        """Process incoming loop packets and generate gauge-data.txt."""

        # get time for debug timing
        t1 = time.time()
        # update the packet cache with this packet
        self.packet_cache.update(packet, packet['dateTime'])
        # do those things that must be done with every loop packet
        # ie update our lows and highs and our 5 and 10 min wind lists
        self.buffer.setLowsAndHighs(packet)
        # generate if we have no minimum interval setting or if minimum
        # interval seconds have elapsed since our last generation
        if self.min_interval is None or (self.last_write + float(self.min_interval)) < time.time():
            try:
                # get a cached packet
                cached_packet = self.packet_cache.get_packet(packet['dateTime'],
                                                             self.max_cache_age)
                logdbg2("rtgdthread", "cached loop packet: %s" % (cached_packet,))
                # set our lost contact flag if applicable
                if self.station_type in LOOP_STATIONS:
                    self.lost_contact_flag = cached_packet[STATION_LOST_CONTACT[self.station_type]['field']] == STATION_LOST_CONTACT[self.station_type]['value']
                data = {}
                # get a data dict from which to construct our file
                data = self.calculate(cached_packet)
                # write our file
                self.write_data(data)
                # set our write time
                self.last_write = time.time()
                # log the generation
                logdbg("rtgdthread",
                       "packet (%s) gauge-data.txt generated in %.5f seconds" % (cached_packet['dateTime'],
                                                                                 (self.last_write-t1)))
            except Exception, e:
                weeutil.weeutil.log_traceback('rtgdthread: **** ')
        else:
            # we skipped this packet so log it
            logdbg("rtgdthread", "packet (%s) skipped" % packet['dateTime'])

    def process_stats(self, package):
        """Process a stats package.

        Inputs:
            package: dict containing the stats data
        """

        if package is not None:
            for key, value in package.iteritems():
                setattr(self, key, value)

    def write_data(self, data):
        """Write the gauge-data.txt file.

        Takes dictionary of data elements, converts them to JSON format and
        writes them to file. Order of data elements may vary from time to time
        but not an issue as gauge-data.txt is just a JSON format data file.

        Inputs:
            data:   dictionary of gauge-data.txt data elements
        """

        with open(self.rtgd_path_file, 'w') as f:
            json.dump(data, f)
            f.close()

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
        data = {}
        # timeUTC - UTC date/time in format YYYY,mm,dd,HH,MM,SS
        data['timeUTC'] = datetime.datetime.utcfromtimestamp(ts).strftime("%Y,%m,%d,%H,%M,%S")
        # date - date in (default) format Y.m.d HH:MM
        data['date'] = time.strftime(self.date_format, time.localtime(ts))
        # dateFormat - date format
        data['dateFormat'] = self.date_format.replace('%','')
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
        temp = temp if temp is not None else 0.0
        data['temp'] = self.temp_format % temp
        # tempTL - today's low temperature
        tempTL_vt = ValueTuple(self.day_stats['outTemp'].min,
                               self.p_temp_type,
                               self.p_temp_group)
        tempTL = convert(tempTL_vt, self.temp_group).value
        tempTL_loop_vt = ValueTuple(self.buffer.tempL_loop[0],
                                    self.p_temp_type,
                                    self.p_temp_group)
        tempL_loop = convert(tempTL_loop_vt, self.temp_group).value
        tempTL = min(i for i in [tempL_loop, tempTL] if i is not None)
        data['tempTL'] = self.temp_format % tempTL
        # tempTH - today's high temperature
        tempTH_vt = ValueTuple(self.day_stats['outTemp'].max,
                               self.p_temp_type,
                               self.p_temp_group)
        tempTH = convert(tempTH_vt, self.temp_group).value
        tempTH_loop_vt = ValueTuple(self.buffer.tempH_loop[0],
                                    self.p_temp_type,
                                    self.p_temp_group)
        tempH_loop = convert(tempTH_loop_vt, self.temp_group).value
        tempTH = max(tempH_loop, tempTH)
        data['tempTH'] = self.temp_format % tempTH
        # TtempTL - time of today's low temp (hh:mm)
        TtempTL = time.localtime(self.day_stats['outTemp'].mintime) if tempL_loop >= tempTL else time.localtime(self.buffer.tempL_loop[1])
        data['TtempTL'] = time.strftime(self.time_format, TtempTL)
        # TtempTH - time of today's high temp (hh:mm)
        TtempTH = time.localtime(self.day_stats['outTemp'].maxtime) if tempH_loop <= tempTH else time.localtime(self.buffer.tempH_loop[1])
        data['TtempTH'] = time.strftime(self.time_format, TtempTH)
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
        # hum - relative humidity
        hum = packet_d['outHumidity'] if packet_d['outHumidity'] is not None else 0.0
        data['hum'] = self.hum_format % hum
        # humTL - today's low relative humidity
        humTL = min(i for i in [self.buffer.humL_loop[0], self.day_stats['outHumidity'].min] if i is not None)
        data['humTL'] = self.hum_format % humTL
        # humTH - today's high relative humidity
        humTH = max(self.buffer.humH_loop[0], self.day_stats['outHumidity'].max)
        data['humTH'] = self.hum_format % humTH
        # ThumTL - time of today's low relative humidity (hh:mm)
        ThumTL = time.localtime(self.day_stats['outHumidity'].mintime) if self.buffer.humL_loop[0] >= humTL else time.localtime(self.buffer.humL_loop[1])
        data['ThumTL'] = time.strftime(self.time_format, ThumTL)
        # ThumTH - time of today's high relative humidity (hh:mm)
        ThumTH = time.localtime(self.day_stats['outHumidity'].maxtime) if self.buffer.humH_loop[0] <= humTH else time.localtime(self.buffer.humH_loop[1])
        data['ThumTH'] = time.strftime(self.time_format, ThumTH)
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
        dew = dew if dew is not None else 0.0
        data['dew'] = self.temp_format % dew
        # dewpointTL - today's low dew point
        dewpointTL_vt = ValueTuple(self.day_stats['dewpoint'].min,
                                   self.p_temp_type,
                                   self.p_temp_group)
        dewpointTL = convert(dewpointTL_vt, self.temp_group).value
        dewpointTL_loop_vt = ValueTuple(self.buffer.dewpointL_loop[0],
                                        self.p_temp_type,
                                        self.p_temp_group)
        dewpointL_loop = convert(dewpointTL_loop_vt, self.temp_group).value
        dewpointTL = min(i for i in [dewpointL_loop, dewpointTL] if i is not None)
        data['dewpointTL'] = self.temp_format % dewpointTL
        # dewpointTH - today's high dew point
        dewpointTH_vt = ValueTuple(self.day_stats['dewpoint'].max,
                                   self.p_temp_type,
                                   self.p_temp_group)
        dewpointTH = convert(dewpointTH_vt, self.temp_group).value
        dewpointTH_loop_vt = ValueTuple(self.buffer.dewpointH_loop[0],
                                        self.p_temp_type,
                                        self.p_temp_group)
        dewpointH_loop = convert(dewpointTH_loop_vt, self.temp_group).value
        dewpointTH = max(dewpointH_loop, dewpointTH)
        data['dewpointTH'] = self.temp_format % dewpointTH
        # TdewpointTL - time of today's low dew point (hh:mm)
        TdewpointTL = time.localtime(self.day_stats['dewpoint'].mintime) if dewpointL_loop >= dewpointTL else time.localtime(self.buffer.dewpointL_loop[1])
        data['TdewpointTL'] = time.strftime(self.time_format, TdewpointTL)
        # TdewpointTH - time of today's high dew point (hh:mm)
        TdewpointTH = time.localtime(self.day_stats['dewpoint'].maxtime) if dewpointH_loop <= dewpointTH else time.localtime(self.buffer.dewpointH_loop[1])
        data['TdewpointTH'] = time.strftime(self.time_format, TdewpointTH)
        # wchill - wind chill
        wchill_vt = ValueTuple(packet_d['windchill'],
                               self.p_temp_type,
                               self.p_temp_group)
        wchill = convert(wchill_vt, self.temp_group).value
        wchill = wchill if wchill is not None else 0.0
        data['wchill'] = self.temp_format % wchill
        # wchillTL - today's low wind chill
        wchillTL_vt = ValueTuple(self.day_stats['windchill'].min,
                                 self.p_temp_type,
                                 self.p_temp_group)
        wchillTL = convert(wchillTL_vt, self.temp_group).value
        wchillTL_loop_vt = ValueTuple(self.buffer.wchillL_loop[0],
                                      self.p_temp_type,
                                      self.p_temp_group)
        wchillL_loop = convert(wchillTL_loop_vt, self.temp_group).value
        wchillTL = min(i for i in [wchillL_loop, wchillTL] if i is not None)
        data['wchillTL'] = self.temp_format % wchillTL
        # TwchillTL - time of today's low wind chill (hh:mm)
        TwchillTL = time.localtime(self.day_stats['windchill'].mintime) if wchillL_loop >= wchillTL else time.localtime(self.buffer.wchillL_loop[1])
        data['TwchillTL'] = time.strftime(self.time_format, TwchillTL)
        # heatindex - heat index
        heatindex_vt = ValueTuple(packet_d['heatindex'],
                                  self.p_temp_type,
                                  self.p_temp_group)
        heatindex = convert(heatindex_vt, self.temp_group).value
        heatindex = heatindex if heatindex is not None else 0.0
        data['heatindex'] = self.temp_format % heatindex
        # heatindexTH - today's high heat index
        heatindexTH_vt = ValueTuple(self.day_stats['heatindex'].max,
                                    self.p_temp_type,
                                    self.p_temp_group)
        heatindexTH = convert(heatindexTH_vt, self.temp_group).value
        heatindexTH_loop_vt = ValueTuple(self.buffer.heatindexH_loop[0],
                                         self.p_temp_type,
                                         self.p_temp_group)
        heatindexH_loop = convert(heatindexTH_loop_vt, self.temp_group).value
        heatindexTH = max(heatindexH_loop, heatindexTH)
        data['heatindexTH'] = self.temp_format % heatindexTH
        # TheatindexTH - time of today's high heat index (hh:mm)
        TheatindexTH = time.localtime(self.day_stats['heatindex'].maxtime) if heatindexH_loop >= heatindexTH else time.localtime(self.buffer.heatindexH_loop[1])
        data['TheatindexTH'] = time.strftime(self.time_format, TheatindexTH)
        # apptemp - apparent temperature
        if 'appTemp' in packet_d:
            # appTemp has been calculated for us so use it
            apptemp_vt = ValueTuple(packet_d['appTemp'],
                                    self.p_temp_type,
                                    self.p_temp_group)
        else:
            # apptemp not available so calculate it
            # first get the arguments for the calculation
            temp_C = convert(temp_vt, 'degree_C').value
            windspeed_vt = ValueTuple(packet_d['windSpeed'],
                                      self.p_wind_type,
                                      self.p_wind_group)
            windspeed_ms = convert(windspeed_vt, 'meter_per_second').value
            # now calculate it
            apptemp_C = weewx.wxformulas.apptempC(temp_C,
                                                 packet_d['outHumidity'],
                                                 windspeed_ms)
            apptemp_vt = ValueTuple(apptemp_C, 'degree_C', 'group_temperature')
        apptemp = convert(apptemp_vt, self.temp_group).value
        apptemp = apptemp if apptemp is not None else convert(ValueTuple(0.0,'degree_C','group_temperature'),
                                                              self.temp_group).value
        data['apptemp'] = self.temp_format % apptemp
        # apptempTL - today's low apparent temperature
        # apptempTH - today's high apparent temperature
        # TapptempTL - time of today's low apparent temperature (hh:mm)
        # TapptempTH - time of today's high apparent temperature (hh:mm)
        if 'appTemp' in self.apptemp_day_stats:
            # we have day stats for appTemp
            apptempTL_vt = ValueTuple(self.apptemp_day_stats['appTemp'].min,
                                      self.p_temp_type,
                                      self.p_temp_group)
            apptempTL = convert(apptempTL_vt, self.temp_group).value
            apptempTL_loop_vt = ValueTuple(self.buffer.apptempL_loop[0],
                                           self.p_temp_type,
                                           self.p_temp_group)
            apptempL_loop = convert(apptempTL_loop_vt, self.temp_group).value
            apptempTL = min(i for i in [apptempL_loop, apptempTL] if i is not None)
            apptempTH_vt = ValueTuple(self.apptemp_day_stats['appTemp'].max,
                                      self.p_temp_type,
                                      self.p_temp_group)
            apptempTH = convert(apptempTH_vt, self.temp_group).value
            apptempTH_loop_vt = ValueTuple(self.buffer.apptempH_loop[0],
                                           self.p_temp_type,
                                           self.p_temp_group)
            apptempH_loop = convert(apptempTH_loop_vt, self.temp_group).value
            apptempTH = max(apptempH_loop, apptempTH)
            TapptempTL = time.localtime(self.apptemp_day_stats['appTemp'].mintime) if apptempL_loop >= apptempTL else time.localtime(self.buffer.apptempL_loop[1])
            TapptempTH = time.localtime(self.apptemp_day_stats['appTemp'].maxtime) if apptempH_loop <= apptempTH else time.localtime(self.buffer.apptempH_loop[1])
        else:
            # There are no appTemp day stats. Normally we would return None but
            # the SteelSeries Gauges do not like None/null. Return the current
            # appTemp value so as to not upset the gauge auto scaling. The day
            # apptemp range wedge will not show, and the mouse-over low/highs
            # will be wrong but it is the best we can do.
            apptempTL = apptemp
            apptempTH = apptemp
            TapptempTL = datetime.date.today().timetuple()
            TapptempTH = datetime.date.today().timetuple()
        apptempTL = apptempTL if apptempTL is not None else convert(ValueTuple(0.0,'degree_C','group_temperature'),
                                                                    self.temp_group).value
        data['apptempTL'] = self.temp_format % apptempTL
        apptempTH = apptempTH if apptempTH is not None else convert(ValueTuple(0.0,'degree_C','group_temperature'),
                                                                    self.temp_group).value
        data['apptempTH'] = self.temp_format % apptempTH
        data['TapptempTL'] = time.strftime(self.time_format, TapptempTL)
        data['TapptempTH'] = time.strftime(self.time_format, TapptempTH)
        # humidex - humidex
        if 'humidex' in packet_d:
            # humidex is in the packet so use it
            humidex_vt = ValueTuple(packet_d['humidex'],
                                    self.p_temp_type,
                                    self.p_temp_group)
            humidex = convert(humidex_vt, self.temp_group).value
        else:   # No humidex in our loop packet so all we can do is calculate it.
            # humidex is not in the packet so calculate it
            temp_C = convert(temp_vt, 'degree_C').value
            dewpoint_C = convert(dew_vt, 'degree_C').value
            humidex_C = weewx.wxformulas.humidexC(temp_C,
                                                  packet_d['outHumidity'])
            humidex_vt = ValueTuple(humidex_C, 'degree_C', 'group_temperature')
            humidex = convert(humidex_vt, self.temp_group).value
        humidex = humidex if humidex is not None else convert(ValueTuple(0.0,'degree_C','group_temperature'),
                                                              self.temp_group).value
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
            pressTL_vt = ValueTuple(self.day_stats['barometer'].min,
                                    self.p_baro_type,
                                    self.p_baro_group)
            pressTL = convert(pressTL_vt, self.pres_group).value
            pressL_loop_vt = ValueTuple(self.buffer.pressL_loop[0],
                                        self.p_baro_type,
                                        self.p_baro_group)
            pressL_loop = convert(pressL_loop_vt, self.pres_group).value
            pressTL = min(i for i in [pressL_loop, pressTL] if i is not None)
            data['pressTL'] = self.pres_format % pressTL
            pressTH_vt = ValueTuple(self.day_stats['barometer'].max,
                                    self.p_baro_type,
                                    self.p_baro_group)
            pressTH = convert(pressTH_vt, self.pres_group).value
            pressH_loop_vt = ValueTuple(self.buffer.pressH_loop[0],
                                        self.p_baro_type,
                                        self.p_baro_group)
            pressH_loop = convert(pressH_loop_vt, self.pres_group).value
            pressTH = max(pressH_loop, pressTH)
            data['pressTH'] = self.pres_format % pressTH
            TpressTL = time.localtime(self.day_stats['barometer'].mintime) if pressL_loop >= pressTL else time.localtime(self.buffer.pressL_loop[1])
            data['TpressTL'] = time.strftime(self.time_format, TpressTL)
            TpressTH = time.localtime(self.day_stats['barometer'].maxtime) if pressH_loop <= pressTH else time.localtime(self.buffer.pressH_loop[1])
            data['TpressTH'] = time.strftime(self.time_format, TpressTH)
        else:
            data['pressTL'] = self.pres_format % 0.0
            data['pressTH'] = self.pres_format % 0.0
            data['TpressTL'] = None
            data['TpressTH'] = None
        # pressL - all time low barometer
        if self.min_barometer is not None:
            pressL_vt = ValueTuple(self.min_barometer,
                                   self.p_baro_type,
                                   self.p_baro_group)
        else:
            pressL_vt = ValueTuple(850,
                                   'hPa',
                                   self.p_baro_group)
        pressL = convert(pressL_vt, self.pres_group).value
        data['pressL'] = self.pres_format % pressL
        # pressH - all time high barometer
        if self.max_barometer is not None:
            pressH_vt = ValueTuple(self.max_barometer,
                                   self.p_baro_type,
                                   self.p_baro_group)
        else:
            pressH_vt = ValueTuple(1100,
                                   'hPa',
                                   self.p_baro_group)
        pressH = convert(pressH_vt, self.pres_group).value
        data['pressH'] = self.pres_format % pressH
        # presstrendval -  pressure trend value
        _p_trend_val = calc_trend('barometer', press_vt, self.pres_group,
                                  self.db_manager, ts - 3600, 300)
        presstrendval = _p_trend_val if _p_trend_val is not None else 0.0
        data['presstrendval'] = self.pres_format % presstrendval
        # rfall - rain today
        rainDay = self.day_stats['rain'].sum + self.buffer.rainsum
        rainT_vt = ValueTuple(rainDay, self.p_rain_type, self.p_rain_group)
        rainT = convert(rainT_vt, self.rain_group).value
        rainT = rainT if rainT is not None else 0.0
        data['rfall'] = self.rain_format % rainT
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
            rrateTM_vt = ValueTuple(self.day_stats['rainRate'].max,
                                    self.p_rainr_type,
                                    self.p_rainr_group)
            rrateTM = convert(rrateTM_vt, self.rainrate_group).value
        else:
            rrateTM = 0
        rrateTM_loop_vt = ValueTuple(self.buffer.rrateH_loop[0], self.p_rainr_type, self.p_rainr_group)
        rrateH_loop = convert(rrateTM_loop_vt, self.rainrate_group).value
        rrateTM = max(rrateH_loop, rrateTM, rrate)
        data['rrateTM'] = self.rainrate_format % rrateTM
        # TrrateTM - time of today's maximum rain rate (per hour)
        if 'rainRate' not in self.day_stats:
            data['TrrateTM'] = '00:00'
        else:
            TrrateTM = time.localtime(self.day_stats['rainRate'].maxtime) if rrateH_loop <= rrateTM else time.localtime(self.buffer.rrateH_loop[1])
            data['TrrateTM'] = time.strftime(self.time_format, TrrateTM)
        # hourlyrainTH - Today's highest hourly rain
        ###FIX ME - need to determine hourlyrainTH
        data['hourlyrainTH'] = "0.0"
        # ThourlyrainTH - time of Today's highest hourly rain
        ###FIX ME - need to determine ThourlyrainTH
        data['ThourlyrainTH'] = "00:00"
        # LastRainTipISO -
        ###FIX ME - need to determine LastRainTipISO
        data['LastRainTipISO'] = "00:00"
        # wlatest - latest wind speed reading
        wlatest_vt = ValueTuple(packet_d['windSpeed'],
                                self.p_wind_type,
                                self.p_wind_group)
        wlatest = convert(wlatest_vt, self.wind_group).value if wlatest_vt.value is not None else 0.0
        data['wlatest'] = self.wind_format % wlatest
        # wspeed - wind speed (average)
        wspeed_vt = ValueTuple(self.windSpeedAvg,
                               self.p_wind_type,
                               self.p_wind_group)
        wspeed = convert(wspeed_vt, self.wind_group).value
        wspeed = wspeed if wspeed is not None else 0.0
        data['wspeed'] = self.wind_format % wspeed
        # windTM - today's high wind speed (average)
        windTM_vt = ValueTuple(self.day_stats['windSpeed'].max,
                               self.p_wind_type,
                               self.p_wind_group)
        windTM = convert(windTM_vt, self.wind_group).value
        windTM_loop_vt = ValueTuple(self.buffer.windM_loop[0],
                                    self.p_wind_type,
                                    self.p_wind_group)
        windM_loop = convert(windTM_loop_vt, self.wind_group).value
        windTM = max(windM_loop, windTM)
        data['windTM'] = self.wind_format % windTM
        # wgust - 10 minute high gust
        wgust = self.buffer.tenMinuteWindGust()
        wgust_vt = ValueTuple(wgust, self.p_wind_type, self.p_wind_group)
        wgust = convert(wgust_vt, self.wind_group).value
        wgust = wgust if wgust is not None else 0.0
        data['wgust'] = self.wind_format % wgust
        # wgustTM - today's high wind gust
        wgustTM_vt = ValueTuple(self.day_stats['wind'].max,
                                self.p_wind_type,
                                self.p_wind_group)
        wgustTM = convert(wgustTM_vt, self.wind_group).value
        wgustM_loop_vt = ValueTuple(self.buffer.wgustM_loop[0],
                                    self.p_wind_type,
                                    self.p_wind_group)
        wgustM_loop = convert(wgustM_loop_vt, self.wind_group).value
        wgustTM = max(wgustM_loop, wgustTM)
        data['wgustTM'] = self.wind_format % wgustTM
        # TwgustTM - time of today's high wind gust (hh:mm)
        TwgustTM = time.localtime(self.day_stats['wind'].maxtime) if wgustM_loop <= wgustTM else time.localtime(self.buffer.wgustM_loop[2])
        data['TwgustTM'] = time.strftime(self.time_format, TwgustTM)
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
        bearingTM = self.day_stats['wind'].max_dir if self.day_stats['wind'].max_dir is not None else 0
        bearingTM = self.buffer.wgustM_loop[1] if wgustTM == wgustM_loop else bearingTM
        data['bearingTM'] = self.dir_format % bearingTM
        # BearingRangeFrom10 - The 'lowest' bearing in the last 10 minutes
        # (or as configured using AvgBearingMinutes in cumulus.ini), rounded
        # down to nearest 10 degrees
        if self.windDirAvg is not None:
            fromBearing = max((self.windDirAvg-d) if ((d-self.windDirAvg) < 0 and s > 0) else None for x,y,s,d,t in self.buffer.wind_dir_list) if self.buffer.tenMinuteWind_valid else None
            BearingRangeFrom10 = self.windDirAvg - fromBearing if fromBearing is not None else 0.0
            if BearingRangeFrom10 < 0:
                BearingRangeFrom10 += 360
            elif BearingRangeFrom10 > 360:
                BearingRangeFrom10 -= 360
        else:
            BearingRangeFrom10 = 0.0
        data['BearingRangeFrom10'] = self.dir_format % BearingRangeFrom10
        # BearingRangeTo10 - The 'highest' bearing in the last 10 minutes
        # (or as configured using AvgBearingMinutes in cumulus.ini), rounded
        # up to the nearest 10 degrees
        if self.windDirAvg is not None:
            toBearing = max((d-self.windDirAvg) if ((d-self.windDirAvg) > 0 and s > 0) else None for x,y,s,d,t in self.buffer.wind_dir_list) if self.buffer.tenMinuteWind_valid else None
            BearingRangeTo10 = self.windDirAvg + toBearing if toBearing is not None else 0.0
            if BearingRangeTo10 < 0:
                BearingRangeTo10 += 360
            elif BearingRangeTo10 > 360:
                BearingRangeTo10 -= 360
        else:
            BearingRangeTo10 = 0.0
        data['BearingRangeTo10'] = self.dir_format % BearingRangeTo10
        # domwinddir - Today's dominant wind direction as compass point
        deg = 90.0 - math.degrees(math.atan2(self.day_stats['wind'].ysum,
                                  self.day_stats['wind'].xsum))
        dom_dir = deg if deg >= 0 else deg + 360.0
        data['domwinddir'] = degreeToCompass(dom_dir)
        # WindRoseData -
        data['WindRoseData'] = self.rose
        # windrun - wind run (today)
        last_ts = self.db_manager.lastGoodStamp()
        try:
            wind_sum_vt = ValueTuple(self.day_stats['wind'].sum,
                                     self.p_wind_type,
                                     self.p_wind_group)
            windrun_day_average = (last_ts - weeutil.weeutil.startOfDay(ts))/3600.0 * convert(wind_sum_vt,
                                                                                              self.wind_group).value/self.day_stats['wind'].count
        except:
            windrun_day_average = 0.0
        if self.windrun_loop:   # is loop/realtime estimate
            loop_hours = (ts - last_ts)/3600.0
            try:
                windrun = windrun_day_average + loop_hours * convert((self.buffer.windsum,
                                                                      self.p_wind_type,
                                                                      self.p_wind_group),
                                                                     self.wind_group).value/self.buffer.windcount
            except:
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
            UV = 0.0
        else:
            UV = packet_d['UV'] if packet_d['UV'] is not None else 0.0
        data['UV'] = self.uv_format % UV
        # UVTH - today's high UV index
        if 'UV' not in self.day_stats:
            UVTH = 0.0
        else:
            UVTH = self.day_stats['UV'].max
        UVTH = max(self.buffer.UVH_loop[0], UVTH, UV)
        data['UVTH'] = self.uv_format % UVTH
        # SolarRad - solar radiation W/m2
        if 'radiation' not in packet_d:
            SolarRad = 0.0
        else:
            SolarRad = packet_d['radiation']
        SolarRad = SolarRad if SolarRad is not None else 0.0
        data['SolarRad'] = self.rad_format % SolarRad
        # SolarTM - today's maximum solar radiation W/m2
        if 'radiation' not in self.day_stats:
            SolarTM = 0.0
        else:
            SolarTM = self.day_stats['radiation'].max
        SolarTM = max(self.buffer.SolarH_loop[0], SolarTM, SolarRad)
        data['SolarTM'] = self.rad_format % SolarTM
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
            temp_C = convert(temp_vt, 'degree_C').value
            cb = weewx.wxformulas.cloudbase_Metric(temp_C,
                                                   packet_d['outHumidity'],
                                                   self.altitude_m)
            cb_vt = ValueTuple(cb, 'meter', self.p_alt_group)
        cloudbase = convert(cb_vt, self.alt_group).value
        cloudbase = cloudbase if cloudbase is not None else 0.0
        data['cloudbasevalue'] = self.alt_format % cloudbase
        # forecast - forecast text
        # if we have any scroller text set then display that otherwise use the
        # Zambretti text
        if self.scroller_text is not None:
            data['forecast'] = self.scroller_text
        else:
            data['forecast'] = self.forecast.get_zambretti_text()
        # version - weather software version
        data['version'] = '%s' % weewx.__version__
        # build -
        data['build'] = ''
        # ver - gauge-data.txt version number
        data['ver'] = self.version
        return data

    def new_archive_record(self, record):
        """Control processing when new a archive record is presented."""

        # set our lost contact flag if applicable
        if self.station_type in ARCHIVE_STATIONS:
            self.lost_contact_flag = record[STATION_LOST_CONTACT[self.station_type]['field']] == STATION_LOST_CONTACT[self.station_type]['value']
        # save the windSpeed value to use as our archive period average
        if 'windSpeed' in record:
            self.windSpeedAvg = record['windSpeed']
        else:
            self.windSpeedAvg = None
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


# ============================================================================
#                             class RtgdBuffer
# ============================================================================


class RtgdBuffer(object):
    """Class to buffer various loop packet obs.

    If archive based stats are an efficient means of getting stats for today.
    However, their use would mean that any daily stat (eg todays max outTemp)
    that 'occurs' after the most recent archive record but before the next
    archive record is written to archive will not be captured. For this reason
    selected loop data is buffered to ensure that such stats are correctly
    reflected.
    """

    def __init__(self, config_dict):
        """Initialise an instance of our class."""

        # Initialise min/max for loop data received since last archive record
        # and sum/counter for windrun calculator
        self.reset_loop_stats()

        # Setup lists/flags for 5 and 10 minute wind stats
        self.wind_list = []
        self.wind_dir_list = []
        self.averageWind_valid = False
        self.tenMinuteWind_valid = False

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
        self.tempL_loop = [None,None]
        self.tempH_loop = [None,None]
        self.dewpointL_loop = [None,None]
        self.dewpointH_loop = [None,None]
        self.apptempL_loop = [None,None]
        self.apptempH_loop = [None,None]
        self.wchillL_loop = [None,None]
        self.heatindexH_loop = [None,None]
        self.wgustM_loop = [None,None,None]
        self.pressL_loop = [None,None]
        self.pressH_loop = [None,None]
        self.rrateH_loop = [None,None]
        self.humL_loop = [None,None]
        self.humH_loop = [None,None]
        self.windM_loop = [None, None]
        self.UVH_loop = [None,None]
        self.SolarH_loop = [None,None]

    def averageWind(self):
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
        wind data is held. self.averageWind_valid is used to check whether the
        result is valid or not.

        Inputs:
            Nothing

        Returns:
            Average wind speed over the last 'archive interval' seconds
        """

        if self.averageWind_valid:
            if len(self.wind_list) > 0:
                average = sum(w for w,_ in self.wind_list)/float(len(self.wind_list))
            else:
                average = 0.0
        else:
            average = 0.0
        return average

    def tenMinuteAverageWindDir(self):
        """ Calculate average wind direction over the last 10 minutes.

        Takes list of last 10 minutes of loop wind speed and direction data and
        calculates a vector average direction.
        Result is only considered valid if a full 10 minutes of loop wind data
        is held. self.tenMinuteWind_valid is used to check whether the result
        is valid or not.

        Inputs:
            Nothing

        Returns:
            10 minute vector average wind direction
        """

        if self.tenMinuteWind_valid:
            if len(self.wind_dir_list) > 0:
                avg_dir = 90.0 - math.degrees(math.atan2(sum(y for x,y,s,d,t in self.wind_dir_list),
                                                         sum(x for x,y,s,d,t in self.wind_dir_list)))
                avg_dir = avg_dir if avg_dir > 0 else avg_dir + 360.0
            else:
                avg_dir = None
        else:
            avg_dir = None
        return avg_dir

    def tenMinuteWindGust(self):
        """ Calculate 10 minute wind gust.

        Takes list of last 10 minutes of loop wind speed data and finds the max
        value.  Units used are loop data units so unit conversion of the result
        may be required.
        Result is only considered valid if a full 10 minutes of loop wind data
        is held. self.tenMinuteWind_valid is used to check whether the result
        is valid or not.

        Inputs:
            Nothing

        Returns:
            10 minute wind gust
        """

        if self.tenMinuteWind_valid:
            if len(self.wind_dir_list) > 0:
                gust = max(s for x,y,s,d,t in self.wind_dir_list)
            else:
                gust = None
        else:
            gust = None
        return gust

    def setLowsAndHighs(self, packet):
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

        # process temp
        outTemp = packet_d.get('outTemp', None)
        if outTemp is not None:
            self.tempL_loop = [outTemp, ts] if (outTemp < self.tempL_loop[0] or self.tempL_loop[0] is None) else self.tempL_loop
            self.tempH_loop = [outTemp, ts] if outTemp > self.tempH_loop[0] else self.tempH_loop

        # process dewpoint
        dewpoint = packet_d.get('dewpoint', None)
        if dewpoint is not None:
            self.dewpointL_loop = [dewpoint, ts] if (dewpoint < self.dewpointL_loop[0] or self.dewpointL_loop[0] is None) else self.dewpointL_loop
            self.dewpointH_loop = [dewpoint, ts] if dewpoint > self.dewpointH_loop[0] else self.dewpointH_loop

        # process appTemp
        appTemp = packet_d.get('appTemp', None)
        if appTemp is not None:
            self.apptempL_loop = [appTemp, ts] if (appTemp < self.apptempL_loop[0] or self.apptempL_loop[0] is None) else self.apptempL_loop
            self.apptempH_loop = [appTemp, ts] if appTemp > self.apptempH_loop[0] else self.apptempH_loop

        # process windchill
        windchill = packet_d.get('windchill', None)
        if windchill is not None:
            self.wchillL_loop = [windchill, ts] if (windchill < self.wchillL_loop[0] or self.wchillL_loop[0] is None) else self.wchillL_loop

        # process heatindex
        heatindex = packet_d.get('heatindex', None)
        if heatindex is not None:
            self.heatindexH_loop = [heatindex, ts] if heatindex > self.heatindexH_loop[0] else self.heatindexH_loop

        # process barometer
        barometer = packet_d.get('barometer', None)
        if barometer is not None:
            self.pressL_loop = [barometer, ts] if (barometer < self.pressL_loop[0] or self.pressL_loop[0] is None) else self.pressL_loop
            self.pressH_loop = [barometer, ts] if barometer > self.pressH_loop[0] else self.pressH_loop

        # process rain
        rain = packet_d.get('rain', None)
        self.rainsum += rain if rain is not None else self.rainsum

        # process rainRate
        rainRate = packet_d.get('rainRate', None)
        if rainRate is not None:
            self.rrateH_loop = [rainRate, ts] if rainRate > self.rrateH_loop[0] else self.rrateH_loop

        # process humidity
        outHumidity = packet_d.get('outHumidity', None)
        if outHumidity is not None:
            self.humL_loop = [outHumidity, ts] if (outHumidity < self.humL_loop[0] or self.humL_loop[0] is None) else self.humL_loop
            self.humH_loop = [outHumidity, ts] if outHumidity > self.humH_loop[0] else self.humH_loop

        # process UV
        UV = packet_d.get('UV', None)
        if UV is not None:
            self.UVH_loop = [UV, ts] if UV > self.UVH_loop[0] else self.UVH_loop

        # process radiation
        radiation = packet_d.get('radiation', None)
        if radiation is not None:
            self.SolarH_loop = [radiation, ts] if radiation > self.SolarH_loop[0] else self.SolarH_loop

        # process windSpeed/windDir
        # if windDir exists then get it, if it does not exist get None
        windDir = packet_d.get('windDir', None)
        # if windSpeed exists get it, if it does not exist or is None then
        # get 0.0
        windSpeed = packet_d.get('windSpeed', 0.0)
        windSpeed = 0.0 if windSpeed is None else windSpeed
        self.windsum += windSpeed
        self.windcount += 1
        # Have we seen a new high gust? If so update self.wgustM_loop but only
        # if we have a corresponding wind direction
        if windSpeed > self.wgustM_loop[0] and windDir is not None:
            self.wgustM_loop = [windSpeed, windDir, ts]
        # average wind speed
        self.wind_list.append([windSpeed, ts])
        # if we have samples in our list then delete any too old
        if len(self.wind_list) > 0:
            # calc ts of oldest sample we want to retain
            old_ts = ts - self.wind_period
            # if we have (archive_interval) of data in our list set flag that
            # averageWind result is valid
            self.averageWind_valid = self.wind_list[0][1] <= old_ts
            # Remove any samples older than 5 minutes
            self.wind_list = [s for s in self.wind_list if s[1] > old_ts]
        # get our latest (archive_interval) average wind
        windM_loop = self.averageWind() if self.averageWind_valid else 0.0
        # have we seen a new high (archive_interval) avg wind? if so update
        # self.windM_loop
        self.windM_loop = [windM_loop, ts] if windM_loop > self.windM_loop[0] else self.windM_loop
        # Update the 10 minute wind direction list, but only if windDir is not
        # None
        if windDir is not None:
            self.wind_dir_list.append([windSpeed * math.cos(math.radians(90.0 - windDir)),
                                      windSpeed * math.sin(math.radians(90.0 - windDir)),
                                      windSpeed, windDir, ts])
        # if we have samples in our list then delete any too old
        if len(self.wind_dir_list) > 0:
            # calc ts of oldest sample we want to retain
            old_ts = ts - self.wind_period
            # if we have 10 minutes of data in our list set flag that
            # calcTenMinuteAverageWindDir result is valid
            self.tenMinuteWind_valid = self.wind_dir_list[0][4] <= old_ts
            # Remove any samples older than 10 minutes
            self.wind_dir_list = [s for s in self.wind_dir_list if s[4] > old_ts]


# ============================================================================
#                            Class CachedPacket
# ============================================================================


class CachedPacket():
    """Class to cache loop packets.

    Cache consists of a dictionary of value, timestamp pairs where timestamp is
    the timestamp of the packet when obs was last seen and value is the value
    of the obs at that time. None values may be cached.

    A cached loop packet may be obtained by calling the get_packet() method.
    """

    # These fields must be available in every loop packet read from the
    # cache. Initialise them to None.
    OBS = ["cloudbase", "windDir", "windrun", "inHumidity", "outHumidity",
           "barometer", "radiation", "rain", "rainRate","windSpeed",
           "appTemp", "dewpoint", "heatindex", "humidex", "inTemp",
           "outTemp", "windchill", "UV"]

    def __init__(self):

        self.cache = dict()
        _ts = int(time.time() + 0.5)
        for _obs in CachedPacket.OBS:
            self.cache[_obs] = {'value': None, 'ts': _ts}
        self.unit_system = None

    def prime(self, record, ts):
        """Prime the cache from an archive record."""

        if self.unit_system is None:
            self.unit_system = record['usUnits']
        elif self.unit_system != record['usUnits']:
            record = weewx.units.to_std_system(record, self.unit_system)
        for obs in record:
            if record[obs] is not None and obs in CachedPacket.OBS:
                self.cache[obs] = {'value': record[obs], 'ts': ts}

    def update(self, packet, ts):
        """Update the cache from a loop packet."""

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


def degreeToCompass(x):
    """Convert degrees to ordinal compass point.

    Input:
        x:      degrees

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
    return [round(x,1) for x in rose]