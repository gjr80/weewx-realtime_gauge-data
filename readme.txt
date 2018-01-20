The Realtime gauge-data extension provides for near realtime updating of the
SteelSeries Weather Gauges by weeWX. The extension consists of a weeWX service
that generates the file gauge-data.txt used to update the SteelSeries Weather
Gauges.

Pre-Requisites

The Realtime gauge-data extension requires weeWX v3.4.0 or greater.

Installation Instructions

Installation using the wee_extension utility

Note:   Symbolic names are used below to refer to some file location on the
weeWX system. These symbolic names allow a common name to be used to refer to
a directory that may be different from system to system. The following symbolic
names are used below:

-   $DOWNLOAD_ROOT. The path to the directory containing the downloaded
    Realtime gauge-data extension.

-   $HTML_ROOT. The path to the directory where weeWX generated reports are
    saved. This directory is normally set in the [StdReport] section of
    weewx.conf. Refer to 'where to find things' in the weeWX User's Guide:
    http://weewx.com/docs/usersguide.htm#Where_to_find_things for further
    information.

-   $BIN_ROOT. The path to the directory where weeWX executables are located.
    This directory varies depending on weeWX installation method. Refer to
    'where to find things' in the weeWX User's Guide:
    http://weewx.com/docs/usersguide.htm#Where_to_find_things for further
    information.

-   $SKIN_ROOT. The path to the directory where weeWX skin folders are located.
    This directory is normally set in the [StdReport] section of
    weewx.conf. Refer to 'where to find things' in the weeWX User's Guide:
    http://weewx.com/docs/usersguide.htm#Where_to_find_things for further
    information.

1.  Download the latest Realtime gauge-data extension from the Realtime
gauge-data releases page (https://github.com/gjr80/weewx-realtime_gauge-data
/releases) into
a directory accessible from the weeWX machine.

    wget -P $DOWNLOAD_ROOT https://github.com/gjr80/weewx-realtime_gauge-data
/releases/download/v0.3.2/rtgd-0.3.2.tar.gz

	where $DOWNLOAD_ROOT is the path to the directory where the Realtime
    gauge-data extension is to be downloaded.

2.  Stop weeWX:

    sudo /etc/init.d/weewx stop

	or

    sudo service weewx stop

3.  Install the Realtime gauge-data extension downloaded at step 1 using the
wee_extension utility:

    wee_extension --install=$DOWNLOAD_ROOT/rtgd-0.3.2.tar.gz

    This will result in output similar to the following:

        Request to install '/var/tmp/rtgd-0.3.2.tar.gz'
        Extracting from tar archive /var/tmp/rtgd-0.3.2.tar.gz
        Saving installer file to /home/weewx/bin/user/installer/Rtgd
        Saved configuration dictionary. Backup copy at /home/weewx/weewx.conf.20161123124410
        Finished installing extension '/var/tmp/rtgd-0.3.2.tar.gz'

4. Start weeWX:

    sudo /etc/init.d/weewx start

	or

    sudo service weewx start

This will result in the gauge-data.txt file being generated on receipt of each
loop packet. A default installation will result in the generated gauge-data.txt
file being placed in the $HTML_ROOT directory. The Realtime gauge-data
extension installation can be further customized (eg file locations, frequency
of generation etc) by referring to the Realtime gauge-data extension wiki.

Manual installation

1.  Download the latest Realtime gauge-data extension from the Realtime
gauge-data releases page (https://github.com/gjr80/weewx-realtime_gauge-data
/releases) into
a directory accessible from the weeWX machine.

    wget -P $DOWNLOAD_ROOT https://github.com/gjr80/weewx-realtime_gauge-data
/releases/download/v0.3.2/rtgd-0.3.2.tar.gz

	where $DOWNLOAD_ROOT is the path to the directory where the Realtime
    gauge-data extension is to be downloaded.

2.  Unpack the extension as follows:

    tar xvfz rtgd-0.3.2.tar.gz

3.  Copy files from within the resulting folder as follows:

    cp rtgd/bin/user/rtgd.py $BIN_ROOT/user

	replacing the symbolic name $BIN_ROOT with the nominal locations for your
    installation.

4.  Edit weewx.conf:

    vi weewx.conf

5.  In weewx.conf, modify the [Engine] [[Services]] section by adding the
RealtimeGaugeData service to the list of process services to be run:

    [Engine]
        [[Services]]

            report_services = weewx.engine.StdPrint, weewx.engine.StdReport, user.rtgd.RealtimeGaugeData

6. Start weeWX:

    sudo /etc/init.d/weewx start

	or

    sudo service weewx start

This will result in the gauge-data.txt file being generated on receipt of each
loop packet. A default installation will result in the generated gauge-data.txt
file being placed in the $HTML_ROOT directory. The Realtime gauge-data
extension installation can be further customized (eg file locations, frequency
of generation etc) by referring to the Realtime gauge-data extension wiki.