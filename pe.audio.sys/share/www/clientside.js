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

// SOME GLOBALS
var state               = {};       // The main state dictionary
var server_available    = false;
var show_advanced       = false;    // defaults for display advanced controls
var show_graphs         = false;    // defaults for show graphs
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
var last_disc           = '';       // Helps on refreshing cd tracks list
var last_input          = '';       // Helps on refreshing sources playlits
var last_loudspeaker    = '';       // Will detect if audio processes has beeen
                                    // restarted with new loudspeaker configuration.
var macro_button_list   = [];
var hold_selected_track = 0;        // A counter to keep the selected cd track during updates
var hold_tmp_msg        = 0;        // A counter to keep tmp_msg during updates
var tmp_msg             = '';       // A temporary message

// STATIC WEB CONFIGURATION
try{
    var web_config = JSON.parse( control_cmd('aux info') )['web_config'];
}catch(e){
    console.log('problems with \'aux info\' command', e.name, e.message);
    var web_config = { 'main_selector':      'inputs',
                       'hide_LU':            false,
                       'LU_monitor_enabled': false,
                       'restart_cmd_info':   '',
                       'show_graphs':        false,
                       'user_macros':        []
                     };
}
var main_selector = web_config.main_selector;
var mFnames = web_config.user_macros;   // User macros


// SERVER SIDE COMMUNICATION (updates <server_available>)
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
        server_available = true;
        return ans;
    }else{
        server_available = false;
        return '';
    }
}


//////// PAGE MANAGEMENT ////////

