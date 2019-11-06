/*
Copyright (c) 2019 Rafael Sánchez
This file is part of 'pe.audio.sys', a PC based personal audio system.

This is based on 'pre.di.c,' a preamp and digital crossover
https://github.com/rripio/pre.di.c
Copyright (C) 2018 Roberto Ripio
'pre.di.c' is based on 'FIRtro', a preamp and digital crossover
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

/*
   debug trick: console.log(something);
   NOTICE: remember do not leaving any console.log actives
*/

/* TO REVIEW: At some http request we use sync=false, this is not recommended
              but this way we get the answer.
              Maybe it is better to use onreadystatechange as per in refresh_system_status()
*/

/////////////   GLOBALS //////////////
var loud_measure    = 0.0;                  // Initialize, will be updated reading the loudness monitor file.
var ecasound_ecs = get_ecasound_ecs();      // The .ecs filename if ecasound is used
var auto_update_interval = 1500;            // Auto-update interval millisec
var advanced_controls = false;              // Default for showing advanced controls
var metablank = {
    'player':       '-',
    'time_pos':     '-:-',
    'time_tot':     '-:-',
    'bitrate':      '-',
    'artist':       '-',
    'album':        '-',
    'title':        '-',
    'track_num':    '-'
    }                                       // a player's metadata dictionary 
var last_loudspeaker = get_loudspeaker_name(); // If changed, then force a full page reload

// Returns the ecs file to be loaded with ecasound as per in '/config.yml'
function get_ecasound_ecs() {
    var config  = get_file('config');
    var lines   = config.split('\n');
    var result  = null
    var line    = ''
    for (i in lines) {
        line = lines[i];
        if ( line.trim().split(':')[0].trim() == '- ecasound_peq.py' ){
            result = line.trim().split(':')[1].trim().replace('.ecs','');
        }
    }
    return result
}

// Used from buttons to send commands to the control server
function control_cmd(cmd, update=true) {
    // Sends the command through by the server's PHP:
    // https://www.w3schools.com/js/js_ajax_http.asp
    var myREQ = new XMLHttpRequest();
    myREQ.open("GET", "php/functions.php?command=" +  cmd, true);
    myREQ.send();

    // Then update the web page
    if (update) {
        refresh_system_status();
    }
}

//////// TOGGLES ADVANCED CONTROLS ////////
function advanced_toggle() {
    if ( advanced_controls !== true ) {
        advanced_controls = true;
    }
    else {
        advanced_controls = false;
    }
    page_update(status);
}

//////// AUX SERVER FUNCTIONS ////////

// Monitor loudspeakers volume
function MON_vol(dB) {
    var myREQ = new XMLHttpRequest();
    myREQ.open("GET", "php/functions.php?command=mon_volume " + dB, async=true);
    myREQ.send();
}

// Switch the amplifier
function ampli(mode) {
    var myREQ = new XMLHttpRequest();
    myREQ.open("GET", "php/functions.php?command=amp_" + mode, async=true);
    myREQ.send();
}

// Queries the amplifier switch remote state
function update_ampli_switch() {
    var myREQ = new XMLHttpRequest();
    var amp_state = '';
    myREQ.open("GET", "php/functions.php?command=amp_state", async=false);
    myREQ.send();
    amp_state = myREQ.responseText.replace('\n','')
    document.getElementById("onoffSelector").value = amp_state;
}

// Changes a target
function set_target(value) {

    // avoids http socket lossing some symbols
    value = http_prepare( value );

    var myREQ = new XMLHttpRequest();
    myREQ.open("GET", "php/functions.php?command=set_target " + value, async=true);
    myREQ.send();
}

// Resets the loudness monitor daemon
function loudness_monitor_reset() {
    var myREQ = new XMLHttpRequest();
    myREQ.open("GET", "php/functions.php?command=loudness_monitor_reset", async=true);
    myREQ.send();
}

//////// USER MACROS ////////

// Gets a list of user macros availables
function list_macros() {
    var list  = [];
    var list2 = []; // a clean list version
    var myREQ = new XMLHttpRequest();
    myREQ.open("GET", "php/functions.php?command=list_macros", async=false);
    myREQ.send();
    list = JSON.parse( myREQ.responseText );
    // Remove '.' and '..' from the list ...
    if ( list.length > 2 ) {
        list = list.slice(2, );
        // ... and discard any disabled item, i.e. not named as 'N_xxxxx'
        for (i in list) {
            if ( isNumeric( list[i].split('_')[0] ) ) {
                list2.push( list[i] );
            }
        }
        return list2;
    }
    // if no elements, but '.' and '..', then returns an empty list
    else { return [];}
}

