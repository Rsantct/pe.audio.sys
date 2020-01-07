/*
    Copyright (c) 2019 Rafael Sánchez
    This file is part of 'pe.audio.sys', a PC based preamplifier.

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

/* TO REVIEW:
    We use http request GET with async=false, this is not recommended
    but this way we get the answer.
s*/

// -----------------------------------------------------------------------------
// ------------------------------- CONFIG: -------------------------------------
// -----------------------------------------------------------------------------
//
//  (i) Set URL_PREFIX ='/' if you use the provided peasys_node.js server script,
//      or set it '/functions.php' if you use Apache+PHP at server side.
//
const URL_PREFIX = '/functions.php';
const AUTO_UPDATE_INTERVAL = 1000;      // Auto-update interval millisec
// -----------------------------------------------------------------------------


// Some globals
var advanced_controls = false;          // Default for displaying advanced controls
var ecasound_ecs = get_ecasound_ecs();  // The .ecs filename if ecasound is used
var metablank = {
    'player':       '-',
    'time_pos':     '-:-',
    'time_tot':     '-:-',
    'bitrate':      '-',
    'artist':       '-',
    'album':        '-',
    'title':        '-',
    'track_num':    '-'
    }                                   // a player's metadata blank dict

// Returns the ecs file to be loaded with ecasound as per in 'config.yml' (if so)
function get_ecasound_ecs() {
    return JSON.parse( control_cmd( 'aux get_ecasound_ecs' ) );
}

// Talks to the pe.audio.sys node.js HTTP SERVER
function control_cmd( cmd ) {

    // avoids http socket lossing some symbols
    cmd = http_prepare(cmd);

    const myREQ = new XMLHttpRequest();

    // a handler that waits for HttpRequest has completed.
    myREQ.onreadystatechange = function() {
        if (this.readyState == 4 && this.status == 200) {
            return;
        }
    };

    myREQ.open(method="GET", url = URL_PREFIX + "?command=" + cmd, async=false);
    myREQ.send();
    //console.log('httpTX: ' + cmd);

    ans = myREQ.responseText;
    //console.log('httpRX: ' + ans);

    return ans;
}

function page_initiate(){

    // Macros buttons (!) place this first because
    // aux server is supposed to be always alive
    fill_in_macro_buttons();

    // Web header
    document.getElementById("main_lside").innerText = ':: pe.audio.sys :: ' +
                                JSON.parse( control_cmd('aux get_loudspeaker') );

    // Filling in the selectors: inputs, target, XO, DRC and PEQ
    fill_in_inputs_selector();
    fill_in_target_selector();
    fill_in_xo_selector();
    fill_in_drc_selector();
    if ( ecasound_ecs != ''){
        document.getElementById("peq").style.color = "white";
        document.getElementById("peq").innerHTML = "PEQ: " +
                                                ecasound_ecs.replace('.ecs','');
    }
    else {
        document.getElementById("peq").style.color = "grey";
        document.getElementById("peq").innerHTML = "(no peq)";
    }

    // Schedules the page_update (only runtime variable items):
    // Notice: the function call inside setInterval uses NO brackets)
    setInterval( page_update, AUTO_UPDATE_INTERVAL );

}

