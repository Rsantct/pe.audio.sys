/*
    Copyright (c) Rafael Sánchez
    This file is part of 'pe.audio.sys'
    'pe.audio.sys', a PC based personal audio system.
*/

/*
   (i) debug trick: console.log(something);
       NOTICE: remember do not leaving any console.log active
*/

//////// CONFIGURABLE ITEMS
//
//  (i) Set URL_PREFIX ='/' if you use the provided peasys_node.js server script,
//      or set it '/functions.php' if you use Apache+PHP at server side.
//
const URL_PREFIX = '/functions.php';
const AUTO_UPDATE_INTERVAL = 1000;      // Auto-update interval millisec



//////// GLOBAL VARIABLES

var web_config          = { 'main_selector':      'inputs',
                            'hide_LU':            false,
                            'LU_monitor_enabled': false,
                            'show_graphs':        false,
                            'user_macros':        []
                          };

var main_sel_mode       = web_config.main_selector;

var mFnames             = web_config.user_macros; // Macro file names

var macro_button_list   = [];

var state               = {};       // The preamp-convolver state

var aux_info            = { 'amp': 'n/a',
                            'loudness_monitor': {'LU_I': 0, 'LU_M': 0, 'scope': 'track' },
                            'last_macro': '-',
                            'warning': ''
                           };

var metablank           = {         // A player's metadata blank dict
                            'player':       '',
                            'time_pos':     '',
                            'time_tot':     '',
                            'bitrate':      '',
                            'artist':       '',
                            'album':        '',
                            'title':        '',
                            'track_num':    '',
                            'tracks_tot':   ''
                            };


var server_available    = false;
var show_advanced       = false;    // defaults for display advanced controls
var hide_graphs         = true;     // defaults for displaying graphs

var last_eq_params      = {};       // To evaluate if eq curve changed
var last_drc            = '';       // To evaluate if drc changed
var last_disc           = '';       // Helps on refreshing cd tracks list
var last_input          = '';       // Helps on refreshing sources playlits
var last_loudspeaker    = '';       // Will detect if audio processes has beeen
                                    // restarted with new loudspeaker configuration.
var last_delay          = 0;        // A helper for the delay toggle button


var hold_selected_track = 0;        // A counter to keep the selected cd track during updates
var main_cside_msg      = '';       // The message displayed on page header
var hold_cside_msg      = 0;        // A counter to keep main_cside_msg during updates



//////// PAGE MANAGEMENT