// Filling the user's macros buttons
function filling_macro_buttons() {
    var macros = list_macros();
    // If no macros on the list, do nothing, so leaving "display:none" on the buttons keypad div
    if ( macros.length < 1 ) { return; }
    // If any macro found, lets show the macros toggle switch
    document.getElementById( "playback_control_23").style.display = 'block';
    document.getElementById( "playback_control_21").style.display = 'block'; // just for symmetry reasons
    var macro = ''
    for (i in macros) {
        macro = macros[i];
        // Macro files are named this way: 'N_macro_name', so N will serve as button position
        macro_name = macro.slice(2, );
        macro_pos = macro.split('_')[0];
        document.getElementById( "macro_button_" + macro_pos ).innerText = macro_name;
    }
}

// Toggles displaying macro buttons
function macros_toggle() {
    var curMode = document.getElementById( "macro_buttons").style.display;
    if (curMode == 'none') {
        document.getElementById( "macro_buttons").style.display = 'inline-table'
    }
    else {
        document.getElementById( "macro_buttons").style.display = 'none'
    }
}

// Executes user defined macros
function user_macro(prefix, name) {
    var myREQ = new XMLHttpRequest();
    myREQ.open("GET", "php/functions.php?command=macro_" + prefix + "_" + name, async=true);
    myREQ.send();
}

//////// PLAYER CONTROL ////////

// Controls the player
function playerCtrl(action) {
    var myREQ = new XMLHttpRequest();
    myREQ.open("GET", "php/functions.php?command=player_" + action, async=true);
    myREQ.send();
}

// Updates the player control buttons, hightlights the corresponding button to the playback state
function update_player_controls() {
    var myREQ = new XMLHttpRequest();
    var playerState = '';
    myREQ.open("GET", "php/functions.php?command=player_state", async=false);
    myREQ.send();
    playerState = myREQ.responseText.replace('\n','')
    if        ( playerState == 'stop' ) {
        document.getElementById("buttonStop").style.background  = "rgb(185, 185, 185)";
        document.getElementById("buttonStop").style.color       = "white";
        document.getElementById("buttonPause").style.background = "rgb(100, 100, 100)";
        document.getElementById("buttonPause").style.color      = "lightgray";
        document.getElementById("buttonPlay").style.background  = "rgb(100, 100, 100)";
        document.getElementById("buttonPlay").style.color       = "lightgray";
    } else if ( playerState == 'pause' ){
        document.getElementById("buttonStop").style.background  = "rgb(100, 100, 100)";
        document.getElementById("buttonStop").style.color       = "lightgray";
        document.getElementById("buttonPause").style.background = "rgb(185, 185, 185)";
        document.getElementById("buttonPause").style.color      = "white";
        document.getElementById("buttonPlay").style.background  = "rgb(100, 100, 100)";
        document.getElementById("buttonPlay").style.color       = "lightgray";
    } else if ( playerState == 'play' ) {
        document.getElementById("buttonStop").style.background  = "rgb(100, 100, 100)";
        document.getElementById("buttonStop").style.color       = "lightgray";
        document.getElementById("buttonPause").style.background = "rgb(100, 100, 100)";
        document.getElementById("buttonPause").style.color      = "lightgray";
        document.getElementById("buttonPlay").style.background  = "rgb(185, 185, 185)";
        document.getElementById("buttonPlay").style.color       = "white";
    }
}

// Shows the playing info metadata
function update_player_info() {

    var myREQ = new XMLHttpRequest();
    var tmp = '';
    myREQ.open("GET", "php/functions.php?command=player_get_meta", async=false);
    myREQ.send();
    tmp = myREQ.responseText.replace('\n','');

    // players.py will allways give a dictionary as response, but if
    // no metadata are available then most fields will be empty, except 'player'
    if ( ! tmp.includes("failed")  &&
         ! tmp.includes("refused")    )  {

		d = JSON.parse( tmp );

        if ( d['artist'] == ''  && d['album'] == '' && d['title'] == '' ){
            d = metablank;
        }
        
        document.getElementById("bitrate").innerText    = d['bitrate'] + "\nkbps";
        document.getElementById("artist").innerText     = d['artist'];
        document.getElementById("track").innerText      = d['track_num'];
        document.getElementById("time").innerText       = d['time_pos'] + "\n" + d['time_tot'];
        document.getElementById("album").innerText      = d['album'];
        document.getElementById("title").innerText      = d['title'];
	}
}

