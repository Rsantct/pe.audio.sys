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
   (i) debug trick: console.log(something);
       NOTICE: remember do not leaving any console.log active

   (i) Cannot reference document.getElementbyxxxx until started page_initiate()
*/

/* PENDING:
    We use http request GET with async=false, this is deprecated and
    not recommended but this way we get the answer from the server side.
*/

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
var state = {loudspeaker:"not connected"};
var advanced_controls = false;          // Default for displaying advanced controls
var metablank = {                       // A player's metadata blank dict
    'player':       '-',
    'time_pos':     '-:-',
    'time_tot':     '-:-',
    'bitrate':      '-',
    'artist':       '-',
    'album':        '-',
    'title':        '-',
    'track_num':    '-'
    }
var last_loudspeaker = ''               // Will detect if audio processes has beeen
                                        // restarted with new loudspeaker configuration.

try{
    var web_config = JSON.parse( control_cmd('aux get_web_config') );
}catch{
    var web_config = { 'at_startup':{'hide_macro_buttons':false} };
    web_config.reboot_button_action = 'peaudiosys_restart.sh';
}

// Talks to the pe.audio.sys HTTP SERVER
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
    // Show or hide the macro buttons
    const hide_mbuttons = web_config.at_startup.hide_macro_buttons;
    if ( hide_mbuttons ){
        document.getElementById("macro_buttons").style.display = 'none';
    }else{
        document.getElementById("macro_buttons").style.display = 'inline-table';
    }
    // Updates the title of the reboot button as per the web_config dict
    document.getElementById("reboot_switch").title = 'RESTART: ' +
                                                web_config.reboot_button_action;
    // Schedules the page_update (only runtime variable items):
    // Notice: the function call inside setInterval uses NO brackets)
    setInterval( page_update, AUTO_UPDATE_INTERVAL );
}

function fill_in_page_header_and_selectors(){

    // Web header
    document.getElementById("main_cside").innerText = ':: pe.audio.sys :: ' +
                                                       state.loudspeaker;

    // Filling in the selectors: inputs, target, XO, DRC and PEQ
    fill_in_inputs_selector();
    fill_in_target_selector();
    fill_in_xo_selector();
    fill_in_drc_selector();
    if ( state.peq_set != 'none'){
        document.getElementById("peq").style.color = "white";
        document.getElementById("peq").innerHTML = "PEQ: " + state.peq_set;
    }
    else {
        document.getElementById("peq").style.color = "grey";
        document.getElementById("peq").innerHTML = "(no peq)";
    }
}

// Queries the system state and updates the page (only runtime variable items):
function page_update() {

    // Amplifier switching (aux service always runs)
    update_ampli_switch();

    try{
        state = JSON.parse( control_cmd('get_state') );
    }catch{
        state = {loudspeaker:'not connected'};
    }

    // Displays or hides the advanced controls section
    if ( advanced_controls == true ) {
        document.getElementById( "advanced_controls").style.display = "block";
        document.getElementById( "level_buttons13").style.display = "table-cell";
        document.getElementById( "main_lside").style.display = "table-cell";
    }
    else {
        document.getElementById( "advanced_controls").style.display = "none";
        document.getElementById( "level_buttons13").style.display = "none";
        document.getElementById( "main_lside").style.display = "none";
    }

    // Refresh some stuff if loudspeaker's audio processes has changed
    if ( last_loudspeaker != state.loudspeaker ){
        fill_in_page_header_and_selectors();
        last_loudspeaker = state.loudspeaker;
    }

    if (state.loudspeaker == 'not connected'){
        document.getElementById("levelInfo").innerHTML  = '--';
        return;
    }

    if (state.convolver_runs == false){
        document.getElementById("levelInfo").innerHTML  = '--';
        document.getElementById("main_cside").innerText = ':: pe.audio.sys :: ' +
                                                          'convolver-OFF';
        return;
    }
    else{
        document.getElementById("main_cside").innerText = ':: pe.audio.sys :: ' +
                                                       state.loudspeaker;
    }

    // The selected item on INPUTS
    document.getElementById("inputsSelector").value = state.input;

    // Level balance, tone info
    document.getElementById("levelInfo").innerHTML  = state.level.toFixed(1);
    document.getElementById("balInfo").innerHTML    = 'BAL: '  + state.balance;
    document.getElementById("bassInfo").innerText   = 'BASS: ' + state.bass;
    document.getElementById("trebleInfo").innerText = 'TREB: ' + state.treble;

    // the loudness reference to the slider and the loudness monitor to the meter
    document.getElementById("loud_slider_container").innerText =
                    'Loud. Ref: ' + state.loudness_ref;
    document.getElementById("loud_slider").value    = state.loudness_ref;
    try{
        const loud_measure = JSON.parse( control_cmd('aux get_loudness_monitor') );
        document.getElementById("loud_meter").value    =  loud_measure;
    }catch{
    }

    // The selected item on INPUTS, XO, DRC and PEQ
    document.getElementById("targetSelector").value = state.target;
    document.getElementById("inputsSelector").value = state.input;
    document.getElementById("xoSelector").value     = state.xo_set;
    document.getElementById("drcSelector").value    = state.drc_set;

    // Highlights activated buttons and related indicators
    buttonMuteHighlight()
    buttonMonoHighlight()
    buttonLoudHighlight()

    // Updates metadata player info
    update_player_info()
    // Highlights player controls when activated
    update_player_controls()

    // Displays the track selector if input == 'cd'
    if ( state.input == "cd") {
        document.getElementById( "track_selector").style.display = "inline";
    }
    else {
        document.getElementById( "track_selector").style.display = "none";
    }

    // Displays the [url] button if input == 'iradio' or 'istreams'
    if (state.input == "iradio" ||
        state.input == "istreams") {
        document.getElementById( "url_button").style.display = "inline";
    }
    else {
        document.getElementById( "url_button").style.display = "none";
    }

}