// Queries the system status and updates the page (only runtime variable items):
function page_update() {

    // Amplifier switching
    update_ampli_switch();

    const status = JSON.parse( control_cmd('get_state') );

    // The selected item on INPUTS
    document.getElementById("inputsSelector").value = status['input'];

    // Level, balance, tone info
    document.getElementById("levelInfo").innerHTML  = status['level'].toFixed(1);
    document.getElementById("balInfo").innerHTML    = 'BAL: '  + status['balance'];
    document.getElementById("bassInfo").innerText   = 'BASS: ' + status['bass'];
    document.getElementById("trebleInfo").innerText = 'TREB: ' + status['treble'];

    // the loudness reference to the slider and the loudness monitor to the meter
    document.getElementById("loud_slider_container").innerText =
                    'Loud. Ref: ' + status['loudness_ref'];
    document.getElementById("loud_slider").value    =
                    parseInt(status['loudness_ref']);
    const loud_measure = JSON.parse( control_cmd('aux get_loudness_monitor') );
    document.getElementById("loud_meter").value    =  loud_measure;

    // The selected item on INPUTS, XO, DRC and PEQ
    document.getElementById("targetSelector").value = status['target'];
    document.getElementById("inputsSelector").value = status['input'];
    document.getElementById("xoSelector").value     = status['xo_set'];
    document.getElementById("drcSelector").value    = status['drc_set'];

    // Highlights activated buttons and related indicators
    if ( status['muted'] == true ) {
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
    if ( status['midside'] == 'mid' ) {
        document.getElementById("buttonMono").style.background = "rgb(100, 0, 0)";
        document.getElementById("buttonMono").style.color = "rgb(255, 200, 200)";
        document.getElementById("buttonMono").innerText = 'MO';
    } else if ( status['midside'] == 'side' ) {
        document.getElementById("buttonMono").style.background = "rgb(100, 0, 0)";
        document.getElementById("buttonMono").style.color = "rgb(255, 200, 200)";
        document.getElementById("buttonMono").innerText = 'L-R';
    } else {
        document.getElementById("buttonMono").style.background = "rgb(0, 90, 0)";
        document.getElementById("buttonMono").style.color = "white";
        document.getElementById("buttonMono").innerText = 'ST';
    }
    if ( status['loudness_track'] == true ) {
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

    // Displays or hides the advanced controls section
    if ( advanced_controls == true ) {
        document.getElementById( "advanced_controls").style.display = "block";
        document.getElementById( "level_buttons13").style.display = "table-cell";
    }
    else {
        document.getElementById( "advanced_controls").style.display = "none";
        document.getElementById( "level_buttons13").style.display = "none";
    }

    // Updates metadata player info
    update_player_info()
    // Highlights player controls when activated
    update_player_controls()

}

// INPUTS selector
function fill_in_inputs_selector() {

    // getting the inputs list from running core
    const inputs = JSON.parse( control_cmd( 'get_inputs' ) );
    //console.log( typeof inputs, inputs );

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
function fill_in_xo_selector() {
    const xo_sets = JSON.parse( control_cmd( 'get_xo_sets' ) );
    var x = document.getElementById("xoSelector");
    for ( i in xo_sets ) {
        var option = document.createElement("option");
        option.text = xo_sets[i];
        x.add(option);
    }
}

// DRC selector
function fill_in_drc_selector() {
    const drc_sets = JSON.parse( control_cmd( 'get_drc_sets' ) );
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

// TARGETS selector
function fill_in_target_selector() {
    const target_files = JSON.parse( control_cmd( 'get_target_sets' ) );
    var x = document.getElementById("targetSelector");
    for ( i in target_files ) {
        var option = document.createElement("option");
        option.text = target_files[i];
        x.add(option);
    }
}
// Changes a target
function set_target(value) {
    control_cmd( 'set_target ' + value );
}

//////// PLAYER CONTROL ////////
// Controls the player
function playerCtrl(action) {
    control_cmd( 'players player_' + action );
}
// Updates the player control buttons, hightlights the corresponding button to the playback state
function update_player_controls() {
    const playerState = control_cmd( 'players player_state' );
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

    const tmp = control_cmd( 'players player_get_meta' );

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

//////// USER MACROS ////////
// Filling the user's macros buttons
function fill_in_macro_buttons() {
    const macros = JSON.parse( control_cmd( 'aux get_macros' ).split(',') );
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
    control_cmd( 'aux run_macro ' + prefix + '_' + name );
}

//////// AUX SERVER FUNCTIONS ////////
// Switch the amplifier
function ampli(mode) {
    control_cmd( 'aux amp_switch ' + mode );
}
// Queries the remote amplifier switch state
function update_ampli_switch() {
    const amp_state = JSON.parse( control_cmd( 'aux amp_switch state' )
                                  .replace('\n','') );
    document.getElementById("onoffSelector").value = amp_state;
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

// Processing the LOUDNESS_REF slider
function loudness_ref_change(slider_value) {
    loudness_ref = parseInt(slider_value);
    control_cmd('loudness_ref ' + loudness_ref, update=false);
}

// Auxiliary function to avoid http socket lossing some symbols
function http_prepare(x) {
    //x = x.replace(' ', '%20');  // leaving spaces as they are
    x = x.replace('!', '%21');
    x = x.replace('"', '%22');
    x = x.replace('#', '%23');
    x = x.replace('$', '%24');
    x = x.replace('%', '%25');
    x = x.replace('&', '%26');
    x = x.replace("'", '%27');
    x = x.replace('(', '%28');
    x = x.replace(')', '%29');
    x = x.replace('*', '%2A');
    x = x.replace('+', '%2B');
    x = x.replace(',', '%2C');
    x = x.replace('-', '%2D');
    x = x.replace('.', '%2E');
    x = x.replace('/', '%2F');
    return x;
}

// Aux to test buttons
function TESTING1(){
    //do something
}
function TESTING2(){
    //do something
}