//////// PAGE MANAGEMENT ////////

// Initializaes the page, then starts the auto-update
function page_initiate() {

    // Showing and filling the macro buttons
    filling_macro_buttons();

    // Filling the selectors: inputs, XO, DRC and PEQ
    fills_inputs_selector();
    fills_target_selector();
    fills_xo_selector();
    fills_drc_selector();
    if ( ecasound_ecs != null){
        document.getElementById("peq").style.color = "white";
        document.getElementById("peq").innerHTML = "PEQ: " + ecasound_ecs;
    }
    else {
        document.getElementById("peq").style.color = "grey";
        document.getElementById("peq").innerHTML = "(no peq)";
    }
    // Web header shows the loudspeaker name
    document.getElementById("main_lside").innerText = ':: pe.audio.sys :: ' + get_loudspeaker_name() + ' ::';

    // Amplifier switch status
    update_ampli_switch();

    // Queries the system status and updates the page
    refresh_system_status();
        
    // Waits 1 sec, then schedules the auto-update itself:
    // Notice: the function call inside setInterval uses NO brackets)
    setTimeout( setInterval( refresh_system_status, auto_update_interval ), 1000);
}

// Gets the system status and updates the page
function get_system_response(cmd) {
    // https://www.w3schools.com/js/js_ajax_http.asp

    var myREQ = new XMLHttpRequest();

    // waiting for HttpRequest has completed.
    myREQ.onreadystatechange = function() {
        if (this.readyState == 4 && this.status == 200) {
            return;
        }
    };

    // the http request:
    myREQ.open(method="GET", url="php/functions.php?command="+cmd, async=false);
    myREQ.send();
    return myREQ.responseText;
}

// Gets the system status and updates the page
function refresh_system_status() {
    var curr_loudspeaker = get_loudspeaker_name();
    if ( last_loudspeaker != curr_loudspeaker ){
        // Pausing some seconds because the service pasysctrl
        // will be restarter when changing the loudspaker set,
        // so socket errors can occur when queriyng info for update.
        setTimeout( dummy , 5000);
        last_loudspeaker = curr_loudspeaker;
        location.reload(forceGet=true);
        page_initiate();
    }
    page_update( get_system_response('status') );
}
function dummy(){
}