function fill_in_page_statics(){

    function fill_in_main_selector(){

        function fill_in_main_as_inputs() {
            // MAIN SELECTOR manages inputs:

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


        function fill_in_main_as_macros() {
            // MAIN SELECTOR manages macros:

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


        // standard: main selector as INPUTS manager
        if ( main_sel_mode == 'inputs' ){
            document.getElementById("mainSelector").title = 'Source Selector';
            document.getElementById("macro_buttons").style.display = 'inline-table';
            fill_in_main_as_inputs();

        // alternative: main selector as MACROS manager
        }else{
            document.getElementById("mainSelector").title = 'Macros Launcher';
            document.getElementById("macro_buttons").style.display = 'none';
            fill_in_main_as_macros();
        }
    }

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
        var option = document.createElement("option");
        option.text = 'none';
        mySel.add(option);
    }

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

    function fill_in_LUscope_selector() {
        select_clear_options( ElementId="LUscopeSelector" );
        const mySel = document.getElementById("LUscopeSelector");
        scopes = ['input', 'album', 'track'];
        for ( i in scopes ) {
            var option = document.createElement("option");
            option.text = scopes[i];
            mySel.add(option);
        }
    }

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

    main_cside_msg = ':: pe.audio.sys :: ' + state.loudspeaker;


    // updates level cell info with ref_SPL
    document.getElementById("levelInfo").title = 'Target volume ref@' +
                                                 state.loudspeaker_ref_SPL + 'dBSPL';

    fill_in_main_selector();

    fill_in_target_selector();

    fill_in_xo_selector();

    fill_in_drc_selector();

    fill_in_LUscope_selector();

    show_peq_info();
}


function manage_main_cside(){

    // Server warnings have max prioriy
    if (aux_info.warning !== ''){
        main_cside_msg = aux_info.warning;
    }else if (state.convolver_runs==false){
        main_cside_msg = '( sleeping )';
    }else{
        if (hold_cside_msg > 0){
            hold_cside_msg -= 1;
        }else{
            main_cside_msg = '::pe.audio.sys:: ' + state.loudspeaker;
        }
    }
    document.getElementById("main_cside").innerText = main_cside_msg;
}


function page_initiate(){

    function download_drc_graphs(){
        if (web_config.show_graphs==false){
            return;
        }
        // geat all drc_xxxx.png at once at start, so them will remain in cache.
        const drc_sets = JSON.parse( control_cmd('preamp get_drc_sets') );
        for (i in drc_sets){
            document.getElementById("drc_img").src =  'images/'
                                                    + state.loudspeaker
                                                    + '/drc_' + drc_sets[i]
                                                    + '.png';


        }
        document.getElementById("drc_img").src =  'images/'
                                                + state.loudspeaker
                                                + '/drc_none.png';
    }


    function download_web_config(){
        try{
            web_config      = JSON.parse( control_cmd('aux get_web_config') );
            main_sel_mode   = web_config.main_selector;
            mFnames         = web_config.user_macros;
            if (web_config.show_graphs==false){
                document.getElementById( "button_toggleEQgraphs").style.display = "none";
            }
        }catch(e){
            console.log('problems with \'aux get_web_config\' command', e.name, e.message);
        }
    }


    function show_hide_LU_frame(){
        if ( web_config.hide_LU == true ){
            document.getElementById("LU_offset").style.display = 'none';
            document.getElementById("LU_monitor").style.display = 'none';
        }else{
            document.getElementById("LU_offset").style.display = 'block';
            if ( web_config.LU_monitor_enabled == true ){
                document.getElementById("LU_monitor").style.display = 'block';
            }
        }
    }


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
                                  "oc_run_macro(\'" + mFname + "\')" );
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


    download_web_config();

    state_update();

    download_drc_graphs();

    manage_main_cside();

    fill_in_macro_buttons();

    fill_in_playlists_selector();

    show_hide_LU_frame();

    // SCHEDULES THE PAGE_UPDATE (only runtime variable items):
    // Notice: the function call inside setInterval uses NO brackets)
    setInterval( page_update, AUTO_UPDATE_INTERVAL );
}


