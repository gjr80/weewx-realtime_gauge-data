The Realtime gauge-data extension provides for near realtime updating of the
SteelSeries Weather Gauges by WeeWX. The extension consists of a WeeWX service
that generates the file gauge-data.txt used to update the SteelSeries Weather
Gauges.


Pre-Requisites

The Realtime gauge-data extension requires WeeWX v3.4.0 or greater.

A number of fields have additional pre-requisites:

-   CurrentSolarMax. Requires the pyephem(http://weewx.com/docs/setup.htm)
    module be installed.

-   forecast:

    -   If using the Zambretti forecast text then the WeeWX forecasting
        extension must be installed.

    -   If a text file is to be used as the scroller text source then a
        suitable text file must be available on the WeeWX machine.


Installation Instructions

Installation using the wee_extension utility

Note:   Symbolic names are used below to refer to some file location on the
WeeWX system. These symbolic names allow a common name to be used to refer to
a directory that may be different from system to system. The following symbolic
names are used below:

-   $DOWNLOAD_ROOT. The path to the directory containing the downloaded
    Realtime gauge-data extension.

-   $HTML_ROOT. The path to the directory where WeeWX generated reports are
    saved. This directory is normally set in the [StdReport] section of
    weewx.conf. Refer to 'where to find things' in the WeeWX User's Guide:
    http://weewx.com/docs/usersguide.htm#Where_to_find_things for further
    information.

-   $BIN_ROOT. The path to the directory where WeeWX executables are located.
    This directory varies depending on WeeWX installation method. Refer to
    'where to find things' in the WeeWX User's Guide:
    http://weewx.com/docs/usersguide.htm#Where_to_find_things for further
    information.

-   $SKIN_ROOT. The path to the directory where WeeWX skin directories are
    located. This directory is normally set in the [StdReport] section of
    weewx.conf. Refer to 'where to find things' in the WeeWX User's Guide:
    http://weewx.com/docs/usersguide.htm#Where_to_find_things for further
    information.

1.  Download the latest Realtime gauge-data extension from the Realtime
gauge-data releases page (https://github.com/gjr80/weewx-realtime_gauge-data
/releases) into a directory accessible from the WeeWX machine.

    $ wget -P $DOWNLOAD_ROOT https://github.com/gjr80/weewx-realtime_gauge-data
/releases/download/v0.3.7/rtgd-0.3.7.tar.gz

	where $DOWNLOAD_ROOT is the path to the directory where the Realtime
    gauge-data extension is to be downloaded.

2.  Install the Realtime gauge-data extension downloaded at step 1 using the
wee_extension utility:

    $ wee_extension --install=$DOWNLOAD_ROOT/rtgd-0.3.7.tar.gz

    This will result in output similar to the following:

        Request to install '/var/tmp/rtgd-0.3.7.tar.gz'
        Extracting from tar archive /var/tmp/rtgd-0.3.7.tar.gz
        Saving installer file to /home/weewx/bin/user/installer/Rtgd
        Saved configuration dictionary. Backup copy at /home/weewx/weewx.conf.20190101124410
        Finished installing extension '/var/tmp/rtgd-0.3.7.tar.gz'

3. Restart WeeWX:

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


Manual installation

1.  Download the latest Realtime gauge-data extension from the Realtime
gauge-data releases page (https://github.com/gjr80/weewx-realtime_gauge-data
/releases) into a directory accessible from the WeeWX machine.

    $ wget -P $DOWNLOAD_ROOT https://github.com/gjr80/weewx-realtime_gauge-data
/releases/download/v0.3.7/rtgd-0.3.7.tar.gz

	where $DOWNLOAD_ROOT is the path to the directory where the Realtime
    gauge-data extension is to be downloaded.

2.  Unpack the extension as follows:

    $ tar xvfz rtgd-0.3.7.tar.gz

3.  Copy files from within the resulting directory as follows:

    $ cp rtgd/bin/user/rtgd.py $BIN_ROOT/user

	replacing the symbolic name $BIN_ROOT with the nominal locations for your
    installation.

4.  Edit weewx.conf:

    $ vi weewx.conf

5.  In weewx.conf, add a [RealtimeGaugeData] stanza as per the abbreviated 
instructions for use in the comments at the start of $BIN_ROOT/user/rtgd.py.

6.  In weewx.conf, modify the [Engine] [[Services]] section by adding the
RealtimeGaugeData service to the list of process services to be run:

    [Engine]
        [[Services]]

            report_services = weewx.engine.StdPrint, weewx.engine.StdReport, user.rtgd.RealtimeGaugeData

7. Restart WeeWX:

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