// Dumps system status into the web page
function page_update(status) {

    // Level, balance, tone info
    document.getElementById("levelInfo").innerHTML  =            status_decode(status, 'level');
    document.getElementById("balInfo").innerHTML    = 'BAL: '  + status_decode(status, 'balance');
    document.getElementById("bassInfo").innerText   = 'BASS: ' + status_decode(status, 'bass');
    document.getElementById("trebleInfo").innerText = 'TREB: ' + status_decode(status, 'treble');

    // the loudness reference to the slider and the loudness monitor to the meter 
    document.getElementById("loud_slider_container").innerText =
                                                     'Loud. Ref: '
                                                      + status_decode(status, 'loudness_ref');
    document.getElementById("loud_slider").value    = parseInt(status_decode(status, 'loudness_ref'));
    loud_measure = get_file('loudness_monitor').trim();
    document.getElementById("loud_meter").value    =  loud_measure;

    // The selected item on INPUTS, XO, DRC and PEQ
    document.getElementById("targetSelector").value =            status_decode(status, 'target');
    document.getElementById("inputsSelector").value =            status_decode(status, 'input');
    document.getElementById("xoSelector").value     =            status_decode(status, 'xo_set');
    document.getElementById("drcSelector").value    =            status_decode(status, 'drc_set');

    // MONO, LOUDNESS buttons text lower case if deactivated ( not used but leaving this code here)
    //document.getElementById("buttonMono").innerHTML = UpLow( 'mono', status_decode(status, 'mono') );
    //document.getElementById("buttonLoud").innerHTML = UpLow( 'loud', status_decode(status, 'loudness_track') );

    // Highlights activated buttons and related indicators
    if ( status_decode(status, 'muted') == 'true' ) {
        document.getElementById("buttonMute").style.background = "rgb(185, 185, 185)";
        document.getElementById("buttonMute").style.color = "white";
        document.getElementById("buttonMute").style.fontWeight = "bolder";
        document.getElementById("levelInfo").style.color = "rgb(150, 90, 90)";
    } else {
        document.getElementById("buttonMute").style.background = "rgb(100, 100, 100)";
        document.getElementById("buttonMute").style.color = "lightgray";
        document.getElementById("buttonMute").style.fontWeight = "normal";
        document.getElementById("levelInfo").style.color = "white";
    }
    if ( status_decode(status, 'midside') == 'mid' ) {
        document.getElementById("buttonMono").style.background = "rgb(100, 0, 0)";
        document.getElementById("buttonMono").style.color = "rgb(255, 200, 200)";
        document.getElementById("buttonMono").innerText = 'MO';
    } else if ( status_decode(status, 'midside') == 'side' ) {
        document.getElementById("buttonMono").style.background = "rgb(100, 0, 0)";
        document.getElementById("buttonMono").style.color = "rgb(255, 200, 200)";
        document.getElementById("buttonMono").innerText = 'L-R';
    } else {
        document.getElementById("buttonMono").style.background = "rgb(0, 90, 0)";
        document.getElementById("buttonMono").style.color = "white";
        document.getElementById("buttonMono").innerText = 'ST';
    }
    if ( status_decode(status, 'loudness_track') == 'true' ) {
        document.getElementById("buttonLoud").style.background = "rgb(0, 90, 0)";
        document.getElementById("buttonLoud").style.color = "white";
        document.getElementById("buttonLoud").innerText = 'LD';
        document.getElementById( "loudness_metering_and_slider").style.display = "block";
    } else {
        document.getElementById("buttonLoud").style.background = "rgb(100, 100, 100)";
        document.getElementById("buttonLoud").style.color = "rgb(150, 150, 150)";
        document.getElementById("buttonLoud").innerText = 'LD';
        // Hides loudness_metering_and_slider if loudness_track=False
        document.getElementById( "loudness_metering_and_slider").style.display = "none";
    }

    // Loudspeaker name (can change in some systems)
    document.getElementById("main_lside").innerText = ':: pe.audio.sys :: ' + get_loudspeaker_name() + ' ::';

    // Updates the amplifier switch
    update_ampli_switch()
    
    // Updates metadata player info
    update_player_info()

    // Highlights player controls when activated
    update_player_controls()
    
    // Displays the [url] button if input == 'iradio' or 'istreams'
    if (status_decode(status, 'input') == "iradio" ||
        status_decode(status, 'input') == "istreams") {
        document.getElementById( "url_button").style.display = "inline";
    }
    else {
        document.getElementById( "url_button").style.display = "none";
    }

    // Displays the track selector if input == 'cd'
    if (status_decode(status, 'input') == "cd") {
        document.getElementById( "track_selector").style.display = "inline";
    }
    else {
        document.getElementById( "track_selector").style.display = "none";
    }


    // Displays or hides the advanced controls section
    if ( advanced_controls == true ) {
        document.getElementById( "advanced_controls").style.display = "block";
        document.getElementById( "MON_vol_down").style.display = "inline-block";
        document.getElementById( "MON_vol_up").style.display = "inline-block";
        document.getElementById( "level_buttons13").style.display = "table-cell";
    }
    else {
        document.getElementById( "advanced_controls").style.display = "none";
        document.getElementById( "MON_vol_down").style.display = "none";
        document.getElementById( "MON_vol_up").style.display = "none";
        document.getElementById( "level_buttons13").style.display = "none";
    }
}

// Getting predefined files from server
function get_file(fid) {
    var phpCmd   = "";
    var response = "still_no_answer";
    if ( fid == 'config' ) {
        phpCmd = 'read_config_file';
    }
    else if ( fid == 'speaker' ) {
        phpCmd = 'read_speaker_file';
    }
    else if ( fid == 'loudness_monitor' ) {
        phpCmd = 'read_loudness_monitor_file';
    }
    else {
        return null;
    }
    var myREQ = new XMLHttpRequest();
    myREQ.open(method="GET", url="php/functions.php?command=" + phpCmd, async=false);
    myREQ.send();
    return (myREQ.responseText);
}

