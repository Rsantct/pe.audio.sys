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
var show_advanced = false;          // defaults for display advanced controls
var show_graphs   = false;          // defaults for show graphs
var metablank = {                   // A player's metadata blank dict
    'player':       '',
    'time_pos':     '',
    'time_tot':     '',
    'bitrate':      '',
    'artist':       '',
    'album':        '',
    'title':        '',
    'track_num':    '',
    'tracks_tot':   ''
    }
var last_loudspeaker = ''           // Will detect if audio processes has beeen
                                    // restarted with new loudspeaker configuration.
var macro_button_list = [];
var hold_tmp_msg = 0;               // A counter to keep tmp_msg during updates
var tmp_msg = '';                   // A temporary message

// Web config dictionary
try{
    var web_config = JSON.parse( control_cmd('aux get_web_config') );
}catch(e){
    console.log('problems with aux get_web_config', e.name, e.message);
    var web_config = { 'hide_macro_buttons': false,
                       'hide_LU':            false,
                       'LU_monitor_enabled': false,
                       'restart_cmd_info':   '',
                       'show_graphs':        false,
                     };
}

// SERVER SIDE COMMUNICATION
function control_cmd( cmd ) {
    /*
    We need synchronous mode (async=false), althougt it is deprecated
    and not recommended in the main JS thread.
    https://developer.mozilla.org/en/docs/Web/API/XMLHttpRequest
    https://developer.mozilla.org/en-US/docs/Web/API/XMLHttpRequest/Using_XMLHttpRequest
    https://developer.mozilla.org/en-US/docs/Web/API/XMLHttpRequest/Synchronous_and_Asynchronous_Requests
    */

    // avoids http socket lossing some symbols
    cmd = http_prepare(cmd);

    const myREQ = new XMLHttpRequest();

    myREQ.open(method="GET", url = URL_PREFIX + "?command=" + cmd,
               async=false);
    // (i) send() is blocking because async=false, so no handlers
    //     on myREQ status changes are needed because of this.
    myREQ.send();
    ans = myREQ.responseText;

    //console.log('httpTX: ' + cmd);
    //console.log('httpRX: ' + ans);

    if ( ans.indexOf('socket_connect\(\) failed' ) == -1 ){
        return ans;
    }else{
        return '';
    }
}


//////// PAGE MANAGEMENT ////////

// Page INITIATE
function page_initiate(){
    // Macros buttons (!) place this first because
    // aux server is supposed to be always alive
    fill_in_macro_buttons();
    // Shows or hides the macro buttons
    if ( web_config.hide_macro_buttons == true ){
        document.getElementById("macro_buttons").style.display = 'none';
    }else{
        document.getElementById("macro_buttons").style.display = 'inline-table';
    }
    // Shows or hides the LU offset slider and the LU monitor bar
    if ( web_config.hide_LU == true ){
        document.getElementById("LU_offset").style.display = 'none';
        document.getElementById("LU_monitor").style.display = 'none';
    }else{
        document.getElementById("LU_offset").style.display = 'block';
        if ( web_config.LU_monitor_enabled == true ){
            document.getElementById("LU_monitor").style.display = 'block';
        }
    }
    // Updates the title of the restart button as per config.yml
    document.getElementById("restart_switch").title = 'RESTART: ' +
                                         web_config.restart_cmd_info;
    // Schedules the page_update (only runtime variable items):
    // Notice: the function call inside setInterval uses NO brackets)
    setInterval( page_update, AUTO_UPDATE_INTERVAL );
}