function page_update() {

    function player_all_update(){


        function player_random_mode_update(mode){
            if        ( mode=='on' ) {
                document.getElementById("random_toggle_button").style.background  = "rgb(185, 185, 185)";
                document.getElementById("random_toggle_button").style.color       = "white";

            } else {
                document.getElementById("random_toggle_button").style.background  = "rgb(100, 100, 100)";
                document.getElementById("random_toggle_button").style.color       = "lightgray";
            }
        }


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


        try{
            var player_all_info = JSON.parse( control_cmd('player get_all_info') );
            if (player_all_info == "null"){
                main_cside_msg = ':: pe.audio.sys :: players OFFLINE';
                return;
            }
        }catch(e){
            console.log( 'error getting player info', e.name, e.message );
            return;
        }

        player_controls_update(     player_all_info.state       );
        player_metadata_update(     player_all_info.metadata    );
        player_random_mode_update(  player_all_info.random_mode );

        // Updates tracks list if disc has changed
        if (last_disc != player_all_info.discid) {
            fill_in_track_selector();
            last_disc = player_all_info.discid;
        }

        // Updates the playlist loader when input source changed, keep hidden if empty.
        if (last_input != state.input){
            const plists = fill_in_playlists_selector();
            if ( plists.length > 0 ) {
                document.getElementById( "playlist_selector").style.display = "inline";
            }else{
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


    function aux_info_refresh(){
        try{
            aux_info  = JSON.parse( control_cmd('aux info') );
        }catch(e){
            console.log('problems with \'aux info\' command', e.name, e.message);
        }
        if ( aux_info.amp == 'off' || aux_info.amp == 'on' ) {
            document.getElementById("OnOffButton").innerText = aux_info.amp.toUpperCase();
            document.getElementById("OnOffButton").style.display = 'block';
        }else{
            document.getElementById("OnOffButton").style.display = 'none';
        }
    }


    function LU_update(){
        // Updates the LU offset slider
        document.getElementById("LU_slider").value           = (15 - state.lu_offset);
        document.getElementById("LU_offset_value").innerText =
                                            'LU offset: ' + -1 * state.lu_offset;
        // Updates the Integrated LU monitor
        const LU_I  = aux_info.loudness_monitor.LU_I
        let scope   = aux_info.loudness_monitor.scope
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
    }


    function graphs_update(){

        function eq_changed(){
            // evaluates if the set of params that determines an eq curve contour has changed
            let result = false;
            const eq_params = { 'level':    state.level,    'eq_loud':  state.equal_loudness,
                                'bass':     state.bass,     'treb':     state.treble,
                                'target':   state.target
                            };
            if ( JSON.stringify(eq_params) !== JSON.stringify(last_eq_params) ) {
                //console.log('eq changed');
                last_eq_params = eq_params;
                result = true;
            }else{
                result = false;
            }
            return result
        }


        function drc_changed(){
            let result = false;
            if ( state.drc_set !== last_drc ) {
                //console.log('drc changed');
                last_drc = state.drc_set;
                result = true;
            }else{
                result = false;
            }
            return result
        }


        if ( hide_graphs == false ) {
            if (eq_changed() == true) {
                // Artifice to avoid using cached image by adding an offset timestamp
                // inside the  http.GET image source request
                document.getElementById("bfeq_img").src = 'images/brutefir_eq.png?'
                                                          + Math.floor(Date.now()/3000);
            }
            if (drc_changed() == true) {
                // Here we can use cached images because drc graphs does not change
                document.getElementById("drc_img").src =  'images/'
                                                        + state.loudspeaker
                                                        + '/drc_' + state.drc_set
                                                        + '.png';
            }
        }
    }


    function preamp_refresh(){
        // Updates level, balance, tone and delay info
        document.getElementById("levelInfo").innerHTML  = state.level.toFixed(1);
        document.getElementById("balInfo").innerHTML    = 'BAL: '  + state.balance;
        document.getElementById("bassInfo").innerText   = 'BASS: ' + state.bass;
        document.getElementById("trebleInfo").innerText = 'TREB: ' + state.treble;
        document.getElementById("buttAOD").innerText = state.extra_delay + ' ms';

        // Delete level info if convolver off
        if (state.convolver_runs == false){
            document.getElementById("levelInfo").innerHTML  = '--';
        }

        // Updates current INPUTS, XO, DRC, and TARGET (PEQ is meant to be static)
        if ( main_sel_mode == 'macros' ){
            const mName = aux_info.last_macro;
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
        toneDefeatHighlight()
        buttonSubsonicHighlight()
        buttonAODHighlight()
        levelInfoHighlight()

        // Used by the delay toggle button
        if (state.extra_delay !== 0) {
            last_delay = state.extra_delay;
        }
    }


    function player_controls_clear() {
        document.getElementById("buttonStop").style.background  = "rgb(100, 100, 100)";
        document.getElementById("buttonStop").style.color       = "lightgray";
        document.getElementById("buttonPause").style.background = "rgb(100, 100, 100)";
        document.getElementById("buttonPause").style.color      = "lightgray";
        document.getElementById("buttonPlay").style.background  = "rgb(100, 100, 100)";
        document.getElementById("buttonPlay").style.color       = "lightgray";
    }


    function player_info_clear() {
        document.getElementById("bitrate").innerText = "-\nkbps"
        document.getElementById("artist").innerText = "-"
        document.getElementById("track_info").innerText = "-"
        document.getElementById("track_info").innerText += "\n-"
        document.getElementById("time").innerText = "-"
        document.getElementById("album").innerText = "-"
        document.getElementById("title").innerText = "-"
    }


    state_update();

    // Cancel updating if not connected
    if (!server_available){
        document.getElementById("levelInfo").innerHTML  = '--';
        document.getElementById("main_cside").innerText = ':: pe.audio.sys :: not connected';
        player_info_clear();
        player_controls_clear();
        return;
    }

    // Refresh static stuff if loudspeaker's audio processes has changed
    if ( last_loudspeaker != state.loudspeaker ){
        fill_in_page_statics();
        last_loudspeaker = state.loudspeaker;
    }

    preamp_refresh();

    player_all_update();

    aux_info_refresh();

    LU_update();

    graphs_update();

    manage_main_cside();

}



//////// AUDIO 'onchange' 'onmousedown' page handlers ////////

function oc_main_select(itemName){
    // (i) The main selector can have two flavors:
    //      - regular input selector management
    //      - alternative macros management

    // helper for macros manager behavior
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

    hold_cside_msg = 3;
    main_cside_msg = 'Please wait for "' + itemName + '"';

    // (i) The arrow syntax '=>' fails on Safari iPad 1 (old version)
    // setTimeout( () => { control_cmd('input ' + itemName); }, 200 );
    function tmp(itemName){
        // regular behavior managing preamp inputs
        if ( main_sel_mode == 'inputs' ){
            control_cmd('input ' + itemName);
        // alternative behavior managing macros
        }else{
            mName = find_macroName(itemName);
            control_cmd( 'aux run_macro ' + mName );
        }
    }
    setTimeout( tmp, 200, itemName );  // 'itemName' is given as argument for 'tmp'

    clear_highlighteds();
    document.getElementById('mainSelector').style.color = "white";

}


function oc_drc_select(drcName){
    control_cmd('set_drc ' + drcName);
    clear_highlighteds();
    document.getElementById('drcSelector').style.color = "white";
}


function oc_xo_select(xoName){
    control_cmd('set_xo ' + xoName);
    clear_highlighteds();
    document.getElementById('xoSelector').style.color = "white";
}


function oc_target_select(xoName){
    control_cmd('set_target ' + xoName);
    clear_highlighteds();
    document.getElementById('targetSelector').style.color = "white";
}


function oc_LU_scope_select(scope){
    control_cmd('aux set_loudness_monitor_scope ' + scope);
    clear_highlighteds();
    document.getElementById('LUscopeSelector').style.color = "white";
}


function omd_audio_change(param, value) {
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


function omd_mute_toggle() {
    state.muted = ! state.muted;
    buttonMuteHighlight();
    control_cmd( 'mute toggle' );
}


function omd_equal_loudness_toggle() {
    state.equal_loudness = ! state.equal_loudness;
    buttonLoudHighlight();
    control_cmd( 'equal_loudness toggle' );
}


function omd_mono_toggle() {
    if (state.midside == "mid" || state.midside == "side"){
        state.midside = "off";
    }else{
        state.midside = "mid";
    }
    buttonMonoHighlight();
    control_cmd( 'mono toggle' );
}


function omd_delay_toggle() {
    if (state.extra_delay !== 0) {
        control_cmd('preamp add_delay 0');
    }else{
        control_cmd('preamp add_delay ' + last_delay.toString());
    }
}

//////// PLAYER 'onchange' 'onmousedown' 'onclick' page handlers ////////

function omd_playerCtrl(action) {
    if (action == 'random_toggle') {
        control_cmd( 'player random_mode toggle' );
    } else {
        control_cmd( 'player ' + action );
    }
}


function oc_load_playlist(plistname) {
    if (plistname == '-CLEAR-') {
        control_cmd( 'player clear_playlist ' );
    } else if (plistname != '--') {
        control_cmd( 'player clear_playlist ' );
        control_cmd( 'player load_playlist ' + plistname );
    }
}


function omd_select_track_number_dialog() {
    var tracknum = prompt('Enter track number to play:');
    if ( true ) {
        control_cmd( 'player play_track ' + tracknum );
    }
}


function oc_play_track_number(N) {
    control_cmd( 'player play_track ' + N );
    hold_selected_track = 10;
}


function ck_play_url() {
    var url = prompt('Enter url to play:');
    if ( url.slice(0,5) == 'http:' || url.slice(0,6) == 'https:' ) {
        control_cmd( 'aux play_url ' + url );
    }
}



//////// AUX 'onmousedown' 'onclick' 'oninput' page handlers ////////

function ck_peaudiosys_restart() {
    control_cmd('peaudiosys_restart');
    ck_display_advanced('off');
    page_update();
}


function omd_ampli_set(mode) {
    control_cmd( 'aux amp_switch ' + mode );
}


function oi_LU_slider_action(slider_value){
    control_cmd( 'lu_offset ' + (15 - parseInt(slider_value) ).toString() )
}


function oc_run_macro(mFname){

    function highlight_macro_button(id){
        document.getElementById(id).className = 'macro_button_highlighted';
    }


    control_cmd( 'aux run_macro ' + mFname );

    var mName = mFname.slice(mFname.indexOf('_') + 1, mFname.length);
    clear_highlighteds();

    // (i) The arrow syntax '=>' fails on Safari iPad 1 (old version)
    // setTimeout(() => { highlight_macro_button(mName);}, 200);
    function tmp(mName){
        highlight_macro_button(mName);
    }
    setTimeout( tmp, 200, mName );  // 'mName' is given as argument for 'tmp'

    hold_cside_msg = 3;
    main_cside_msg = 'Please wait for "' + mName + '"' ;
}


function omd_macro_buttons_display_toggle() {
    var curMode = document.getElementById( "macro_buttons").style.display;
    if (curMode == 'none') {
        document.getElementById( "macro_buttons").style.display = 'inline-table'
        main_sel_mode = 'inputs';
    }
    else {
        document.getElementById( "macro_buttons").style.display = 'none'
        main_sel_mode = 'macros';
    }
    fill_in_page_statics();
}


function ck_display_advanced(mode) {
    // (i) This also allows access to the RESTART buttons

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
        document.getElementById( "div_advanced_controls").style.display = "block";
        document.getElementById( "level_buttons13").style.display = "table-cell";
        document.getElementById( "main_lside").style.display = "table-cell";
        document.getElementById( "buttAOD").style.display = "inline-block";
        document.getElementById( "subsonic").style.display = "inline-block";
        document.getElementById( "tone_defeat").style.display = "inline-block";
    }
    else {
        document.getElementById( "div_advanced_controls").style.display = "none";
        document.getElementById( "level_buttons13").style.display = "none";
        document.getElementById( "main_lside").style.display = "none";
        if ( state.extra_delay === 0 ) {
            document.getElementById( "buttAOD").style.display = "none";
        }
        document.getElementById( "subsonic").style.display = "none";
        document.getElementById( "tone_defeat").style.display = "none";
    }
}


function omd_graphs_toggle() {
    if ( web_config.show_graphs == false ){
        return;
    }
    if ( hide_graphs == true ) {
        hide_graphs = false;
    }
    else {
        hide_graphs = true;
    }

    if ( hide_graphs == false ){
        document.getElementById("drc_graph").style.display = 'block';
        document.getElementById("bfeq_graph").style.display = 'block';
    }else{
        document.getElementById("drc_graph").style.display = 'none';
        document.getElementById("bfeq_graph").style.display = 'none';
    }
}



////////  MISCEL INTERNALS

function control_cmd( cmd ) {
    // Communicate with the pe.audio.sys server through the php socket

    /*
    We need synchronous mode (async=false), althougt it is deprecated
    and not recommended in the main JS thread.
    https://developer.mozilla.org/en/docs/Web/API/XMLHttpRequest
    https://developer.mozilla.org/en-US/docs/Web/API/XMLHttpRequest/Using_XMLHttpRequest
    https://developer.mozilla.org/en-US/docs/Web/API/XMLHttpRequest/Synchronous_and_Asynchronous_Requests
    */


    function http_prepare(x) {
        // Avoid http socket lossing some symbols

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


function state_update() {
    try{
        state = JSON.parse( control_cmd('preamp state') );
        server_available = true;
    }catch(e){
        server_available = false;
        document.getElementById("main_cside").innerText =
                                        ':: pe.audio.sys :: not connected';
        console.log( 'not connected', e.name, e.message );
    }
    if (server_available){
        document.title = 'pe.audio.sys ' + state.loudspeaker;
    }
}


function fill_in_playlists_selector() {

    // getting playlists
    var plists = [];
    try{
        plists = JSON.parse( control_cmd( 'player get_playlists' ) );
    }catch(e){
        console.log( e.name, e.message );
        return plists;
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

    return plists
}


function select_clear_options(ElementId){
    // https://www.w3schools.com/jsref/dom_obj_select.asp
    var mySel = document.getElementById(ElementId);
    while (mySel.length > 0){
        mySel.remove( mySel.length-1 );
    }
}


function clear_highlighteds(){
    for (i = 0; i < macro_button_list.length; i++) {
        document.getElementById(macro_button_list[i]).className = 'macro_button';
    }
    document.getElementById('mainSelector').style.color     = "rgb(200,200,200)";
    document.getElementById('drcSelector').style.color      = "rgb(200,200,200)";
    document.getElementById('xoSelector').style.color       = "rgb(200,200,200)";
    document.getElementById('targetSelector').style.color   = "rgb(200,200,200)";
}


function toneDefeatHighlight(){
    if (state.tone_defeat){
        document.getElementById("tone_defeat").style.border = "3px solid rgb(160, 160, 160)";
        document.getElementById("tone_defeat").style.background = "rgb(100, 0, 0)";
        document.getElementById("tone_defeat").style.color = "rgb(255, 200, 200)";
        document.getElementById("bassInfo").style.color = "grey";
        document.getElementById("trebleInfo").style.color = "grey";
    }else{
        document.getElementById("tone_defeat").style.border = "2px solid rgb(100, 100, 100)";
        document.getElementById("tone_defeat").style.background = "rgb(100, 100, 100)";
        document.getElementById("tone_defeat").style.color = "rgb(180, 180, 180)";
        document.getElementById("bassInfo").style.color = "white";
        document.getElementById("trebleInfo").style.color = "white";
    }
}

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

function buttonAODHighlight(){
    if ( state.extra_delay === 0 ) {
        document.getElementById("buttAOD").style.border = "2px solid rgb(100, 100, 100)";
        document.getElementById("buttAOD").style.background = "rgb(100, 100, 100)";
        document.getElementById("buttAOD").style.color = "rgb(180, 180, 180)";
    } else {
        document.getElementById("buttAOD").style.border = "3px solid rgb(160, 160, 160)";
        document.getElementById("buttAOD").style.background = "rgb(100, 0, 0)";
        document.getElementById("buttAOD").style.color = "rgb(255, 200, 200)";
        document.getElementById("buttAOD").style.display = 'inline-table';
    }
}

function buttonSubsonicHighlight(){
    if ( state.subsonic == 'off' ) {
        document.getElementById("subsonic").style.border = "2px solid rgb(100, 100, 100)";
        document.getElementById("subsonic").style.background = "rgb(100, 100, 100)";
        document.getElementById("subsonic").style.color = "rgb(180, 180, 180)";
        document.getElementById("subsonic").innerText = 'SUBS\n-';
    } else if ( state.subsonic == 'mp' ) {
        document.getElementById("subsonic").style.border = "3px solid rgb(160, 160, 160)";
        document.getElementById("subsonic").style.background = "rgb(100, 0, 0)";
        document.getElementById("subsonic").style.color = "rgb(255, 200, 200)";
        document.getElementById("subsonic").innerText = 'SUBS\nmp';
    } else if ( state.subsonic == 'lp' ) {
        document.getElementById("subsonic").style.border = "3px solid rgb(160, 160, 160)";
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