// Decodes the value from a system parameter inside the system status stream
function status_decode(status, prop) {
    var result = "";
    arr = status.split("\n"); // the tuples 'parameter:value' comes separated by line breaks
    for ( i in arr ) {
        if ( prop == arr[i].split(":")[0] ) {
            result = arr[i].split(":")[1]
        }
    }
    return String(result).trim();
}

// To upper-lower case button labels (OBSOLETE)
function UpLow(prop, truefalse) {
    var label = '';
    label = prop.toLowerCase()
    if ( truefalse == 'true' ) { label = prop.toUpperCase(); }
    return label;
}

// INPUTS selector
function fills_inputs_selector() {

    var inputs = [];

    // Reading "config.yml" and looking for sources definitions:
    var source_section = false;
    var clines = get_file('config').split('\n');
    var line = '';
    
    for ( i in clines) {
        line = clines[i];
        
        // continue if blank line
        if (line.length == 0){ continue; }
        
        if (line.substr(0,).trim() == 'sources:') {
            source_section = true;
        }
        if (source_section == true){
            
            if ( (line.substr(-1)  == ":"   )     && 
                 (line.substr(0,4) == "    ")     ) {
                inputs.push( line.trim().slice(0,-1) );
            }

            if ( (line.substr(0,1) != " ")              &&
                 (line.substr(0,).trim() != 'sources:') && 
                 (line.indexOf('#') < 0 )               ) {
                source_section = false;
            }
        }
    }

    // Filling the options in the inputs selector
    // https://www.w3schools.com/jsref/met_select_add.asp
    var x = document.getElementById("inputsSelector");
    for ( i in inputs) {
        var option = document.createElement("option");
        option.text = inputs[i];
        x.add(option);
    }    

    // And adds the input 'none' as intended into server_process that will disconnet all inputs
    var option = document.createElement("option");
    option.text = 'none';
    x.add(option);
    
}

// XO selector
function fills_xo_selector() {

    // getting the drcs from running core
    var xo_sets = get_system_response( 'get_xo_sets' ).split('\n');

    // filling the selector
    var x = document.getElementById("xoSelector");
    for ( i in xo_sets ) {
        var option = document.createElement("option");
        option.text = xo_sets[i];
        x.add(option);
    }
}

// DRC selector
function fills_drc_selector() {
    
    // getting the drcs from running core
    var drc_sets = get_system_response( 'get_drc_sets' ).split('\n');

    // filling the selector
    var x = document.getElementById("drcSelector");
    for ( i in drc_sets ) {
        var option = document.createElement("option");
        option.text = drc_sets[i];
        x.add(option);
    }

    // And adds 'none'
    var option = document.createElement("option");
    option.text = 'none';
    x.add(option);

}

// Inserts the PEQ selector if Ecasound is used
function insert_peq_selector(){

    // defines the selector
    var newSelector = document.createElement("select");
    newSelector.setAttribute("id", "peqSelector");
    newSelector.setAttribute("onchange", "control_cmd('peq ' + this.value, update=false)" );

    // Appends it
    var element = document.getElementById("span_peq");
    // label it with 'PEQ:' and restore font color from grey to white
    element.innerHTML = 'PEQ:';
    element.appendChild(newSelector);
    document.getElementById("peq").style.color = "white";
}

// PEQ selector
function fills_peq_selector() {
    var peq_sets = get_speaker_prop('PEQ');
    var x = document.getElementById("peqSelector");
    for ( i in peq_sets ) {
        var option = document.createElement("option");
        option.text = peq_sets[i];
        x.add(option);
    }
}

// Gets the current loudspeaker name
function get_loudspeaker_name() {
    var myREQ = new XMLHttpRequest();
    myREQ.open(method="GET", url="php/functions.php?command=get_loudspeaker_name", async=false);
    myREQ.send();
    return (myREQ.responseText);
}

