<?php

    /*
    Copyright (c) Rafael Sánchez
    This file is part of 'pe.audio.sys'
    'pe.audio.sys', a PC based personal audio system.
    */

    $UHOME = get_home();
    // echo "UHOME: ".$UHOME."\n"; // cmdline debugging

    // Gets the base folder where php code and pe.audio.sys are located
    function get_home() {
        $phpdir = getcwd();
        $pos = strpos($phpdir, 'pe.audio.sys');
        $uhome= substr($phpdir, 0, $pos-1);
        return $uhome;
    }

    // Gets single line configured items from the 'wolservice.cfg' YAML file
    function get_config($item) {
        // to have access to variables from outside
        global $UHOME;

        $tmp = "";
        $cfile = fopen( $UHOME."/pe.audio.sys/share/scripts/wolservice/wolservice.cfg", "r" )
                  or die("Unable to open file!");
        while( !feof($cfile) ) {
            $line = fgets($cfile);
            // Ignore yaml commented out lines
            if ( strpos($line, '#') === false ) {
                if ( strpos( $line, $item) !== false ) {
                    $tmp = str_replace( "\n", "", $line);   # remove \n
                    $tmp = str_replace( $item, "", $tmp);   # remove item itself
                    $tmp = str_replace( ":", "", $tmp);     # remove : separator
                    $tmp = str_replace( "\"", "", $tmp);    # remove quotes
                    $tmp = str_replace( "'", "", $tmp);
                    $tmp = trim($tmp);
                }
            }
        }
        fclose($cfile);
        return $tmp;
    }


    // Communicates to the pe.audio.sys TCP server.
    function system_socket ($cmd) {

        $address =         get_config( "server_addr" );
        $port    = intval( get_config( "server_port" ) );

        // Creates a TCP socket
        $socket = socket_create(AF_INET, SOCK_STREAM, SOL_TCP);
        if ($socket === false) {
            echo "socket_create() failed: " . socket_strerror(socket_last_error()) . "\n";
            return '';
        }

        socket_set_option($socket, SOL_SOCKET, SO_RCVTIMEO, array("sec"=>0, "usec"=>500));
        socket_set_option($socket, SOL_SOCKET, SO_SNDTIMEO, array("sec"=>0, "usec"=>500));

        $so_result = socket_connect($socket, $address, $port);
        if ($so_result === false) {
            echo "(comms.php) socket_connect() failed: ($so_result) " . socket_strerror(socket_last_error($socket)) . "\n";
            return '';
        }

        // PHP ---> App server side
        socket_write($socket, $cmd, strlen($cmd));

        // App server side ---> PHP
        $ans = '';
        while ( ($tmp = socket_read($socket, 1000)) !== '') {
           $ans = $ans.$tmp;
        }
        socket_close($socket);

        return $ans;
    }

?>
