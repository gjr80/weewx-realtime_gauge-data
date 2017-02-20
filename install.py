#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
#                     Installer for Realtime gauge-data
#
# Version: 0.2.3                                        Date: 20 February 2017
#
# Revision History
#   20 February 2017    v0.2.3
#       - no chnages, bump version number only
#   19 February 2017    v0.2.2
#       - added mile to string formats
#   15 February 2017    v0.2.1
#       - minor formatting changes
#   24 January 2017      v0.2
#       - updated weewx.conf options
#   10 January 2017      v0.1
#       - initial implementation
#

import weewx

from distutils.version import StrictVersion
from setup import ExtensionInstaller

REQUIRED_VERSION = "3.4.0"
RTGD_VERSION = "0.2.3"

def loader():
    return RtgdInstaller()

class RtgdInstaller(ExtensionInstaller):
    def __init__(self):
        if StrictVersion(weewx.__version__) < StrictVersion(REQUIRED_VERSION):
            msg = "%s requires weeWX %s or greater, found %s" % ('Rtgd ' + RTGD_VERSION,
                                                                 REQUIRED_VERSION,
                                                                 weewx.__version__)
            raise weewx.UnsupportedFeature(msg)
        super(RtgdInstaller, self).__init__(
            version=RTGD_VERSION,
            name='Rtgd',
            description='weeWX support for near realtime updating of the SteelSeries Weather Gauges.',
            author="Gary Roderick",
            author_email="gjroderick@gmail.com",
            report_services=['user.rtgd.RealtimeGaugeData'],
            config={
                'RealtimeGaugeData': {
                    'date_format': '%Y.%m.%d %H:%M',
                    'min_interval': '9',
                    'rtgd_path': '/home/weewx/public_html',
                    'windrose_points': '16',
                    'windrose_period': '86400',
                    'Calculate': {
                        'atc': '0.8',
                        'nfac': '2',
                        'Algorithm': {
                            'maxSolarRad': 'RS'
                        },
                    },
                    'StringFormats': {
                        'degree_C': '%.1f',
                        'degree_F': '%.1f',
                        'degree_compass': '%.0f',
                        'hPa': '%.1f',
                        'inHg': '%.3f',
                        'inch': '%.2f',
                        'inch_per_hour': '%.2f',
                        'km_per_hour': '%.0f',
                        'km': '%.1f',
                        'knot': '%.0f',
                        'mbar': '%.1f',
                        'meter': '%.0f',
                        'meter_per_second': '%.1f',
                        'mile': '%.1f',
                        'mile_per_hour': '%.0f',
                        'mm': '%.1f',
                        'mm_per_hour': '%.1f',
                        'percent': '%.0f',
                        'uv_index': '%.1f',
                        'watt_per_meter_squared': '%.0f'
                    },
                    'Groups': {
                        'group_pressure': 'hPa',
                        'group_rain': 'mm',
                        'group_rainrate': 'mm_per_hour',
                        'group_speed': 'km_per_hour',
                        'group_distance': 'km',
                        'group_temperature': 'degree_C',
                        'group_percent': 'percent',
                        'group_uv': 'uv_index',
                        'group_direction': 'degree_compass'
                    }
                }
            },
            files=[('bin/user', ['bin/user/rtgd.py'])]
        )