// PAGE INITIATE
function page_initiate(){

    state_update();

    // Macros buttons (!) place this first because
    // aux server is supposed to be always alive
    fill_in_macro_buttons();

    // playlists selector for some sources
    fill_in_playlists_selector();

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


// PAGE STATIC ITEMS (HEADER and SELECTORS)
function fill_in_page_statics(){

    // MAIN_SELECTOR
    function fill_in_main_selector(){
        // standard INPUTS manager
        if ( main_selector == 'inputs' ){
            document.getElementById("mainSelector").title = 'Source Selector';
            document.getElementById("macro_buttons").style.display = 'inline-table';
            fill_in_main_as_inputs();

        // alternative MACROS manager
        }else{
            document.getElementById("mainSelector").title = 'Macros Launcher';
            document.getElementById("macro_buttons").style.display = 'none';
            fill_in_main_as_macros();
        }
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

    // Level cell info
    document.getElementById("levelInfo").title = 'Target volume ref@' +
                                                 state.loudspeaker_ref_SPL + 'dBSPL';

    // Selectors:
    fill_in_main_selector();
    fill_in_target_selector();
    fill_in_xo_selector();
    fill_in_drc_selector();
    fill_in_LUscope_selector();

    // PEQ info
    show_peq_info();
}


// STATE DICT. UPDATE by queriyng the server
function state_update() {
    try{
        state = control_cmd('preamp state');
        // console.log('Rx state:', state); # debug
        state = JSON.parse( state );
        if (state == null){
            document.getElementById("main_cside").innerText =
                    ':: pe.audio.sys :: preamp OFFLINE';
            return;

        } else {

            if ( hold_tmp_msg == 0 ){

                let warning = control_cmd('aux warning get');

                if (warning == ''){
                    document.getElementById("main_cside").innerText =
                            ':: pe.audio.sys :: ' + state.loudspeaker;
                } else {
                    document.getElementById("main_cside").innerText = warning;
                }

            } else {
                document.getElementById("main_cside").innerText = tmp_msg;
                hold_tmp_msg -= 1;
            }

        }
    }catch(e){
        console.log( 'not connected', e.name, e.message );
        state = {loudspeaker:'not connected'};
    }
}


// PAGE UPDATE (RUNTIME VARIABLE ITEMS):
function page_update() {

    // Amplifier switching (aux service always runs)
    ampli_switch_update();

    // Getting the current STATUS
    state_update();

    // Refresh static stuff if loudspeaker's audio processes has changed
    if ( last_loudspeaker != state.loudspeaker ){
        fill_in_page_statics();
        last_loudspeaker = state.loudspeaker;
    }

    // Cancel updating if not connected
    if (!server_available){
        document.getElementById("levelInfo").innerHTML  = '--';
        player_info_clear();
        player_controls_clear();
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
    document.getElementById("LU_slider").value           = (15 - state.lu_offset);
    document.getElementById("LU_offset_value").innerText =
                                        'LU offset: ' + -1 * state.lu_offset;
    try{
        const LU_mon_dict = JSON.parse( control_cmd('aux get_loudness_monitor') );
        const LU_I = LU_mon_dict.LU_I
        var scope  = LU_mon_dict.scope
        // Preferred displaying 'track' instead of 'title'
        if ( scope == 'title' ) {
            scope = 'track';
        }
        document.getElementById("LU_meter").value           = -LU_I;
        document.getElementById("LUscopeSelector").value    = scope;
        if (LU_I <= 0){
          document.getElementById("LU_meter_value").innerHTML ='LU monit: ' + LU_I;
        }else{
          document.getElementById("LU_meter_value").innerHTML ='LU monit: +' + LU_I;
        }
    }catch(e){
        console.log('Error getting loudness monitor from server', e.name, e.message);
    }

    // Updates current INPUTS, XO, DRC, and TARGET (PEQ is meant to be static)
    if ( main_selector == 'macros' ){
        var mName = control_cmd('aux get_last_macro');
        document.getElementById("mainSelector").value =
                            mName.slice(mName.indexOf('_') + 1, mName.length);
    }else{
        document.getElementById("mainSelector").value = state.input;
    }
    document.getElementById("xoSelector").value     = state.xo_set;
    document.getElementById("drcSelector").value    = state.drc_set;
    document.getElementById("targetSelector").value = state.target;

    // Highlights activated buttons and related indicators accordingly
    buttonMuteHighlight()
    buttonMonoHighlight()
    buttonLoudHighlight()
    buttonsToneBalanceHighlight()
    buttonSubsonicHighlight()
    levelInfoHighlight()

    // Updates all player stuff
    player_all_update()

    // Artifice to wait 3000 milliseconds to refresh brutefir_eq.png
    if ( show_graphs == true ) {
        document.getElementById("bfeq_img").src = 'images/brutefir_eq.png?'
                                                  + Math.floor(Date.now()/3000);
    }

    // Displays and updates the playlist loader for some sources when input source changed
    if (last_input != state.input){
        if ( state.input == "mpd"     ||
             state.input == "spotify" ) {
            fill_in_playlists_selector()
            document.getElementById( "playlist_selector").style.display = "inline";
        }
        else {
            document.getElementById( "playlist_selector").style.display = "none";
        }
        last_input = state.input;
    }

    // Displays the track selector if input == 'cd'
    if ( state.input == "cd") {
        document.getElementById( "track_selector").style.display = "inline";
    }
    else {
        document.getElementById( "track_selector").style.display = "none";
    }

    // Clears the CD track selector when expired
    hold_selected_track -= 1;
    if (hold_selected_track == 0) {
        document.getElementById('track_selector').value = '--';
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

// MAIN SELECTOR
function main_select(itemName){
    // (i) The main selector can have two flavors:
    //      - regular input selector management
    //      - alternative macros management

    // Aux for macros manager behavior
    function find_macroName(x){
        var result = '';
        for ( i in mFnames ){
            var mFname = mFnames[i];
            var mName = mFname.slice(mFname.indexOf('_') + 1, mFname.length);
            if ( x == mName ){
                result = mFname;
                break
            }
        }
        return result;
    }

    display_tmp_msg( 'Please wait for "' + itemName + '"', 3 );

    // (i) The arrow syntax '=>' fails on Safari iPad 1 (old version)
    // setTimeout( () => { control_cmd('input ' + itemName); }, 200 );
    function tmp(itemName){
        // regular behavior managing preamp inputs
        if ( main_selector == 'inputs' ){
            control_cmd('input ' + itemName);
        // alternative behavior managing macros
        }else{
            mName = find_macroName(itemName);
            control_cmd( 'aux run_macro ' + mName );
            last_macro = mName;
        }
    }
    setTimeout( tmp, 200, itemName );  // 'itemName' is given as argument for 'tmp'

    clear_highlighted();
    document.getElementById('mainSelector').style.color = "white";

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
    if (action == 'random_toggle') {
        control_cmd( 'player random_mode toggle' );
    } else {
        control_cmd( 'player ' + action );
    }
}

// Retrieves and updates all player stuff
function player_all_update(){
    try{
        var player_all_info = control_cmd( 'player get_all_info' );
        if (player_all_info == "null"){
            document.getElementById("main_cside").innerText =
                    ':: pe.audio.sys :: players OFFLINE';
            return;
        } else {
            player_all_info = JSON.parse(player_all_info);
        }
    }catch(e){
        console.log( 'error getting player info', e.name, e.message );
        return;
    }

    player_controls_update(     player_all_info.state );
    player_metadata_update(     player_all_info.metadata );
    player_random_mode_update(  player_all_info.random_mode);

    // Updates tracks list if disc has changed
    if (last_disc != player_all_info.discid) {
        fill_in_track_selector();
        last_disc = player_all_info.discid;
    }

}

// Highlights the random mode button:
function player_random_mode_update(mode){
    if        ( mode=='on' ) {
        document.getElementById("random_toggle_button").style.background  = "rgb(185, 185, 185)";
        document.getElementById("random_toggle_button").style.color       = "white";

    } else {
        document.getElementById("random_toggle_button").style.background  = "rgb(100, 100, 100)";
        document.getElementById("random_toggle_button").style.color       = "lightgray";
    }
}

// Hightlights the corresponding playback button as per the playback state
function player_controls_update(playerState) {

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
function player_metadata_update(d) {


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

// Aux to clear controls when not connected
function player_controls_clear() {
    document.getElementById("buttonStop").style.background  = "rgb(100, 100, 100)";
    document.getElementById("buttonStop").style.color       = "lightgray";
    document.getElementById("buttonPause").style.background = "rgb(100, 100, 100)";
    document.getElementById("buttonPause").style.color      = "lightgray";
    document.getElementById("buttonPlay").style.background  = "rgb(100, 100, 100)";
    document.getElementById("buttonPlay").style.color       = "lightgray";
}

// Aux to clear metadata when not connected
function player_info_clear() {
    document.getElementById("bitrate").innerText = "-\nkbps"
    document.getElementById("artist").innerText = "-"
    document.getElementById("track_info").innerText = "-"
    document.getElementById("track_info").innerText += "\n-"
    document.getElementById("time").innerText = "-"
    document.getElementById("album").innerText = "-"
    document.getElementById("title").innerText = "-"
}

// When changing a playlist selector
function load_playlist(plistname) {
    if (plistname == '-CLEAR-') {
        control_cmd( 'player clear_playlist ' );
    } else if (plistname != '--') {
        control_cmd( 'player clear_playlist ' );
        control_cmd( 'player load_playlist ' + plistname );
    }
}

// Emerge a dialog to select a disk track number to be played (currently not used)
function select_track_number_dialog() {
    var tracknum = prompt('Enter track number to play:');
    if ( true ) {
        control_cmd( 'player play_track ' + tracknum );
    }
}

// Plays a track number
function play_track_number(N) {
    control_cmd( 'player play_track ' + N );
    hold_selected_track = 10;
}

// Sends an url to the server, for it to play
function play_url() {
    var url = prompt('Enter url to play:');
    if ( url.slice(0,5) == 'http:' || url.slice(0,6) == 'https:' ) {
        control_cmd( 'aux play ' + url );
    }
}


//////// AUX FUNCTIONS ////////

// Aux to clearing selector elements, aka options.
function select_clear_options(ElementId){
    // https://www.w3schools.com/jsref/dom_obj_select.asp
    var mySel = document.getElementById(ElementId);
    while (mySel.length > 0){
        mySel.remove( mySel.length-1 );
    }
}

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
function ampli_switch_update() {
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

// MAIN SELECTOR manages inputs:
function fill_in_main_as_inputs() {
    // getting input names
    try{
        var inputs = JSON.parse( control_cmd( 'get_inputs' ) );
    }catch(e){
        console.log( e.name, e.message );
        return;
    }
    // clearing selector options
    select_clear_options(ElementId="mainSelector");
    // Filling in options in a selector
    // https://www.w3schools.com/jsref/dom_obx.length-1j_select.asp
    var mySel = document.getElementById("mainSelector");
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

// MAIN SELECTOR manages macros
function fill_in_main_as_macros() {

    // clearing selector options
    select_clear_options(ElementId="mainSelector");

    // Filling in options in a selector
    // https://www.w3schools.com/jsref/dom_obj_select.asp
    var mySel = document.getElementById("mainSelector");
    for ( i in mFnames) {
        var mFname = mFnames[i];
        var mName  = mFname.slice(mFname.indexOf('_') + 1, mFname.length);
        var option = document.createElement("option");
        option.text = mName;
        mySel.add(option);
    }
}

// Filling in the user's macro buttons
function fill_in_macro_buttons() {

    // If empty macros list, do nothing
    if ( mFnames.length == 0 ){
        console.log( '(i) empty macros array', mFnames)
        document.getElementById( "macro_buttons").style.display = 'none';
        return
    }

    // If any macro found, lets show the corresponding button
    document.getElementById( "macros_toggle_button").style.display = 'inline';


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

// Filling in playlists selector:
function fill_in_playlists_selector() {
    // getting playlists
    try{
        var plists = JSON.parse( control_cmd( 'player get_playlists' ) );
    }catch(e){
        console.log( e.name, e.message );
        return;
    }
    // clearing selector options
    select_clear_options(ElementId="playlist_selector");
    // Filling in options in a selector
    // https://www.w3schools.com/jsref/dom_obx.length-1j_select.asp
    var mySel = document.getElementById("playlist_selector");
    var option = document.createElement("option");
    option.text = '--';
    mySel.add(option);
    for ( i in plists) {
        var option = document.createElement("option");
        option.text = plists[i];
        mySel.add(option);
    }
    var option = document.createElement("option");
    option.text = '-CLEAR-';
    mySel.add(option);
}

// Filling in track selector:
function fill_in_track_selector() {
    // getting tracks
    try{
        var tracks = JSON.parse( control_cmd( 'player list_playlist' ) );
    }catch(e){
        console.log( e.name, e.message );
        return;
    }
    // clearing selector options
    select_clear_options(ElementId="track_selector");
    // Filling in options in a selector
    // https://www.w3schools.com/jsref/dom_obx.length-1j_select.asp
    var mySel = document.getElementById("track_selector");
    var option = document.createElement("option");
    option.text = '--';
    mySel.add(option);
    for ( i in tracks) {
        var option = document.createElement("option");
        option.text = tracks[i];
        mySel.add(option);
    }
    mySel.add(option);
}

// Runs a macro
function run_macro(mFname){

    control_cmd( 'aux run_macro ' + mFname );
    last_macro = mFname;

    var mName = mFname.slice(mFname.indexOf('_') + 1, mFname.length);
    clear_highlighted();

    // (i) The arrow syntax '=>' fails on Safari iPad 1 (old version)
    // setTimeout(() => { highlight_macro_button(mName);}, 200);
    function tmp(mName){
        highlight_macro_button(mName);
    }
    setTimeout( tmp, 200, mName );  // 'mName' is given as argument for 'tmp'

    display_tmp_msg( 'Please wait for "' + mName + '"', 3);
}

// Manages the LU_offset slider
function LU_slider_action(slider_value){
    control_cmd( 'lu_offset ' + (15 - parseInt(slider_value) ).toString() )
}


///////////////  MISCEL INTERNAL ////////////

// Displays a temporary message for some seconds within the upper frame.
function display_tmp_msg(msg, timeout){
    hold_tmp_msg    = timeout;     // these two are global variables checked when
    tmp_msg         = msg;         // every update
    document.getElementById("main_cside").innerText = tmp_msg;
}

// Hightlights a macro button
function highlight_macro_button(id){
    document.getElementById(id).className = 'macro_button_highlighted';
}

// Clear highlighteds
function clear_highlighted(){
    for (i = 0; i < macro_button_list.length; i++) {
        document.getElementById(macro_button_list[i]).className = 'macro_button';
    }
    document.getElementById('mainSelector').style.color   = "rgb(200,200,200)";
    document.getElementById('drcSelector').style.color      = "rgb(200,200,200)";
    document.getElementById('xoSelector').style.color       = "rgb(200,200,200)";
    document.getElementById('targetSelector').style.color   = "rgb(200,200,200)";
}

// Highlights the BASS, TREBLE, BALANCE, MUTE, MONO and LOUDNESS BUTTONS:
function buttonsToneBalanceHighlight(){
    if ( state.bass < 0 ){
        document.getElementById("bass-").style.border = "3px solid rgb(160, 160, 160)";
        document.getElementById("bass+").style.border = "2px solid rgb(100, 100, 100)";
    }else if ( state.bass > 0 ){
        document.getElementById("bass-").style.border = "2px solid rgb(100, 100, 100)";
        document.getElementById("bass+").style.border = "3px solid rgb(160, 160, 160)";
    }else{
        document.getElementById("bass-").style.border = "2px solid rgb(100, 100, 100)";
        document.getElementById("bass+").style.border = "2px solid rgb(100, 100, 100)";
    }
    if ( state.treble < 0 ){
        document.getElementById("treb-").style.border = "3px solid rgb(160, 160, 160)";
        document.getElementById("treb+").style.border = "2px solid rgb(100, 100, 100)";
    }else if ( state.treble > 0 ){
        document.getElementById("treb-").style.border = "2px solid rgb(100, 100, 100)";
        document.getElementById("treb+").style.border = "3px solid rgb(160, 160, 160)";
    }else{
        document.getElementById("treb-").style.border = "2px solid rgb(100, 100, 100)";
        document.getElementById("treb+").style.border = "2px solid rgb(100, 100, 100)";
    }
    if ( state.balance < 0 ){
        document.getElementById("bal-").style.border = "3px solid rgb(160, 160, 160)";
        document.getElementById("bal+").style.border = "2px solid rgb(100, 100, 100)";
    }else if ( state.balance > 0 ){
        document.getElementById("bal-").style.border = "2px solid rgb(100, 100, 100)";
        document.getElementById("bal+").style.border = "3px solid rgb(160, 160, 160)";
    }else{
        document.getElementById("bal-").style.border = "2px solid rgb(100, 100, 100)";
        document.getElementById("bal+").style.border = "2px solid rgb(100, 100, 100)";
    }
}
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
    if ( state.equal_loudness == true ) {
        document.getElementById("buttonLoud").style.background = "rgb(0, 90, 0)";
        document.getElementById("buttonLoud").style.color = "white";
    } else {
        document.getElementById("buttonLoud").style.background = "rgb(100, 100, 100)";
        document.getElementById("buttonLoud").style.color = "rgb(150, 150, 150)";
    }
}
function buttonSubsonicHighlight(){
    if ( state.subsonic == 'off' ) {
        document.getElementById("subsonic").style.background = "rgb(100, 100, 100)";
        document.getElementById("subsonic").style.color = "rgb(180, 180, 180)";
        document.getElementById("subsonic").innerText = 'SUBS\n-';
    } else if ( state.subsonic == 'mp' ) {
        document.getElementById("subsonic").style.background = "rgb(100, 0, 0)";
        document.getElementById("subsonic").style.color = "rgb(255, 200, 200)";
        document.getElementById("subsonic").innerText = 'SUBS\nmp';
    } else if ( state.subsonic == 'lp' ) {
        document.getElementById("subsonic").style.background = "rgb(150, 0, 0)";
        document.getElementById("subsonic").style.color = "rgb(255, 200, 200)";
        document.getElementById("subsonic").innerText = 'SUBS\nlp';
    }
}
function levelInfoHighlight() {
    // currently only indicates subsonic filter activated
    if (state.subsonic != 'off' ){
        document.getElementById("levelInfo").style.borderWidth = "thick";
        document.getElementById("levelInfo").style.borderColor = "DarkRed";
    }else{
        document.getElementById("levelInfo").style.borderWidth = "thin";
        document.getElementById("levelInfo").style.borderColor = "white";
   }
}


// Send preamp changes and display new values
function audio_change(param, value) {
    state[param] += value;
    if ( param == 'level') {
        document.getElementById( 'levelInfo'  ).innerHTML =
                                    state[param].toFixed(1);
    }
    else if( param == 'bass'){
        document.getElementById( 'bassInfo'   ).innerHTML =
                         'BASS: ' + state[param].toFixed(0);
    }
    else if( param == 'treble'){
        document.getElementById( 'trebleInfo' ).innerHTML =
                         'TREB: ' + state[param].toFixed(0);
    }
    else if( param == 'balance'){
        document.getElementById( 'balInfo'    ).innerHTML =
                         'BAL: '  + state[param].toFixed(0);
    }
    else{
        return;
    }
    control_cmd( param + ' ' + value + ' ' + 'add' );
}
function mute_toggle() {
    state.muted = ! state.muted;
    buttonMuteHighlight();
    control_cmd( 'mute toggle' );
}
function equal_loudness_toggle() {
    state.equal_loudness = ! state.equal_loudness;
    buttonLoudHighlight();
    control_cmd( 'equal_loudness toggle' );
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
        main_selector = 'inputs';
    }
    else {
        document.getElementById( "macro_buttons").style.display = 'none'
        main_selector = 'macros';
    }
    fill_in_page_statics();
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
        document.getElementById( "RAOD").style.display = "inline-block";
        document.getElementById( "subsonic").style.display = "inline-block";
    }
    else {
        document.getElementById( "advanced_controls").style.display = "none";
        document.getElementById( "level_buttons13").style.display = "none";
        document.getElementById( "main_lside").style.display = "none";
        document.getElementById( "RAOD").style.display = "none";
        document.getElementById( "subsonic").style.display = "none";
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
        document.getElementById("drc_img").src =  'images/'
                                                + state.loudspeaker
                                                + '/drc_' + state.drc_set
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
