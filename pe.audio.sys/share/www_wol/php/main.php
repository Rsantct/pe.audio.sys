<?php

    /*
    Copyright (c) Rafael Sánchez
    This file is part of 'pe.audio.sys'
    'pe.audio.sys', a PC based personal audio system.
    */

    include 'comms.php';

    $command = $_REQUEST["command"];
    echo system_socket( $command );

?>