// INPUTS selector
function fill_in_inputs_selector() {

    try{
        var inputs = JSON.parse( control_cmd( 'get_inputs' ) );
    }catch{
        return;
    }

    // Filling the options in the inputs selector
    // https://www.w3schools.com/jsref/dom_obj_select.asp
    select_clear_options(ElementId="inputsSelector");
    const mySel = document.getElementById("inputsSelector");
    for ( i in inputs) {
        var option = document.createElement("option");
        option.text = inputs[i];
        mySel.add(option);
    }

    // And adds the input 'none' as expected in server_process that will disconnet all inputs
    var option = document.createElement("option");
    option.text = 'none';
    mySel.add(option);

}

// XO selector
function fill_in_xo_selector() {
    try{
        var xo_sets = JSON.parse( control_cmd( 'get_xo_sets' ) );
    }catch{
        return;
    }
    select_clear_options(ElementId="xoSelector");
    const mySel = document.getElementById("xoSelector");
    for ( i in xo_sets ) {
        var option = document.createElement("option");
        option.text = xo_sets[i];
        mySel.add(option);
    }
}

// DRC selector
function fill_in_drc_selector() {
    try{
        var drc_sets = JSON.parse( control_cmd( 'get_drc_sets' ) );
    }catch{
        return;
    }
    select_clear_options(ElementId="drcSelector");
    const mySel = document.getElementById("drcSelector");
    for ( i in drc_sets ) {
        var option = document.createElement("option");
        option.text = drc_sets[i];
        mySel.add(option);
    }
    // And adds 'none'
    var option = document.createElement("option");
    option.text = 'none';
    mySel.add(option);
}

// TARGETS selector
function fill_in_target_selector() {
    try{
        var target_files = JSON.parse( control_cmd( 'get_target_sets' ) );
    }catch{
        return;
    }
    select_clear_options(ElementId="targetSelector");
    const mySel = document.getElementById("targetSelector");
    for ( i in target_files ) {
        var option = document.createElement("option");
        option.text = target_files[i];
        mySel.add(option);
    }
}
// Changes a target
function set_target(value) {
    control_cmd( 'set_target ' + value );
}

// Processing the LOUDNESS_REF slider
function loudness_ref_change(slider_value) {
    loudness_ref = parseInt(slider_value);
    control_cmd('loudness_ref ' + loudness_ref, update=false);
}

