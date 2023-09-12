The Realtime gauge-data extension provides for near realtime updating of the
SteelSeries Weather Gauges by WeeWX. The extension consists of a WeeWX service
that generates the file gauge-data.txt used to update the SteelSeries Weather
Gauges.


Pre-Requisites

The Realtime gauge-data extension requires WeeWX v4.0.0 or greater using either
Python 2 or Python 3.

A number of fields have additional pre-requisites:

-   CurrentSolarMax. Requires the pyephem(http://weewx.com/docs/setup.htm)
    module be installed.

-   forecast:

    -   If using the Zambretti forecast text then the WeeWX forecasting
        extension must be installed.

    -   If a text file is to be used as the scroller text source then a
        suitable text file must be available on the WeeWX machine.


Installation Instructions

    Note: The symbolic name $HTML_ROOT is used below to refer to the path to
          the directory where WeeWX generated reports are saved. This directory
          is normally set in the [StdReport] section of weewx.conf. Refer to
          http://weewx.com/docs/usersguide.htm#Where_to_find_things in the
          WeeWX User's Guide (http://weewx.com/docs/usersguide.htm) for
          further information.

1.  Install the Realtime gauge-data extension using the wee_extension utility:

    - download the latest Realtime gauge-data extension package:

        $ wget -P /var/tmp https://github.com/gjr80/weewx-realtime_gauge-data/releases/download/v1.0.0a1/rtgd-1.0.0a1.tar.gz

    - install the Realtime gauge-data extension:

        $ wee_extension --install=/var/tmp/rtgd-1.0.0a1.tar.gz

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

This will result in the gauge-data.txt file being generated on receipt of each
loop packet. A default installation will result in the generated gauge-data.txt
file being placed in the $HTML_ROOT directory. The Realtime gauge-data
extension installation can be further customized (eg file locations, frequency
of generation etc) by referring to the Realtime gauge-data extension wiki.


Support

General support issues may be raised in the Google Groups weewx-user forum
(https://groups.google.com/group/weewx-user). Specific bugs in the Realtime
gauge-data extension code should be the subject of a new issue raised via the
Issues Page (https://github.com/gjr80/weewx-realtime_gdrt/issues.


Licensing

The Realtime gauge-data extension is licensed under the GNU Public License v3
(https://github.com/gjr80/weewx-realtime_gauge-data/blob/master/LICENSE).
