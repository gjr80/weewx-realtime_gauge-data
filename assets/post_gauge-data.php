<?php
/*
post_gauge-data.php

Accept a JSON string via HTTP POST and then save the string to file.

Copyright (C) 2017-22 Gary Roderick                 gjroderick<at>gmail.com

This program is free software: you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free Software
Foundation, either version 3 of the License, or (at your option) any later
version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY
WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
PARTICULAR PURPOSE.  See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with
this program.  If not, see http://www.gnu.org/licenses/.

Version: 0.2.0                                          Date: 22 September 2022

Revision History
    22 September 2022   v0.2.0
        - refactored the script based upon the weewx-saratoga equivalent script
          for clientraw.txt
        - the only response now sent is a HTTP response code only, 'success'
          text is no longer sent
        - added explicit return codes for the following results:
            200 - OK for proper operation
            400 - Bad Request for malformed POST request (received data is not 
                  valid JSON)
            405 - Method Not Allowed for GET or HEAD requests
            507 - Insufficient Storage if writing gauge-data.txt to disk fails
    23 March 2017       v0.1.0
        - initial release

Instructions for use:

1.  Copy this file to an appropriate directory in the web server document tree

2.  Change $json_file variable if required. Absolute paths with be relative to
    the web server document root, relative paths will be relative to the
    location of this file. The file name can be changed as well but should be
    left as gauge-data.txt if using the received file with the SteelSeries 
    Weather Gauges.

Troubleshooting:

1.  If the script is unable to write gauge-data.txt to file check that www-data 
    has write permission to the directory concerned.

2.  If gauge-data.txt does not appear where it intended check the $json_file
    setting, paying particular attention to absolute/relative paths and
    permissions (refer point 1 above). Point 3 below may also help.

3.  If the script does not perform as expected check the web server logs (both
    access and error) for clues.
*/

// define our destination path and file name, relative paths are relative to 
// the location of this file
$json_file = "./gauge-data.txt";

// define a function to determine if a string decodes to valid JSON
function isValidJSON($str) {
    json_decode($str);
    return json_last_error() == JSON_ERROR_NONE;
}

// we are only interested in HTTP POST
if($_SERVER['REQUEST_METHOD'] == 'POST') {
    // we have a HTTP POST so get the data
    $data = file_get_contents("php://input");
    // If the received data is valid JSON, try to save it and return a suitable
    // response. Otherwise do nothing, this will trigger a 400 response code
    // later.
    if (strlen($data) > 0 && isValidJSON($data)) {
        // the data is a valid JSON format string, all we need do is write the
        // data string to file
        $flag = file_put_contents($json_file, $data);
        // file_put_contents() returns the number of bytes written to file or
        // false on failure
        if($flag !== false) {
            // our data was saved successfully so terminate the script sending
            // a 200 response code
            header('HTTP/1.0 200 OK');
            exit('<h1>200 OK</h1>');
        } else {
            // we couldn't save the data, so terminate the script sending a 507
            // response code
            header('HTTP/1.0 507 Insufficient Storage');
            exit('<h1>507 Insufficient Storage</h1>');
        }
    }
} else { 
    // GET or HEAD requests are rejected, terminate the script and send a 405
    // response code
    header('HTTP/1.0 405 Method Not Allowed');
    exit('<h1>405 Method Not Allowed</h1>');  
}
// oops.. malformed POST request.. let'em know with a 400 response code
header('HTTP/1.0 400 Bad Request');
exit('<h1>400 Bad Request</h1>');  
?>
