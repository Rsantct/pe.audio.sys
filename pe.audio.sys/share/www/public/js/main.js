/*
    Copyright (c) Rafael Sánchez
    This file is part of 'pe.audio.sys'
    'pe.audio.sys', a PC based personal audio system.
*/

import * as mc from './miscel.js';

const AUTO_UPDATE_INTERVAL = 1000;      // Auto-update interval millisec

//////// GLOBAL VARIABLES ////////
var state               = {};
var server_available    = false;

var player_info         = {};

var aux_info            = { 'amp': 'n/a',
                            'loudness_monitor': {'LU_I': 0, 'LU_M': 0, 'scope': 'track' },
                            'last_macro': '',
                            'warning': ''
};

var web_config          = { 'main_selector':      'inputs',
                            'hide_LU':            false,
                            'LU_monitor_enabled': false,
                            'show_graphs':        false,
                            'user_macros':        [],
                            'lspk_sample_rates':  []
};

var main_sel_mode       = web_config.main_selector;

var mFnames             = web_config.user_macros; // Macro file names

var macro_button_list   = [];

var metablank           = {         // A player's metadata blank dict
                            'player':       '',
                            'time_pos':     '',
                            'time_tot':     '',
                            'bitrate':      '',
                            'format':       '',
                            'file':         '',
                            'artist':       '',
                            'album':        '',
                            'title':        '',
                            'track_num':    '',
                            'tracks_tot':   ''
};


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


//////// PAGE MANAGEMENT ////////