//////// PLAYER SERVER FUNCTIONS ////////
// Controls the player
function playerCtrl(action) {
    control_cmd( 'players player_' + action );
}
// Updates the player control buttons, hightlights the corresponding button to the playback state
function update_player_controls() {
    try{
        var playerState = control_cmd( 'players player_state' );
    }catch{
        return;
    }
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
    try{
        var tmp = control_cmd( 'players player_get_meta' );
    }catch{
        return;
    }
    // players.py will allways give a dictionary as response, but if
    // no metadata are available then most fields will be empty, except 'player'
    if ( ! tmp.includes("failed")  &&
         ! tmp.includes("refused")    )  {

        try{
            var d = JSON.parse( tmp );
        }catch{
            var d = metablank;
        }

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
// Emerge a dialog to select a disk track to be played
function select_track() {
    var tracknum = prompt('Enter track number to play:');
    if ( true ) {
        control_cmd( 'players player_play_track_' + tracknum );
    }
}
// Sends an url to the server, to be played back
function play_url() {
    var url = prompt('Enter url to play:');
    if ( url.slice(0,5) == 'http:' || url.slice(0,6) == 'https:' ) {
        control_cmd( 'players ' + url );
    }
}

//////// AUX SERVER FUNCTIONS ////////
// Switch the amplifier
function ampli(mode) {
    control_cmd( 'aux amp_switch ' + mode );
}
// Queries the remote amplifier switch state
function update_ampli_switch() {
    try{
        const amp_state = JSON.parse( control_cmd( 'aux amp_switch state' )
                                      .replace('\n','') );
        document.getElementById("onoffSelector").value = amp_state;
    }catch{
    document.getElementById("onoffSelector").value = '--';
    }
}
// Filling in the user's macro buttons
function fill_in_macro_buttons() {
    try{
        var macros = JSON.parse( control_cmd( 'aux get_macros' ).split(',') );
    }catch{
    // If no macros list, do nothing, so leaving "display:none" on the buttons keypad div
        return
    }
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
// Executes user defined macros
function user_macro(prefix, name) {
    control_cmd( 'aux run_macro ' + prefix + '_' + name );
}

///////////////  MISCEL INTERNAL ////////////
// Auxs to hightlight the MUTE, MONO and LOUDNESS BUTTONS:
function buttonMuteHighlight(){
    if ( state.muted == true ) {
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
}
function buttonMonoHighlight(){
    if ( state.midside == 'mid' ) {
        document.getElementById("buttonMono").style.background = "rgb(100, 0, 0)";
        document.getElementById("buttonMono").style.color = "rgb(255, 200, 200)";
        document.getElementById("buttonMono").innerText = 'MO';
    } else if ( state.midside == 'side' ) {
        document.getElementById("buttonMono").style.background = "rgb(100, 0, 0)";
        document.getElementById("buttonMono").style.color = "rgb(255, 200, 200)";
        document.getElementById("buttonMono").innerText = 'L-R';
    } else {
        document.getElementById("buttonMono").style.background = "rgb(0, 90, 0)";
        document.getElementById("buttonMono").style.color = "white";
        document.getElementById("buttonMono").innerText = 'ST';
    }
}
function buttonLoudHighlight(){
    if ( state.loudness_track == true ) {
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
}
// Auxs to send preamp changes and display new values w/o waiting for the autoupdate
function audio_change(param, value) {
    if ( param == 'level') {
        document.getElementById('levelInfo').innerHTML =
                                    (state[param] + value).toFixed(1);
    }else if( param == 'bass'){
        document.getElementById('bassInfo').innerHTML =
                         'BASS: ' + (state[param] + value).toFixed(0);
    }else if( param == 'treble'){
        document.getElementById('trebleInfo').innerHTML =
                         'TREB: ' + (state[param] + value).toFixed(0);
    }else if( param == 'balance'){
        document.getElementById('balInfo').innerHTML =
                         'BAL: ' + (state[param] + value).toFixed(0);
    }else{
        return;
    }
    control_cmd( param + ' ' + value + ' add' );
}
function mute_toggle() {
    state.muted = ! state.muted;
    buttonMuteHighlight();
    control_cmd( 'mute toggle' );
}
function loudness_toggle() {
    state.loudness_track = ! state.loudness_track;
    buttonLoudHighlight();
    control_cmd( 'loudness_track toggle' );
}
function mono_toggle() {
    if (state.midside == "mid" || state.midside == "side"){
        state.midside = "off";
    }else{
        state.midside = "mid";
    }
    buttonMonoHighlight();
    control_cmd( 'mono toggle' );
}
// Aux to toggle displaying macro buttons
function macros_toggle() {
    var curMode = document.getElementById( "macro_buttons").style.display;
    if (curMode == 'none') {
        document.getElementById( "macro_buttons").style.display = 'inline-table'
    }
    else {
        document.getElementById( "macro_buttons").style.display = 'none'
    }
}
// Aux to clearing selector elements to avoid repeating
// when audio processes have changed
function select_clear_options(ElementId){
    // https://www.w3schools.com/jsref/dom_obj_select.asp
    const mySel = document.getElementById(ElementId);
    for (opt in mySel.options){
        mySel.remove(opt);
    }
}
// Aux to toggle advanced controls
function advanced_toggle() {
    if ( advanced_controls !== true ) {
        advanced_controls = true;
    }
    else {
        advanced_controls = false;
    }
    page_update();
}
// Aux to avoid http socket lossing some symbols
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