// Page STATIC ITEMS (HEADER and SELECTORS)
function fill_in_page_statics(){
    // Aux to clearing selector elements to avoid repeating items
    // when audio processes have changed
    function select_clear_options(ElementId){
        // https://www.w3schools.com/jsref/dom_obj_select.asp
        const mySel = document.getElementById(ElementId);
        for (opt in mySel.options){
            mySel.remove(opt);
        }
    }
    // Fills in the INPUTS selector
    function fill_in_inputs_selector() {
        try{
            var inputs = JSON.parse( control_cmd( 'get_inputs' ) );
        }catch(e){
            console.log( e.name, e.message );
            return;
        }
        // Filling in options in a selector
        // https://www.w3schools.com/jsref/dom_obj_select.asp
        select_clear_options(ElementId="inputsSelector");
        const mySel = document.getElementById("inputsSelector");
        for ( i in inputs) {
            var option = document.createElement("option");
            option.text = inputs[i];
            mySel.add(option);
        }
        // And adds the input 'none' as expected in core.Preamp
        // so that all inputs will be disconnected.
        var option = document.createElement("option");
        option.text = 'none';
        mySel.add(option);
    }
    // Fills in the XO selector
    function fill_in_xo_selector() {
        try{
            var xo_sets = JSON.parse( control_cmd( 'get_xo_sets' ) );
        }catch(e){
            console.log( e.name, e.message );
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
    // Fills in the DRC selector
    function fill_in_drc_selector() {
        try{
            var drc_sets = JSON.parse( control_cmd( 'get_drc_sets' ) );
        }catch(e){
             console.log( e.name, e.message );
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
    // Fills in the TARGETS selector
    function fill_in_target_selector() {
        try{
            var target_files = JSON.parse( control_cmd( 'get_target_sets' ) );
        }catch(e){
            console.log( e.name, e.message );
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
    // Fills in the LU scope selector
    function fill_in_LUscope_selector() {
        try{
            const LU_mon_dict = JSON.parse( control_cmd('aux get_loudness_monitor') );
        }catch(e){
            console.log( e.name, e.message );
            return;
        }
        select_clear_options(ElementId="LUscopeSelector");
        const mySel = document.getElementById("LUscopeSelector");
        scopes = ['input', 'album', 'track'];
        for ( i in scopes ) {
            var option = document.createElement("option");
            option.text = scopes[i];
            mySel.add(option);
        }
    }
    // Shows the PEQ info
    function show_peq_info() {
        if ( state.peq_set != 'none'){
            document.getElementById("peq").style.color = "white";
            document.getElementById("peq").innerHTML = "PEQ: " + state.peq_set;
        }
        else {
            document.getElementById("peq").style.color = "grey";
            document.getElementById("peq").innerHTML = "(no peq)";
        }
    }

    // Web header:
    document.getElementById("main_cside").innerText = ':: pe.audio.sys :: ' +
                                                       state.loudspeaker;
    // Selectors:
    fill_in_inputs_selector();
    fill_in_target_selector();
    fill_in_xo_selector();
    fill_in_drc_selector();
    fill_in_LUscope_selector();
    show_peq_info();
}


// Page UPDATE (RUNTIME VARIABLE ITEMS):
function page_update() {

    // Amplifier switching (aux service always runs)
    update_ampli_switch();

    // Getting the current STATUS
    try{
        state = JSON.parse( control_cmd('get_state') );
        if (state == null){
            document.getElementById("main_cside").innerText =
                    ':: pe.audio.sys :: preamp OFFLINE';
            return;
        } else {
            if ( hold_tmp_msg == 0 ){
                document.getElementById("main_cside").innerText =
                        ':: pe.audio.sys :: ' + state.loudspeaker;
            } else {
                document.getElementById("main_cside").innerText = tmp_msg;
                hold_tmp_msg -= 1;
            }
        }
    }catch(e){
        console.log( 'not connected', e.name, e.message );
        state = {loudspeaker:'not connected'};
    }

    // Refresh static stuff if loudspeaker's audio processes has changed
    if ( last_loudspeaker != state.loudspeaker ){
        fill_in_page_statics();
        last_loudspeaker = state.loudspeaker;
    }

    // Cancel updating if not connected
    if (state.loudspeaker == 'not connected'){
        document.getElementById("levelInfo").innerHTML  = '--';
        return;
    }

    // Updates level, balance, and tone info
    document.getElementById("levelInfo").innerHTML  = state.level.toFixed(1);
    document.getElementById("balInfo").innerHTML    = 'BAL: '  + state.balance;
    document.getElementById("bassInfo").innerText   = 'BASS: ' + state.bass;
    document.getElementById("trebleInfo").innerText = 'TREB: ' + state.treble;

    // Delete level info if convolver off
    if (state.convolver_runs == false){
        document.getElementById("levelInfo").innerHTML  = '--';
    }

    // Updates the Integrated LU monitor and the LU offset slider
    document.getElementById("LU_offset_value").innerText =
                                      'LU offset: ' + -1 * state.loudness_ref;
    document.getElementById("LU_slider").value           = state.loudness_ref;
    try{
        const LU_mon_dict = JSON.parse( control_cmd('aux get_loudness_monitor') );
        const LU_I = LU_mon_dict.LU_I
        var scope  = LU_mon_dict.scope
        // Preferred displaying 'track' instead of 'title'
        if ( scope == 'title' ) {
            scope = 'track';
        }
        document.getElementById("LU_meter").value           = LU_I;
        document.getElementById("LUscopeSelector").value    = scope;
        document.getElementById("LU_meter_value").innerHTML ='LU monit: ' + LU_I;
    }catch(e){
        console.log('Error getting loudness monitor from server', e.name, e.message);
    }

    // Updates current INPUTS, XO, DRC, and TARGET (PEQ is meant to be static)
    document.getElementById("inputsSelector").value = state.input;
    document.getElementById("xoSelector").value     = state.xo_set;
    document.getElementById("drcSelector").value    = state.drc_set;
    document.getElementById("targetSelector").value = state.target;

    // Highlights activated buttons and related indicators accordingly
    buttonMuteHighlight()
    buttonMonoHighlight()
    buttonLoudHighlight()

    // Updates metadata player info
    update_player_info()

    // Highlights player controls when activated
    update_player_controls()

    // Artifice to wait 3000 milliseconds to refresh brutefir_eq.png
    if ( show_graphs == true ) {
        document.getElementById("bfeq_img").src = 'images/brutefir_eq.png?'
                                                  + Math.floor(Date.now()/3000);
    }

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


//////// PREAMP FUNCTIONS ////////

// INPUT selection
function input_select(iname){
    hold_tmp_msg = 3;
    tmp_msg = 'Please wait for "' + iname + '"';
    document.getElementById("main_cside").innerText = tmp_msg;
    setTimeout(() => { control_cmd('input ' + iname); }, 200);
    clear_highlighted();
    document.getElementById('inputsSelector').style.color = "white";
}

// DRC selection
function drc_select(drcName){
    control_cmd('set_drc ' + drcName);
    clear_highlighted();
    document.getElementById('drcSelector').style.color = "white";
}

// XO selection
function xo_select(xoName){
    control_cmd('set_xo ' + xoName);
    clear_highlighted();
    document.getElementById('xoSelector').style.color = "white";
}

// TARGET selection
function target_select(xoName){
    control_cmd('set_target ' + xoName);
    clear_highlighted();
    document.getElementById('targetSelector').style.color = "white";
}

// LU_monitor SCOPE selection
function LU_scope_select(scope){
    control_cmd('aux set_loudness_monitor_scope ' + scope);
    clear_highlighted();
    document.getElementById('LUscopeSelector').style.color = "white";
}


//////// PLAYERS FUNCTIONS ////////

// Controls the player
function playerCtrl(action) {
    control_cmd( 'player ' + action );
}

// Updates the player control buttons, hightlights the corresponding button to the playback state
function update_player_controls() {
    try{
        var playerState = control_cmd( 'player state' );
        if (playerState == "null"){
            document.getElementById("main_cside").innerText =
                    ':: pe.audio.sys :: players OFFLINE';
            return;
        }
    }catch(e){
        console.log( 'error getting player state', e.name, e.message );
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
        var tmp = control_cmd( 'player get_meta' );
        if (tmp == "null"){
            document.getElementById("main_cside").innerText =
                    ':: pe.audio.sys :: players OFFLINE';
            return;
        }
    }catch(e){
        console.log( 'error getting player meta', e.name, e.message );
        return;
    }
    // players.py will allways give a dictionary as response, but if
    // no metadata are available then most fields will be empty, except 'player'
    if ( tmp.indexOf("failed")  == -1 &&
         tmp.indexOf("refused") == -1    )  {

        try{
            var d = JSON.parse( tmp );
        }catch(e){
            console.log( 'error parsing metadata to dict, using metablank',
                          e.name, e.message );
            var d = metablank;
        }

        if ( d['artist'] == ''  && d['album'] == '' && d['title'] == '' ){
            d = metablank;
        }

        if (d['bitrate']) {
            document.getElementById("bitrate").innerText = d['bitrate'] + "\nkbps";
        } else {
            document.getElementById("bitrate").innerText = "-\nkbps"
        }
        if (d['artist']) {
            document.getElementById("artist").innerText  = d['artist'];
        } else {
            document.getElementById("artist").innerText = "-"
        }
        if (d['track_num']) {
            document.getElementById("track_info").innerText   = d['track_num'];
        } else {
            document.getElementById("track_info").innerText = "-"
        }
        if (d['tracks_tot']) {
            document.getElementById("track_info").innerText += ('\n' + d['tracks_tot']);
        } else {
            document.getElementById("track_info").innerText += "\n-"
        }
        if (d['time_pos']) {
            document.getElementById("time").innerText    = d['time_pos'] + "\n" + d['time_tot'];
        } else {
            document.getElementById("time").innerText = "-"
        }
        if (d['album']) {
            document.getElementById("album").innerText   = d['album'];
        } else {
            document.getElementById("album").innerText = "-"
        }
        if (d['title']) {
            document.getElementById("title").innerText   = d['title'];
        } else {
            document.getElementById("title").innerText = "-"
        }
    }
}

// Emerge a dialog to select a disk track to be played
function select_track() {
    var tracknum = prompt('Enter track number to play:');
    if ( true ) {
        control_cmd( 'player play_track_' + tracknum );
    }
}

// Sends an url to the server, to be played back
function play_url() {
    var url = prompt('Enter url to play:');
    if ( url.slice(0,5) == 'http:' || url.slice(0,6) == 'https:' ) {
        control_cmd( 'aux play ' + url );
    }
}


//////// AUX FUNCTIONS ////////

// Restart procedure
function peaudiosys_restart() {
    control_cmd('aux restart');
    advanced('off');
    page_update();
}

// Switch the amplifier
function ampli(mode) {
    control_cmd( 'aux amp_switch ' + mode );
}

// Queries the remote amplifier switch state
function update_ampli_switch() {
    try{
        var amp_state = control_cmd( 'aux amp_switch state' )
                           .replace('\n','');
        // cosmetic for button not void
        if ( ! amp_state ) {
            var amp_state = '-';
        }
    }catch(e){
        console.log( 'Amp switch error', e.name, e.message );
        var amp_state = '-';
    }
    document.getElementById("OnOffButton").innerText = amp_state.toUpperCase();
}

// Filling in the user's macro buttons
function fill_in_macro_buttons() {
    try{
        var mFnames = JSON.parse( control_cmd( 'aux get_macros' ).split(',') );
    }catch(e){
    // If no macros list, do nothing, so leaving "display:none" on the buttons keypad div
        console.log( 'no macros', e.name, e.message );
        return
    }
    // If any macro found, lets show the corresponding cell playback_control_23
    // also call xx_21 just for symmetry reasons
    document.getElementById( "playback_control_23").style.display = 'block';
    document.getElementById( "playback_control_21").style.display = 'block';


    // Expands number of buttons to a multiple of 3 (arrange of Nx3 buttons)
    // (i) mFnames is supposed to be properly sorted.
    var bTotal = parseInt(mFnames[mFnames.length - 1].split('_')[0])
    bTotal = 3 * ( Math.floor( (bTotal - 1) / 3) + 1 )

    var mtable = document.getElementById("macro_buttons");
    var row  = mtable.insertRow(index=-1);

    // Iterate over button available cells
    for (bPos = 1; bPos <= bTotal; bPos++) {

        // Iterate over macro filenames
        found = false;
        for ( i in mFnames ){
            // Macro file names: 'N_macro_name' where N is the button position
            var mFname = mFnames[i];
            var mPos  = mFname.split('_')[0];
            var mName = mFname.slice(mFname.indexOf('_') + 1, mFname.length);
            if ( mPos == bPos ){
                found = true;
                break;
            }
        }

        // Insert a cell
        var cell = row.insertCell(index=-1);
        cell.className = 'macro_cell';

        // Create a button Element
        var btn = document.createElement('button');
        btn.type = "button";
        btn.className = "macro_button";
        macro_button_list.push(mName);
        if ( found == true ){
            btn.id = mName;
            btn.innerHTML = mName;
            // This doesn't work: always pass mFname incorrectly to run_macro()
            //btn.onclick=function(){run_macro(mFname)}
            // As a workaround lets set the onclick attribute:
            btn.setAttribute( "onclick",
                              "run_macro(\'" + mFname + "\')" );
        }else{
            btn.innerHTML = '-';
        }

        // Put the button inside the cell
        cell.appendChild(btn);

        // Arrange 3 buttons per row
        if ( bPos % 3 == 0 ) {
            row  = mtable.insertRow(index=-1);
        }
    }
}

// Runs a macro
function run_macro(mFname){
    //console.log(mFname);
    control_cmd( 'aux run_macro ' + mFname );
    var mName = mFname.slice(mFname.indexOf('_') + 1, mFname.length);
    clear_highlighted();
    setTimeout(() => { highlight_macro_button(mName);}, 200);
    hold_tmp_msg = 3;
    tmp_msg = 'Please wait for "' + mName + '"';
}


///////////////  MISCEL INTERNAL ////////////

// Hightlights a macro button
function highlight_macro_button(id){
    document.getElementById(id).className = 'macro_button_highlighted';
}

// Clear highlighteds
function clear_highlighted(){
    for (i = 0; i < macro_button_list.length; i++) {
        document.getElementById(macro_button_list[i]).className = 'macro_button';
    }
    document.getElementById('inputsSelector').style.color   = "rgb(200,200,200)";
    document.getElementById('drcSelector').style.color      = "rgb(200,200,200)";
    document.getElementById('xoSelector').style.color       = "rgb(200,200,200)";
    document.getElementById('targetSelector').style.color   = "rgb(200,200,200)";
}

// Highlights the MUTE, MONO and LOUDNESS BUTTONS:
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
    // 'solo' setting will override displaying mono stereo
    if ( state.solo == 'l' ) {
        document.getElementById("buttonMono").style.background = "rgb(100, 0, 0)";
        document.getElementById("buttonMono").style.color = "rgb(255, 200, 200)";
        document.getElementById("buttonMono").innerText = 'L_';
    } else if ( state.solo == 'r' ) {
        document.getElementById("buttonMono").style.background = "rgb(100, 0, 0)";
        document.getElementById("buttonMono").style.color = "rgb(255, 200, 200)";
        document.getElementById("buttonMono").innerText = '_R';
    }
    // temporary experimental 'polarity' setting will override 'midside' and 'solo'
    if ( state.polarity == '+-' ) {
        document.getElementById("buttonMono").style.background = "rgb(100, 0, 0)";
        document.getElementById("buttonMono").style.color = "rgb(255, 200, 200)";
        document.getElementById("buttonMono").innerText = '+-';
    } else if ( state.polarity == '-+' ) {
        document.getElementById("buttonMono").style.background = "rgb(100, 0, 0)";
        document.getElementById("buttonMono").style.color = "rgb(255, 200, 200)";
        document.getElementById("buttonMono").innerText = '-+';
    }
}
function buttonLoudHighlight(){
    if ( state.loudness_track == true ) {
        document.getElementById("buttonLoud").style.background = "rgb(0, 90, 0)";
        document.getElementById("buttonLoud").style.color = "white";
        document.getElementById("buttonLoud").innerText = 'LC';
    } else {
        document.getElementById("buttonLoud").style.background = "rgb(100, 100, 100)";
        document.getElementById("buttonLoud").style.color = "rgb(150, 150, 150)";
        document.getElementById("buttonLoud").innerText = 'LC';
    }
}

// Send preamp changes and display new values w/o waiting for the autoupdate
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

// Toggle displaying macro buttons
function macros_toggle() {
    var curMode = document.getElementById( "macro_buttons").style.display;
    if (curMode == 'none') {
        document.getElementById( "macro_buttons").style.display = 'inline-table'
    }
    else {
        document.getElementById( "macro_buttons").style.display = 'none'
    }
}

// Displays or hides the advanced controls section
// (i) This also allows access to the RESTART button
function advanced(mode) {
    if ( mode == 'toggle' ){
        if ( show_advanced !== true ) {
            show_advanced = true;
        }
        else {
            show_advanced = false;
        }
    }
    else if ( mode == 'off' ){
        show_advanced = false;
    }
    else if ( mode == 'on' ){
        show_advanced = true;
    }

    if ( show_advanced == true ) {
        document.getElementById( "advanced_controls").style.display = "block";
        document.getElementById( "level_buttons13").style.display = "table-cell";
        document.getElementById( "main_lside").style.display = "table-cell";
    }
    else {
        document.getElementById( "advanced_controls").style.display = "none";
        document.getElementById( "level_buttons13").style.display = "none";
        document.getElementById( "main_lside").style.display = "none";
    }
}

// Toggle displaying graphs
function graphs_toggle() {
    if ( web_config.show_graphs == false ){
        return;
    }
    if ( show_graphs !== true ) {
        show_graphs = true;
    }
    else {
        show_graphs = false;
    }

    if ( show_graphs == true ){
        document.getElementById("drc_graph").style.display = 'block';
        document.getElementById("bfeq_graph").style.display = 'block';
        // Points to the current DRC png
        document.getElementById("drc_img").src =  'images/drc_' + state.drc_set
                                                               + '.png';
        document.getElementById("bfeq_img").src = 'images/brutefir_eq.png?';
    }else{
        document.getElementById("drc_graph").style.display = 'none';
        document.getElementById("bfeq_graph").style.display = 'none';
        // Disable loading graph images to save bandwidth on page updates
        document.getElementById("drc_img").src = '';
        document.getElementById("bfeq_img").src = '';
    }
}

// Avoid http socket lossing some symbols
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

// Test buttons
function TESTING1(){
    //do something
}
function TESTING2(){
    //do something
}
