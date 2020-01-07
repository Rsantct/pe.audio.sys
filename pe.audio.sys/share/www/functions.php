<?php

    /*
    Copyright (c) 2019 Rafael Sánchez
    This file is part of 'pe.audio.sys', a PC based personal audio system.

    This code is based on @amr web code on 'FIRtro'
    https://github.com/AudioHumLab/FIRtro
    Copyright (c) 2006-2011 Roberto Ripio
    Copyright (c) 2011-2016 Alberto Miguélez
    Copyright (c) 2016-2018 Rafael Sánchez

    'pe.audio.sys' is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    'pe.audio.sys' is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with 'pe.audio.sys'.  If not, see <https://www.gnu.org/licenses/>.
    */

    /*  This is the hidden server side php code.
        PHP will response to the client via the standard php output, for instance:
            echo $some_varible;
            echo "some_string";
            readfile("some_file_path");
    */

    $UHOME = get_home();
    //echo '---'.$HOME.'---'; // cmdline debugging

    // Gets the base folder where php code and pe.audio.sys are located
    function get_home() {
        $phpdir = getcwd();
        $pos = strpos($phpdir, 'pe.audio.sys');
        return substr($phpdir, 0, $pos-1 );
    }

    // Gets single line configured items from pe.audio.sys 'config.yml' file
    function get_config($item) {
        // to have access to variables from outside
        global $UHOME;

        $tmp = "";
        $cfile = fopen( $UHOME."/pe.audio.sys/config.yml", "r" )
                  or die("Unable to open file!");
        while( !feof($cfile) ) {
            $line = fgets($cfile);
            // Ignore yaml commented out lines
            if ( strpos($line, '#') === false ) {
                if ( strpos( $line, $item) !== false ) {
                    $tmp = str_replace( "\n", "", $line);
                    $tmp = str_replace( $item, "", $tmp);
                    $tmp = str_replace( ":", "", $tmp);
                    $tmp = trim($tmp);
                }
            }
        }
        fclose($cfile);
        return $tmp;
    }


    // Communicates to the pe.audio.sys TCP/IP servers.
    // Notice: server address and port are specified
    //         into 'config.yml' for each service,
    //         for instance 'control', 'players' or 'aux'.
    function system_socket ($service, $cmd) {

        $address =         get_config( $service."_address" );
        $port    = intval( get_config( $service."_port" ) );

        // Creates a TCP socket
        $socket = socket_create(AF_INET, SOCK_STREAM, SOL_TCP);
        if ($socket === false) {
            echo "socket_create() failed: " . socket_strerror(socket_last_error()) . "\n";
        }
        $result = socket_connect($socket, $address, $port);
        if ($result === false) {
            echo "socket_connect() failed: ($result) " . socket_strerror(socket_last_error($socket)) . "\n";
        }
        // Sends and receive:
        socket_write($socket, $cmd, strlen($cmd));
        //
        // (!) read ENOUGH BYTES e.g. 1024 to avoid large responses to be truncated.
        //
        $out = socket_read($socket, 1024);
        //  (i) sending quit and empty the buffer currently not in use, just close:
        //socket_write($socket, "quit", strlen("quit"));
        //socket_read($socket, 1024);   // empties the receiving buffer
        socket_close($socket);
        return $out;
    }

    ///////////////////////////   MAIN: ///////////////////////////////
    // listen to http request then returns results via standard output

    /*  http://php.net/manual/en/reserved.variables.request.php
        PHP server side receives associative arrays, i.e. dictionaries, through by the
        GET o PUT methods from the client side XMLHttpRequest (usually javascript).
        The array is what appears after 'functions.php?.......', examples:
        
            "GET", "functions.php?command=level -15"
            "GET", "functions.php?command=aux amp_switch on"
            "GET", "functions.php?command=players player_stop"
    */

    // echo system_socket('control', 'status'); // DEBUG

    $command = $_REQUEST["command"];

    if     ( substr( $command, 0, 4 ) === "aux " ) {
        echo system_socket( 'aux', substr( $command, 4,  ) );
    }
    elseif ( substr( $command, 0, 8 ) === "players " ) {
        echo system_socket( 'players', substr( $command, 8,  ) );
    }
    else {
        echo system_socket( 'pasysctrl', $command );
    }

?>
