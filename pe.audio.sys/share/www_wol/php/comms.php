<?php

    /*
    Copyright (c) Rafael Sánchez
    This file is part of 'pe.audio.sys'
    'pe.audio.sys', a PC based personal audio system.
    */

    $UHOME = get_home();
    //echo '---'.$HOME.'---'; // cmdline debugging

    // Gets the base folder where php code and pe.audio.sys are located
    function get_home() {
        $phpdir = getcwd();
        $pos = strpos($phpdir, 'pe.audio.sys');
        return substr($phpdir, 0, $pos-1 );
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

?>