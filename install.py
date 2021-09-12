"""
This program is free software; you can redistribute it and/or modify it under the
terms of the GNU General Public License as published by the Free Software
Foundation; either version 2 of the License, or (at your option) any later
version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY
WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
PARTICULAR PURPOSE.  See the GNU General Public License for more details.

                     Installer for Realtime gauge-data

Version: 0.5.0b2                                        Date: ?? ??????? 2021

Revision History

    ?? ????? 2021       v0.5.0
        - fix incorrect date format
        - changed WeeWX required version to 4.0.0
    23 November 2019    v0.4.2
        - bumped version only
    20 November 2019    v0.4.1
        - bumped version only
    16 November 2019    v0.4.0
        - bumped version only
    4 April 2019        v0.3.7
        - bumped version only
    28 March 2019       v0.3.6
        - bumped version only
    1 January 2019      v0.3.5
        - reworked default install [RealtimeGaugeData] config stanza as per
          changes to rtgd.py
        - installation now includes a blank [[DS]] config stanza
    26 April 2018       v0.3.4 (not released)
        - bumped version only
    26 April 2018       v0.3.3
        - bumped version only
    20 January 2018     v0.3.2
        - bumped version only
     3 December 2017     v0.3.1
        - bumped version only
    4 September 2017    v0.3.0
        - added [[WU]] config stanza to support WU forecast text
    8 July 2017         v0.2.14
        - changed default decimal places for foot, inHg, km_per_hour and
          mile_per_hour
    6 May 2017          v0.2.13
        - bumped version only
    29 March 2017       v0.2.12
        - never released
    22 March 2017       v0.2.11
        - added foot StringFormat config option
    17 March 2017       v0.2.10
        - bumped version only
    7 March 2017        v0.2.9
        - bumped version number only
    27 February 2017    v0.2.8
        - bumped version number only
    26 February 2017    v0.2.7
        - bumped version number only
    22 February 2017    v0.2.6
        - reworked Groups
    21 February 2017    v0.2.5
        - trimmed a number of config options
    20 February 2017    v0.2.4
        - bumped version number only
    20 February 2017    v0.2.3
         - removed min_interval config option
    19 February 2017    v0.2.2
         - added mile to string formats
    15 February 2017    v0.2.1
         - minor formatting changes
    24 January 2017      v0.2
        - updated weewx.conf options
    10 January 2017      v0.1
        - initial implementation
"""

import weewx

from distutils.version import StrictVersion
from setup import ExtensionInstaller

REQUIRED_VERSION = "4.0.0"
RTGD_VERSION = "0.5.0"


def loader():
    return RtgdInstaller()


class RtgdInstaller(ExtensionInstaller):
    def __init__(self):
        if StrictVersion(weewx.__version__) < StrictVersion(REQUIRED_VERSION):
            msg = "%s requires WeeWX %s or greater, found %s" % ('Rtgd ' + RTGD_VERSION,
                                                                 REQUIRED_VERSION,
                                                                 weewx.__version__)
            raise weewx.UnsupportedFeature(msg)
        super(RtgdInstaller, self).__init__(
            version=RTGD_VERSION,
            name='Rtgd',
            description='WeeWX support for near realtime updating of the SteelSeries Weather Gauges.',
            author="Gary Roderick",
            author_email="gjroderick<@>gmail.com",
            report_services=['user.rtgd.RealtimeGaugeData'],
            config={
                'RealtimeGaugeData': {
                    'date_format': '%Y-%m-%d %H:%M',
                    'rtgd_path': '/home/weewx/public_html',
                    'scroller_source': 'text|file|WU|DS|Zambretti',
                    'StringFormats': {
                        'degree_C': '%.1f',
                        'degree_F': '%.1f',
                        'degree_compass': '%.0f',
                        'foot': '%.0f',
                        'hPa': '%.1f',
                        'inHg': '%.2f',
                        'inch': '%.2f',
                        'inch_per_hour': '%.2f',
                        'km_per_hour': '%.1f',
                        'km': '%.1f',
                        'mbar': '%.1f',
                        'meter': '%.0f',
                        'meter_per_second': '%.1f',
                        'mile': '%.1f',
                        'mile_per_hour': '%.1f',
                        'mm': '%.1f',
                        'mm_per_hour': '%.1f',
                        'percent': '%.0f',
                        'uv_index': '%.1f',
                        'watt_per_meter_squared': '%.0f'
                    },
                    'Groups': {
                        'group_altitude': 'foot',
                        'group_pressure': 'hPa',
                        'group_rain': 'mm',
                        'group_speed': 'km_per_hour',
                        'group_temperature': 'degree_C'
                    },
                    'DS': {
                        'api_key': 'xxxxxxxxxxxxxxxx'
                    }
                }
            },
            files=[('bin/user', ['bin/user/rtgd.py'])]
        )