function fill_in_page_statics(){

    function fill_in_main_selector(){

        function fill_in_main_as_inputs() {
            // MAIN SELECTOR manages inputs:

            // getting input names
            try{
                var inputs = mc.send_cmd( 'get_inputs' );
            }catch(e){
                console.log( e.name, e.message );
                return;
            }
            // clearing selector options
            select_clear_options("mainSelector");
            // Filling in options in a selector
            // https://www.w3schools.com/jsref/dom_obx.length-1j_select.asp
            var mySel = document.getElementById("mainSelector");
            for ( const i in inputs) {
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
            select_clear_options("mainSelector");

            // Filling in options in a selector
            // https://www.w3schools.com/jsref/dom_obj_select.asp
            var mySel = document.getElementById("mainSelector");
            for ( const i in mFnames) {
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
            var xo_sets = mc.send_cmd( 'get_xo_sets' );
        }catch(e){
            console.log( e.name, e.message );
            return;
        }
        select_clear_options("xoSelector");
        const mySel = document.getElementById("xoSelector");
        for ( const i in xo_sets ) {
            var option = document.createElement("option");
            option.text = xo_sets[i];
            mySel.add(option);
        }
    }


    function fill_in_drc_selector() {
        try{
            var drc_sets = mc.send_cmd( 'get_drc_sets');
        }catch(e){
             console.log( e.name, e.message );
           return;
        }
        select_clear_options("drcSelector");
        const mySel = document.getElementById("drcSelector");
        for ( const i in drc_sets ) {
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
            var target_files = mc.send_cmd( 'get_target_sets' );
        }catch(e){
            console.log( e.name, e.message );
            return;
        }
        select_clear_options("targetSelector");
        const mySel = document.getElementById("targetSelector");
        for ( const i in target_files ) {
            var option = document.createElement("option");
            option.text = target_files[i];
            mySel.add(option);
        }
    }


    function fill_in_LUscope_selector() {
        select_clear_options("LUscopeSelector");
        const mySel = document.getElementById("LUscopeSelector");
        const scopes = ['input', 'album', 'track'];
        for ( const i in scopes ) {
            var option = document.createElement("option");
            option.text = scopes[i];
            mySel.add(option);
        }
    }


    function fill_in_samplerateSelector(){

        select_clear_options("samplerateSelector");

        const mySel = document.getElementById("samplerateSelector");

        for ( const i in web_config.lspk_sample_rates ) {
            var option = document.createElement("option");
            option.text = web_config.lspk_sample_rates[i];
            mySel.add(option);
        }
        mySel.value = state.fs;
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

    fill_in_samplerateSelector();

}


async function init(){

    function download_drc_graphs(){
        if (web_config.show_graphs==false){
            return;
        }
        // geat all drc_xxxx.png at once at start, so them will remain in cache.
        const drc_sets = mc.send_cmd('preamp get_drc_sets');
        for (const i in drc_sets){
            document.getElementById("drc_img").src =  'images/'
                                                    + state.loudspeaker
                                                    + '/drc_' + drc_sets[i]
                                                    + '.png';


        }
        document.getElementById("drc_img").src =  'images/'
                                                + state.loudspeaker
                                                + '/drc_none.png';
    }


    function update_web_config(){

        const tmp = mc.send_cmd('aux get_web_config');

        // bad response
        if ( !tmp.user_macros ){
            return false
        }

        web_config = tmp;

        if (document.body.getAttribute('data-layout') == 'landscape'){
            main_sel_mode = 'macros'
        }else{
            main_sel_mode = web_config.main_selector;
        }

        mFnames = web_config.user_macros;

        if (web_config.show_graphs == false){
            document.getElementById("bt_toggle_eq_graphs").style.display = "none";
        }

        return true
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

        if ( mFnames.length == 0 ){
            console.log( '(i) empty macros array')
            document.getElementById( "macro_buttons").style.display = 'none';
            return
        }

        document.getElementById( "bt_macros_toggle").style.display = 'inline';


        // Expands number of buttons to a multiple of 3 (arrange of Nx3 buttons)
        // (i) mFnames is supposed to be properly sorted.
        var bTotal = parseInt(mFnames[mFnames.length - 1].split('_')[0])
        bTotal = 3 * ( Math.floor( (bTotal - 1) / 3) + 1 )

        var mtable = document.getElementById("macro_buttons");
        var row  = mtable.insertRow(-1); // at index -1

        // Iterate over button available cells
        for (let butPos = 1; butPos <= bTotal; butPos++) {

            let mFname   = '';
            let macroPos = '';
            let mName    = '';

            // Iterate over macro filenames to locate the matching with butPos
            let found = false;
            for (const i in mFnames) {
                // Macro file names: 'N_macro_name' where N is the button position
                mFname = mFnames[i];
                macroPos  = mFname.split('_')[0];
                mName = mFname.slice(mFname.indexOf('_') + 1, mFname.length);

                if ( macroPos == butPos ){
                    found = true;
                    break;
                }
            };


            // Insert a cell
            var cell = row.insertCell(-1); // at index -1
            cell.className = 'macro_cell';

            // Create a button Element
            const btn = document.createElement('button');
            btn.type = "button";
            btn.className = "macro_button";

            if ( found == true ){
                btn.id = mName;
                btn.innerHTML = mName;
                btn.addEventListener('click', () => oc_run_macro(mFname));

            }else{
                btn.innerHTML = '-';
            }

            cell.appendChild(btn);

            // Arrange 3 buttons per row
            if ( butPos % 3 == 0 ) {
                row  = mtable.insertRow(-1); // at index -1
            }
        }
    }



    mc.do_until_function_istrue( update_web_config )

    fill_in_macro_buttons();

    mc.do_until_function_istrue( update_state )

    download_drc_graphs();

    manage_main_cside();

    fill_in_playlists_selector( get_playlists() );

    show_hide_LU_frame();

    setInterval( page_update, AUTO_UPDATE_INTERVAL );
}


function page_update() {

    function player_get(){
        try{
            const tmp = mc.send_cmd('player get_all_info');
            if (tmp != "null"){
                player_info = tmp;
            }else{
                main_cside_msg = ':: pe.audio.sys :: players OFFLINE';
                return;
            }
        }catch(e){
            console.log( 'response error to player get_all_info', e.message );
            return;
        }
    }


    function player_refresh(){

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
                document.getElementById("bt_stop").style.background  = "rgb(185, 185, 185)";
                document.getElementById("bt_stop").style.color       = "white";
                document.getElementById("bt_pause").style.background = "rgb(100, 100, 100)";
                document.getElementById("bt_pause").style.color      = "lightgray";
                document.getElementById("bt_play").style.background  = "rgb(100, 100, 100)";
                document.getElementById("bt_play").style.color       = "lightgray";
            } else if ( playerState == 'pause' ){
                document.getElementById("bt_stop").style.background  = "rgb(100, 100, 100)";
                document.getElementById("bt_stop").style.color       = "lightgray";
                document.getElementById("bt_pause").style.background = "rgb(185, 185, 185)";
                document.getElementById("bt_pause").style.color      = "white";
                document.getElementById("bt_play").style.background  = "rgb(100, 100, 100)";
                document.getElementById("bt_play").style.color       = "lightgray";
            } else if ( playerState == 'play' ) {
                document.getElementById("bt_stop").style.background  = "rgb(100, 100, 100)";
                document.getElementById("bt_stop").style.color       = "lightgray";
                document.getElementById("bt_pause").style.background = "rgb(100, 100, 100)";
                document.getElementById("bt_pause").style.color      = "lightgray";
                document.getElementById("bt_play").style.background  = "rgb(185, 185, 185)";
                document.getElementById("bt_play").style.color       = "white";
            }
        }


        function player_metadata_update(d) {

            if ( d['artist'] == ''  && d['album'] == '' && d['title'] == '' ){
                d = metablank;
            }

            if (d['format']) {
                document.getElementById("format").innerText = d['format'];
            } else {
                document.getElementById("format").innerText = "-:-:2"
            }
            if (d['file']) {
                document.getElementById("file").innerText = d['file'];
            } else {
                document.getElementById("file").innerText = "-"
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
                if (d['time_tot']){
                    document.getElementById("time").innerText    = "-\n" + d['time_tot'];
                } else {
                    document.getElementById("time").innerText = "-"
                }
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


        if (!player_info.state){
            console.log('bad player_info');
            return
        }

        player_controls_update(     player_info.state       );
        player_metadata_update(     player_info.metadata    );
        player_random_mode_update(  player_info.random_mode );

        // Updates tracks list if disc has changed
        if (last_disc != player_info.discid) {
            fill_in_track_selector();
            last_disc = player_info.discid;
        }

        // Updates the playlist loader when input source changed, keep hidden if empty.
        if (last_input != state.input){
            const plists = get_playlists();
            if ( plists.length > 0 ) {
                fill_in_playlists_selector( plists );
                document.getElementById( "playlist_selector").style.display = "inline";
            }else{
                document.getElementById( "playlist_selector").style.display = "none";
            }
            last_input = state.input;
        }

        // Displays the track selector if input == 'cd'
        if ( state.input == "cd") {
            document.getElementById( "track_selector").style.display = "inline";
            document.getElementById( "playlist_selector").style.display = "none";
        }
        else {
            document.getElementById( "track_selector").style.display = "none";
            document.getElementById( "playlist_selector").style.display = "inline";
        }

        // Clears the CD track selector when expired
        hold_selected_track -= 1;
        if (hold_selected_track == 0) {
            document.getElementById('track_selector').value = '--';
        }

        // Displays the [url] button if input == 'url'
        if (state.input == "url") {
            document.getElementById( "bt_url").style.display = "inline";
            document.getElementById( "track_selector").style.display = "none";
            document.getElementById( "playlist_selector").style.display = "none";
        }
        else {
            document.getElementById( "bt_url").style.display = "none";
        }

        // Hide "15 min / 5 min" buttons on track length
        const time_tot = player_info.metadata.time_tot.padStart(8,'00:');

        if ( time_tot.includes(':') && ! time_tot.includes('-')){

            if ( time_tot > '00:30:00' ){

                document.getElementById( "playback_control_02" ).style.display = "table-cell";

                if ( time_tot > '01:00:00' ){
                    document.getElementById( "bt_-15min" ).style.display = "inline-block";
                    document.getElementById( "bt_+15min" ).style.display = "inline-block";
                }else{
                    document.getElementById( "bt_-15min" ).style.display = "none";
                    document.getElementById( "bt_+15min" ).style.display = "none";
                }

            }else{
                document.getElementById( "playback_control_02" ).style.display = "none";
            }
        }
    }


    function aux_info_get(){

        let tmp = mc.send_cmd('aux info');

        if (tmp.amp) {
            aux_info = tmp

        }else{
            tmp = mc.send_cmd('amp_switch state');

            if (typeof tmp == 'string') {
                aux_info.amp = tmp
            }
        }
    }


    function aux_info_refresh(){

        if (!aux_info.amp){
            return
        }

        if ( aux_info.amp == 'off' || aux_info.amp == 'on' ) {
            document.getElementById("bt_onoff").innerText = aux_info.amp.toUpperCase();
            document.getElementById("bt_onoff").style.display = 'block';

        }else{
            document.getElementById("bt_onoff").style.display = 'none';
        }

        if ( ! aux_info.last_macro ){
            clear_macro_buttons_highlight();

        }else{
            const x = aux_info.last_macro;
            const mName = x.slice(x.indexOf('_') + 1, x.length);
            clear_macro_buttons_highlight();
            highlight_macro_button(mName)
        }

        if (aux_info.sysmon) {
            // sysmon
            // Example when wifi is not conneted:
            //  "sysmon": {"wifi": {"Tx-Power": "12"}, "temp": 69.2}}
            //
            let sysmon = '';
            const temp = aux_info.sysmon.temp
            const wifi = aux_info.sysmon.wifi
            const fan1 = aux_info.sysmon.fans.fan1
            const fan2 = aux_info.sysmon.fans.fan2
            const fan3 = aux_info.sysmon.fans.fan3

            let fans = ''
            if (fan1){
                fans += fan1
            }
            if (fan2){
                fans += ',' + fan2
            }
            if (fan3){
                fans += ',' + fan3
            }

            if (temp){
                sysmon += 'temp: ' + temp + 'º';
            }

            if (fans){
                sysmon += ' | fan: ' + fans + ' rpm';
            }

            if (! isEmpty(wifi)){
                if ('Bit-rate-Mb/s' in wifi){
                    sysmon += ' | wifi: ' + wifi['Bit-rate-Mb/s'] + ' Mb/s';
                    sysmon += ' quality: ' + wifi['Quality'];
                    sysmon += ' Rx: ' + wifi['Signal-level'] + ' dBm';
                }else{
                    sysmon += ' | wifi: ' + wifi['iface'] + ' (not connected)';
                }
            }

            document.getElementById("sysmon").innerText = sysmon;
        }
    }


    function LU_refresh(){
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
        // The temporary 'new_eq_graph' flag helps on slow machines because the new PNG graph
        // can take a while after the 'done' is received when issuing some audio command.
            if (eq_changed() == true || aux_info.new_eq_graph == true) {
                // Artifice to avoid using cached image by adding an offset timestamp
                // inside the  http.GET image source request
                document.getElementById("bfeq_img").src = 'images/brutefir_eq.png?'
                                                          + Math.floor(Date.now());
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


    function state_refresh(){
        // Updates level, balance, tone and delay info
        document.getElementById("levelInfo").innerHTML  = state.level.toFixed(1);
        document.getElementById("balInfo").innerHTML    = 'BAL: '  + state.balance;
        document.getElementById("bassInfo").innerText   = 'BASS: ' + state.bass;
        document.getElementById("trebleInfo").innerText = 'TREB: ' + state.treble;
        document.getElementById("bt_aod").innerText = state.extra_delay + ' ms';

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
        bt_muteHighlight()
        bt_monoHighlight()
        bt_soloHighlight()
        bt_polarityHighlight()
        bt_loudHighlight()
        buttonsToneBalanceHighlight()
        toneDefeatHighlight()
        buttonSubsonicHighlight()
        buttonAODHighlight()
        buttonSwapLRHighlight()
        buttonCompressorHighlight()
        levelInfoHighlight()

        // Used by the delay toggle button
        if (state.extra_delay !== 0) {
            last_delay = state.extra_delay;
        }
    }


    function player_controls_clear() {
        document.getElementById("bt_stop").style.background  = "rgb(100, 100, 100)";
        document.getElementById("bt_stop").style.color       = "lightgray";
        document.getElementById("bt_pause").style.background = "rgb(100, 100, 100)";
        document.getElementById("bt_pause").style.color      = "lightgray";
        document.getElementById("bt_play").style.background  = "rgb(100, 100, 100)";
        document.getElementById("bt_play").style.color       = "lightgray";
    }


    function player_info_clear() {
        document.getElementById("file").innerText = "-"
        document.getElementById("format").innerText = "-:-:2"
        document.getElementById("bitrate").innerText = "-\nkbps"
        document.getElementById("artist").innerText = "-"
        document.getElementById("track_info").innerText = "-"
        document.getElementById("track_info").innerText += "\n-"
        document.getElementById("time").innerText = "-"
        document.getElementById("album").innerText = "-"
        document.getElementById("title").innerText = "-"
    }


    function show_peq_info() {

        if ( aux_info.peq_set != 'none'){

            document.getElementById("bt_peq").innerHTML = "PEQ: " + aux_info.peq_set;

            if (allAreTrue(aux_info.peq_bypassed)){
                document.getElementById("bt_peq").style.color = "grey";
            }else{
                document.getElementById("bt_peq").style.color = "white";
            }

        }else {
            document.getElementById("bt_peq").style.color = "grey";
            document.getElementById("bt_peq").innerHTML = "(no peq)";
        }
    }



    aux_info_get();
    aux_info_refresh();

    server_available = update_state();

    if (! server_available){
        document.getElementById("levelInfo").innerHTML  = '--';
        document.getElementById("main_cside").innerText = ':: pe.audio.sys :: not connected';
        player_info_clear();
        player_controls_clear();
        return;
    }

    if ( last_loudspeaker != state.loudspeaker ){
        fill_in_page_statics();
        last_loudspeaker = state.loudspeaker;
    }

    state_refresh();

    player_get();
    player_refresh();

    LU_refresh();

    graphs_update();

    manage_main_cside();

    show_peq_info();
}


////////  MISCEL INTERNALS  ////////

function update_state() {

    const tmp = mc.send_cmd('preamp state');

    if (tmp.loudspeaker){
        state = tmp;
        server_available = true;
        document.title = 'pe.audio.sys ' + state.loudspeaker;
        return true

    }else{
        server_available = false;
        document.getElementById("main_cside").innerText = ':: pe.audio.sys :: not connected';
        return false
    }
}


function manage_main_cside(){

    // Server warnings have max prioriy
    if (aux_info.warning !== ''){
        main_cside_msg = aux_info.warning;
    }else if (state.convolver_runs==false){
        main_cside_msg = state.loudspeaker + ' ( sleeping )';
    }else{
        if (hold_cside_msg > 0){
            hold_cside_msg -= 1;
        }else{
            if (state.drc_set == 'none'){
                main_cside_msg = state.loudspeaker;
            }else{
                main_cside_msg = state.loudspeaker + ' (' + state.drc_set + ')';
            }
        }
    }
    document.getElementById("main_cside").innerText = main_cside_msg;
}


function get_playlists() {

    var plists = [];
    try{
        plists = mc.send_cmd( 'player get_playlists' );
    }catch(e){
        console.log( 'response error to \'get_playlists\'', e.message );
    }
    return plists;
}


function get_playlist() {

    var playlist = [];
    try{
        playlist = mc.send_cmd( 'player get_playlist' );
    }catch(e){
        console.log( e.name, e.message );
    }
    return playlist
}


function get_cd_track_nums() {

    var tracks = [];
    try{
        tracks = mc.send_cmd( 'player get_cd_track_nums' );
    }catch(e){
        console.log( e.name, e.message );
    }
    return tracks
}


function fill_in_playlists_selector(plists) {

    // clearing selector options
    select_clear_options("playlist_selector");

    // Filling in options in a selector
    // https://www.w3schools.com/jsref/dom_obx.length-1j_select.asp
    var mySel = document.getElementById("playlist_selector");
    var option = document.createElement("option");
    option.text = '--';
    mySel.add(option);
    for ( const i in plists) {
        var option = document.createElement("option");
        option.text = plists[i];
        mySel.add(option);
    }
    var option = document.createElement("option");
    option.text = '-CLEAR-';
    mySel.add(option);
}


function fill_in_track_selector() {

    // This get the track numbers
    //const tracks = get_cd_track_nums();

    // This gets the track numbers and titles
    const tracks = get_playlist();

    // clearing selector options
    select_clear_options("track_selector");
    // Filling in options in a selector
    // https://www.w3schools.com/jsref/dom_obx.length-1j_select.asp
    var mySel = document.getElementById("track_selector");
    var option = document.createElement("option");
    option.text = '--';
    mySel.add(option);
    for ( const i in tracks) {
        var option = document.createElement("option");
        option.text = tracks[i];
        mySel.add(option);
    }
    mySel.add(option);
}


function select_clear_options(ElementId){
    // https://www.w3schools.com/jsref/dom_obj_select.asp
    var mySel = document.getElementById(ElementId);
    while (mySel.length > 0){
        mySel.remove( mySel.length-1 );
    }
}


function clear_highlighteds(){
    document.getElementById('mainSelector').style.color     = "rgb(200,200,200)";
    document.getElementById('drcSelector').style.color      = "rgb(200,200,200)";
    document.getElementById('xoSelector').style.color       = "rgb(200,200,200)";
    document.getElementById('targetSelector').style.color   = "rgb(200,200,200)";
}


function clear_macro_buttons_highlight(){
    for (let i = 0; i < macro_button_list.length; i++) {
        document.getElementById(macro_button_list[i]).className = 'macro_button';
    }
}


function allAreTrue(arr) {
  return arr.every(element => element === true);
}


function isEmpty(obj) {
    // test if some object (say a dict) is empty
    return Object.keys(obj).length === 0;
}

//////// HANDLERS: AUDIO 'onchange' 'onmousedown' ////////

function oc_main_select(itemName){
    // (i) The main selector can have two flavors:
    //      - regular input selector management
    //      - alternative macros management

    // helper for macros manager behavior
    function find_macroName(x){
        var result = '';
        for ( const i in mFnames ){
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
    // setTimeout( () => { mc.send_cmd('input ' + itemName); }, 200 );
    function tmp(itemName){
        // regular behavior managing preamp inputs
        if ( main_sel_mode == 'inputs' ){
            mc.send_cmd('input ' + itemName);
        // alternative behavior managing macros
        }else{
            mName = find_macroName(itemName);
            mc.send_cmd( 'aux run_macro ' + mName );
        }
    }
    setTimeout( tmp, 200, itemName );  // 'itemName' is given as argument for 'tmp'

    clear_macro_buttons_highlight();
    document.getElementById('mainSelector').style.color = "white";

}


function oc_drc_select(drcName){
    mc.send_cmd('set_drc ' + drcName);
    clear_highlighteds();
    document.getElementById('drcSelector').style.color = "white";
}


function oc_xo_select(xoName){
    mc.send_cmd('set_xo ' + xoName);
    clear_highlighteds();
    document.getElementById('xoSelector').style.color = "white";
}


function oc_target_select(xoName){
    mc.send_cmd('set_target ' + xoName);
    clear_highlighteds();
    document.getElementById('targetSelector').style.color = "white";
}


function omd_lu_mon_reset(elem){
    mc.flash_element( elem );
    mc.send_cmd('aux reset_loudness_monitor');
}


function oc_LU_scope_select(scope){
    mc.send_cmd('aux set_loudness_monitor_scope ' + scope);
    clear_highlighteds();
    document.getElementById('LUscopeSelector').style.color = "white";
}


function omd_audio_change(element, param, value) {

    mc.flash_element(element, 400);

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
    mc.send_cmd( param + ' ' + value + ' ' + 'add' );
}


function omd_mute_toggle(elem) {
    mc.flash_element( elem );
    mc.send_cmd( 'mute toggle' );
    state.muted = ! state.muted;
    bt_muteHighlight();
}


function omd_equal_loudness_toggle() {
    mc.send_cmd( 'equal_loudness toggle' );
    state.equal_loudness = ! state.equal_loudness;
    bt_loudHighlight();
}


function omd_mono_toggle() {

    // normal: only stereo/mono (off/mid)
    if (!show_advanced){

        if (state.midside == "mid" || state.midside == "side"){
            state.midside = "off";
            mc.send_cmd( 'midside off' );
        }else{
            state.midside = "mid";
            mc.send_cmd( 'midside mid' );
        }

    // advanced-controls: rotate stereo/mono/L-R (off/mid/side)
    }else{

        if (state.midside == "off"){
            state.midside = "mid";
            mc.send_cmd( 'midside mid' );
        }else if (state.midside == "mid"){
            state.midside = "side";
            mc.send_cmd( 'midside side' );
        }else if (state.midside == "side"){
            state.midside = "off";
            mc.send_cmd( 'midside off' );
        }
    }

    bt_monoHighlight();
}


function omd_solo_rotate() {

    if (state.solo == "off"){
        mc.send_cmd( 'solo L' );
    }else if(state.solo == "l"){
        mc.send_cmd( 'solo R' );
    }else if(state.solo == "r"){
        mc.send_cmd( 'solo off' );
    }

    // Solo highlight falls on the Mono/Stereo Button
}


function omd_polarity_rotate() {

    if (state.polarity == "++"){
        mc.send_cmd( 'polarity +-' );

    }else if(state.polarity == "+-"){
        mc.send_cmd( 'polarity -+' );

    }else if(state.polarity == "-+"){
        mc.send_cmd( 'polarity --' );

    }else if(state.polarity == "--"){
        mc.send_cmd( 'polarity ++' );

    }

    bt_polarityHighlight();
}


function omd_delay_toggle(elem) {
    mc.flash_element( elem );
    if (state.extra_delay !== 0) {
        mc.send_cmd('preamp add_delay 0');
    }else{
        mc.send_cmd('preamp add_delay ' + last_delay.toString());
    }
}


function omd_swap_lr(elem) {
    mc.flash_element( elem );
    mc.send_cmd('preamp swap_lr');
}


function omd_subsonic(elem){
    mc.flash_element( elem );
    mc.send_cmd('preamp subsonic rotate');
}


function omd_tone_defeat(elem){
    mc.flash_element( elem );
    mc.send_cmd('preamp tone_defeat toggle');
}


function omd_compressor(elem){
    mc.flash_element( elem );
    mc.send_cmd('preamp compressor rotate');
}


//////// HANDLERS: PLAYER 'onchange' 'onmousedown' 'onclick' ////////

function omd_playerCtrl(element, action) {
    mc.flash_element(element, 400);
    if (action == 'random_toggle') {
        mc.send_cmd( 'player random_mode toggle' );
    } else {
        mc.send_cmd( 'player ' + action );
    }
}


function oc_load_playlist(plistname) {
    if (plistname == '-CLEAR-') {
        mc.send_cmd( 'player clear_playlist ' );
    } else if (plistname != '--') {
        mc.send_cmd( 'player clear_playlist ' );
        mc.send_cmd( 'player load_playlist ' + plistname );
    }
}


function omd_select_track_number_dialog() {
    var tracknum = prompt('Enter track number to play:');
    if ( true ) {
        mc.send_cmd( 'player play_track ' + tracknum );
    }
}


function oc_play_track_number(N) {
    mc.send_cmd( 'player play_track ' + N );
    hold_selected_track = 10;
}


function ck_play_url() {
    var url = prompt('Enter url to play:');
    if ( url.slice(0,5) == 'http:' || url.slice(0,6) == 'https:' ) {
        mc.send_cmd( 'player play_url ' + url );
    }
}


//////// HANDLERS: AUX 'onmousedown' 'onclick' 'oninput' ////////

function oc_restart_samplerate(value){

    const s = document.getElementById("samplerateSelector");

    if ( confirm('Are you sure to restart to sampling rate: ' + value) ){
        const ans = mc.send_cmd('aux restart_to_sample_rate ' + value);
        s.value = null;
        alert(ans);

    }else{
        s.value = state.fs;
    };
}


function ck_peaudiosys_restart() {

    if ( window.confirm('Are you sure to RESTART pe.audio.sys?') ){
        mc.send_cmd('restart_peaudiosys');
        ck_display_advanced('off');
        page_update();
    }
}


function omd_ampli_switch(mode) {

    let msg = 'Please confirm to TURN OFF the amplifier';

    if ( aux_info.amp_off_shutdown ) {
        msg = 'Please confirm to POWER OFF the system';
    }

        if ( aux_info.amp.toLowerCase() == 'on' ) {

        if ( ! confirm(msg) ){
            return;
        }
    }

    mc.send_cmd( 'amp_switch ' + mode );
}


function oi_LU_slider_action(slider_value){
    mc.send_cmd( 'lu_offset ' + (15 - parseInt(slider_value) ).toString() )
}


function highlight_macro_button(id){
    document.getElementById(id).className = 'macro_button_highlighted';
}


function oc_run_macro(mFname){

    mc.send_cmd( 'aux run_macro ' + mFname );

    const mName = mFname.slice(mFname.indexOf('_') + 1, mFname.length);

    clear_macro_buttons_highlight();

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
    // (i) This also allows access to the RESTART button

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
        document.getElementById("format_file").style.display = "table-row";
        document.getElementById("div_advanced_controls").style.display = "block";
        document.getElementById("main_lside").style.display = "table-cell";
        document.getElementById("landscape").style.display = "table-cell";
        document.getElementById("sysmon").style.display = "table-cell";
        document.getElementById("SoloInfo").style.display = "table-cell";
        document.getElementById("PolarityInfo").style.display = "table-cell";
        document.getElementById("bt_aod").style.display = "inline-block";
        document.getElementById("bt_swap_lr").style.display = "inline-block";
        document.getElementById("bt_subsonic").style.display = "inline-block";
        document.getElementById("bt_tone_defeat").style.display = "inline-block";
        document.getElementById("samplerateSelector").style.display = "inline-block";
        if (web_config.use_compressor){
            document.getElementById("bt_compressor").style.display = "inline-block";
        }
    }
    else {
        document.getElementById("format_file").style.display = "none";
        document.getElementById("div_advanced_controls").style.display = "none";
        document.getElementById("main_lside").style.display = "none";
        document.getElementById("landscape").style.display = "none";
        document.getElementById("sysmon").style.display = "none";
        document.getElementById("SoloInfo").style.display = "none";
        document.getElementById("PolarityInfo").style.display = "none";
        if ( state.extra_delay === 0 ) {
            document.getElementById( "bt_aod").style.display = "none";
        }
        if ( ! state.lr_swapped ) {
            document.getElementById("bt_swap_lr").style.display = "none";

        }else{
            document.getElementById("bt_swap_lr").style.display = "inline-block";
        }
        document.getElementById("bt_subsonic").style.display = "none";
        document.getElementById("bt_tone_defeat").style.display = "none";
        document.getElementById("samplerateSelector").style.display = "none";
        document.getElementById("bt_compressor").style.display = "none";
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


//////// ELEMENTS HIGHLIGHT ////////

function toneDefeatHighlight(){

    if (state.tone_defeat){
        document.getElementById("bt_tone_defeat").style.border = "3px solid rgb(160, 160, 160)";
        document.getElementById("bt_tone_defeat").style.background = "rgb(100, 0, 0)";
        document.getElementById("bt_tone_defeat").style.color = "rgb(255, 200, 200)";
        document.getElementById("bassInfo").style.color = "grey";
        document.getElementById("trebleInfo").style.color = "grey";

    }else{
        document.getElementById("bt_tone_defeat").style.border = "2px solid rgb(100, 100, 100)";
        document.getElementById("bt_tone_defeat").style.background = "rgb(100, 100, 100)";
        document.getElementById("bt_tone_defeat").style.color = "rgb(180, 180, 180)";
        document.getElementById("bassInfo").style.color = "white";
        document.getElementById("trebleInfo").style.color = "white";
    }
}


function buttonsToneBalanceHighlight(){

    if ( state.bass < 0 ){
        document.getElementById("bt_bass-").style.border = "3px solid rgb(160, 160, 160)";
        document.getElementById("bt_bass+").style.border = "2px solid rgb(100, 100, 100)";
    }else if ( state.bass > 0 ){
        document.getElementById("bt_bass-").style.border = "2px solid rgb(100, 100, 100)";
        document.getElementById("bt_bass+").style.border = "3px solid rgb(160, 160, 160)";
    }else{
        document.getElementById("bt_bass-").style.border = "2px solid rgb(100, 100, 100)";
        document.getElementById("bt_bass+").style.border = "2px solid rgb(100, 100, 100)";
    }

    if ( state.treble < 0 ){
        document.getElementById("bt_treb-").style.border = "3px solid rgb(160, 160, 160)";
        document.getElementById("bt_treb+").style.border = "2px solid rgb(100, 100, 100)";
    }else if ( state.treble > 0 ){
        document.getElementById("bt_treb-").style.border = "2px solid rgb(100, 100, 100)";
        document.getElementById("bt_treb+").style.border = "3px solid rgb(160, 160, 160)";
    }else{
        document.getElementById("bt_treb-").style.border = "2px solid rgb(100, 100, 100)";
        document.getElementById("bt_treb+").style.border = "2px solid rgb(100, 100, 100)";
    }

    if ( state.balance < 0 ){
        document.getElementById("bt_bal-").style.border = "3px solid rgb(160, 160, 160)";
        document.getElementById("bt_bal+").style.border = "2px solid rgb(100, 100, 100)";
    }else if ( state.balance > 0 ){
        document.getElementById("bt_bal-").style.border = "2px solid rgb(100, 100, 100)";
        document.getElementById("bt_bal+").style.border = "3px solid rgb(160, 160, 160)";
    }else{
        document.getElementById("bt_bal-").style.border = "2px solid rgb(100, 100, 100)";
        document.getElementById("bt_bal+").style.border = "2px solid rgb(100, 100, 100)";
    }
}


function bt_muteHighlight(){

    const e_mute  = document.getElementById("bt_mute");
    const e_level = document.getElementById("levelInfo");

    if ( state.muted == true ) {
        e_mute .style.background = "rgb(185, 185, 185)";
        e_mute .style.color = "white";
        e_mute .style.fontWeight = "bolder";
        e_level.style.color = "rgb(150, 90, 90)";
    } else {
        e_mute .style.background = "rgb(100, 100, 100)";
        e_mute .style.color = "lightgray";
        e_mute .style.fontWeight = "normal";
        e_level.style.color = "white";
    }
}


function bt_monoHighlight(){

    const e = document.getElementById("bt_mono");

    if ( STATE.midside == 'mid' ) {
        e.className = "btn-maroon";
        e.innerText = 'MO';

    } else if ( STATE.midside == 'side' ) {
        e.className = "btn-maroon";
        e.innerText = 'L-R';

    } else if ( STATE.solo == 'l' ) {
        e.className = "btn-maroon";
        e.innerText = 'L_';

    } else if ( STATE.solo == 'r' ) {
        e.className = "btn-maroon";
        e.innerText = '_R';

    } else if ( STATE.solo == 'off' ) {
        e.className = "btn-green";
        e.innerText = 'ST';
    }

    // 'polarity' setting will modify the button border
    if ( STATE.polarity != '++' ) {
        e.style.border = "3px solid rgb(200, 10, 10)";

    } else {
        e.style.border = "2px solid rgb(120, 120, 120)";
    }
}


function bt_soloHighlight(){

    const e = document.getElementById("bt_solo");

    if ( state.solo == 'off' ) {
        e.style = "button";
        e.innerText = 'L|R';

    } else if ( state.solo == 'l' ) {
        e.style.background = "rgb(100, 0, 0)";
        e.innerText = 'L_';

    } else if ( state.solo == 'r' ) {
        e.style.background = "rgb(100, 0, 0)";
        e.innerText = '_R';
    }

}


function bt_polarityHighlight(){

    const e = document.getElementById("bt_polarity");

    if ( state.polarity != '++' ) {
        e.style.background = "rgb(100, 0, 0)";

    } else {
       e.style = "button";
    }

    e.innerText = state.polarity;
}


function bt_loudHighlight(){

    const e = document.getElementById("bt_loud");

    if ( state.equal_loudness == true ) {
        e.className = 'btn-green';

    } else {
        e.className = 'btn-dimm-gray';
    }
}


function buttonAODHighlight(){
    const e = document.getElementById("bt_aod");
    if ( state.extra_delay === 0 ) {
        e.className = 'btn-dimm-gray';
    } else {
        e.className = 'btn-maroon';
        e.style.display = 'inline-block';
    }
}


function buttonSwapLRHighlight(){
    const e = document.getElementById("bt_swap_lr");
    if ( state.lr_swapped === false ) {
        e.innerHTML = "L R";
        e.className = 'btn-dimm-gray';
    } else {
        e.innerHTML = "R L";
        e.className = 'btn-red';
        e.style.display = 'inline-block';
    }
}


function buttonCompressorHighlight(){

    if ( ! web_config.use_compressor ){
        return
    }

    const e = document.getElementById("bt_compressor");

    if ( state.compressor === 'off' ) {
        e.className = 'btn-dimm-gray';
        e.innerHTML = 'comp.<br>OFF';

    } else {
        e.className = 'btn-maroon';
        e.innerHTML = 'COMP.<br>' + state.compressor;
        e.style.display = 'inline-block';
    }
}


function buttonSubsonicHighlight(){

    const e = document.getElementById("bt_subsonic");

    if ( state.subsonic == 'off' ) {
        e.className = 'btn-dimm-gray';
        e.innerText = 'SUBS\n-';

    } else if ( state.subsonic == 'mp' ) {
        e.className = 'btn-maroon';
        e.innerText = 'SUBS\nmp';

    } else if ( state.subsonic == 'lp' ) {
        e.className = 'btn-red';
        e.innerText = 'SUBS\nlp';
    }
}


function levelInfoHighlight() {

    // currently only indicates if the subsonic filter is activated

    const e = document.getElementById("levelInfo");

    if (state.subsonic != 'off' ){
        e.style.borderWidth = "thick";
        e.style.borderColor = "DarkRed";

    }else{
        e.style.borderWidth = "thin";
        e.style.borderColor = "white";
   }
}


/////// EVENT HANDLERS FOR BUTTONS, SELECTORS AND SLIDERS

document.addEventListener('DOMContentLoaded', () => {

    const addLst = (id, event, fn) => {
        const el = document.getElementById(id);
        if (el) el.addEventListener(event, fn);
    };

    addLst('bt_restart_sys', 'click',           () => ck_peaudiosys_restart());
    addLst('advanced_switch', 'click',          () => ck_display_advanced('toggle'));

    addLst('bt_onoff', 'mousedown',             () => omd_ampli_switch('toggle'));
    addLst('bt_loud', 'mousedown',              () => omd_equal_loudness_toggle());
    addLst('bt_solo', 'mousedown',              () => omd_solo_rotate());
    addLst('bt_mono', 'mousedown',              () => omd_mono_toggle());
    addLst('bt_polarity', 'mousedown',          () => omd_polarity_rotate());

    addLst('bt_url', 'click',                   () => ck_play_url());
    addLst('bt_track_num', 'mousedown',         () => omd_select_track_number_dialog());
    addLst('playlist_selector', 'change',       (e) => oc_load_playlist(e.target.value));
    addLst('track_selector', 'change',          (e) => oc_play_track_number(e.target.selectedIndex));
    addLst('mainSelector', 'change',            (e) => oc_main_select(e.target.value));
    addLst('samplerateSelector', 'change',      (e) => oc_restart_samplerate(e.target.value));

    addLst('bt_mute', 'mousedown',              (e) => omd_mute_toggle(e.target));
    addLst('bt_swap_lr', 'mousedown',           (e) => omd_swap_lr(e.target));
    addLst('bt_aod', 'mousedown',               (e) => omd_delay_toggle(e.target));
    addLst('bt_subsonic', 'mousedown',          (e) => omd_subsonic(e.target));
    addLst('bt_tone_defeat', 'mousedown',       (e) => omd_tone_defeat(e.target));
    addLst('bt_compressor', 'mousedown',        (e) => omd_compressor(e.target));

    addLst('LUscopeSelector', 'change',         (e) => oc_LU_scope_select(e.target.value));
    addLst('LU_slider', 'input',                (e) => oi_LU_slider_action(e.target.value));
    addLst('bt_loudMonReset', 'mousedown',      (e) => omd_lu_mon_reset(e.target));

    addLst('bt_lvl_m1', 'mousedown',            (e) => omd_audio_change(e.target, 'level', -1));
    addLst('bt_lvl_p1', 'mousedown',            (e) => omd_audio_change(e.target, 'level', 1));
    addLst('bt_lvl_m3', 'mousedown',            (e) => omd_audio_change(e.target, 'level', -3));
    addLst('bt_lvl_p3', 'mousedown',            (e) => omd_audio_change(e.target, 'level', 3));

    addLst('bt_bass-', 'mousedown',             (e) => omd_audio_change(e.target, 'bass', -1));
    addLst('bt_bass+', 'mousedown',             (e) => omd_audio_change(e.target, 'bass', 1));
    addLst('bt_bal-', 'mousedown',              (e) => omd_audio_change(e.target, 'balance', -1));
    addLst('bt_bal+', 'mousedown',              (e) => omd_audio_change(e.target, 'balance', 1));
    addLst('bt_treb-', 'mousedown',             (e) => omd_audio_change(e.target, 'treble', -1));
    addLst('bt_treb+', 'mousedown',             (e) => omd_audio_change(e.target, 'treble', 1));


    addLst('targetSelector', 'change',          (e) => oc_target_select(e.target.value));
    addLst('xoSelector', 'change',              (e) => oc_xo_select(e.target.value));
    addLst('drcSelector', 'change',             (e) => oc_drc_select(e.target.value));
    addLst('bt_peq', 'mousedown',               () => mc.send_cmd('aux peq_bypass toggle'));
    addLst('bt_toggle_eq_graphs', 'mousedown',  () => omd_graphs_toggle());

    addLst('bt_-15min', 'mousedown',            (e) => omd_playerCtrl(e.target, 'rew_15min'));
    addLst('bt_-5min', 'mousedown',             (e) => omd_playerCtrl(e.target, 'rew_5min'));
    addLst('bt_+5min', 'mousedown',             (e) => omd_playerCtrl(e.target, 'ff_5min'));
    addLst('bt_+15min', 'mousedown',            (e) => omd_playerCtrl(e.target, 'ff_15min'));
    addLst('bt_prev', 'mousedown',              (e) => omd_playerCtrl(e.target, 'previous'));
    addLst('bt_rew', 'mousedown',               (e) => omd_playerCtrl(e.target, 'rew'));
    addLst('bt_ff', 'mousedown',                (e) => omd_playerCtrl(e.target, 'ff'));
    addLst('bt_next', 'mousedown',              (e) => omd_playerCtrl(e.target, 'next'));
    addLst('random_toggle_button', 'mousedown', (e) => omd_playerCtrl(e.target, 'random_toggle'));
    addLst('bt_eject', 'mousedown',             (e) => omd_playerCtrl(e.target, 'eject'));
    addLst('bt_stop', 'mousedown',              (e) => omd_playerCtrl(e.target, 'stop'));
    addLst('bt_pause', 'mousedown',             (e) => omd_playerCtrl(e.target, 'pause'));
    addLst('bt_play', 'mousedown',              (e) => omd_playerCtrl(e.target, 'play'));

    addLst('bt_macros_toggle', 'mousedown',     () => omd_macro_buttons_display_toggle());
});


// INIT
if (document.readyState === 'complete') {
    init();
} else {
    window.addEventListener('load', init);
}