// Gets the 'sets' defined into XO or DRC inside speaker.yml
function get_speaker_prop_sets(prop) {
    var prop_sets = [];
    var yaml = get_file('speaker');

    // custom YAML decoder
    var arr = yaml.split("\n");
    var dentroDeProp = false, dentroDeSets = false, indentOfSets = 0;
    for (i in arr) {
        linea = arr[i];
        if ( linea.trim().replace(' ','') == prop+':') { dentroDeProp = true; };
        if ( dentroDeProp ) {

            if ( linea.indexOf('sets:') != -1 ) {
                dentroDeSets = true;
                indentOfSets = indentLevel(linea);
                continue;
            }

            if ( dentroDeSets && indentLevel(linea) <= indentOfSets ){
                     break;
            }

            if ( dentroDeSets ) {
                setName = linea.split(':')[0].trim()
                prop_sets.push( setName );
            }
        }
    }
    return (prop_sets);
}

// Gets the options of some speaker property when not 'set' kind of, e.g. PEQ or target_xxs_curve
function get_speaker_prop(prop) {
    var opcs = [];
    var yaml = get_file('speaker');

    // custom YAML decoder
    var arr = yaml.split("\n");
    var dentroDeProp = false;
    for (i in arr) {
        linea = arr[i];
        if ( linea.slice(0, (prop.length)+1 ) == prop+':') { dentroDeProp = true; };
        if ( dentroDeProp ) {

            tmp = linea.replace( prop + ':', '' );
            tmp = tmp.replace('{', '').replace('}', '');
            fields = tmp.split(',');
            for (i in fields) {
                f = fields[i];
                opc = f.split(':')[0].trim()
                opcs.push( opc );
            }

            if ( indentLevel(linea) <= 1 ){ break; }
        }
    }
    return (opcs);
}

// Aux function that retrieves the indentation level of some code line, useful for YAML decoding.
function indentLevel(linea) {
    var level = 0;
    for ( i in linea ) {
        if ( linea[i] != ' ' ) { break;}
        level += 1;
    }
    return (level);
}

// Auxiliary to check for "numeric" strings
function isNumeric(num){
  return !isNaN(num)
}

// Sends an url to the server, to be played back
function play_url() {
    var url = prompt('Enter url to play:');
    if ( url.slice(0,5) == 'http:' || url.slice(0,6) == 'https:' ) {
        var myREQ = new XMLHttpRequest();
        myREQ.open("GET", "php/functions.php?command=" + url, async=true);
        myREQ.send();
    }
}

// Select a disk track
function select_track() {
    var tracknum = prompt('Enter track number to play:');
    if ( true ) {
        var myREQ = new XMLHttpRequest();
        myREQ.open("GET", "php/functions.php?command=player_play_track_" + tracknum, async=true);
        myREQ.send();
    }
}


// TARGETS: Reads the meaningful chunk of the target_mag_curve name of the running loudspeaker
//          (i) Function CURRENTLY NOT USED
function displays_target_curve() {
    var tmp = get_speaker_prop('target_mag_curve');
    tmp = tmp[0].replace('.dat', '').replace('target_mag_', '');
    document.getElementById("target").innerText = 'targEQ: ' + tmp
}

// TARGETS selector
function fills_target_selector() {
    target_files = get_system_response( 'get_target_sets' ).split('\n');
    var x = document.getElementById("targetSelector");
    for ( i in target_files ) {
        var option = document.createElement("option");
        option.text = target_files[i];
        x.add(option);
    }
}

// Auxiliary function to avoid http socket lossing some symbols
function http_prepare(x) {
    x = x.replace(' ', '%20')
    x = x.replace('!', '%21')
    x = x.replace('"', '%22')
    x = x.replace('#', '%23')
    x = x.replace('$', '%24')
    x = x.replace('%', '%25')
    x = x.replace('&', '%26')
    x = x.replace("'", '%27')
    x = x.replace('(', '%28')
    x = x.replace(')', '%29')
    x = x.replace('*', '%2A')
    x = x.replace('+', '%2B')
    x = x.replace(',', '%2C')
    x = x.replace('-', '%2D')
    x = x.replace('.', '%2E')
    x = x.replace('/', '%2F')
    return x;
}

// Processing the LOUDNESS_REF slider
function loudness_ref_change(slider_value) {
    loudness_ref = parseInt(slider_value);
    control_cmd('loudness_ref ' + loudness_ref, update=false);
}

// JUST TO TEST
function TESTING() {
    var myREQ = new XMLHttpRequest();
    myREQ.open("GET", "php/functions.php?command=status", async=true);
    myREQ.send();
    console.log( 'respuesta de php:' , myREQ.responseText );
}
