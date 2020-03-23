#!/usr/bin/env node

/*
# Copyright (c) 2019 Rafael Sánchez
# This file is part of 'pe.audio.sys', a PC based personal audio system.
#
# 'pe.audio.sys' is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# 'pe.audio.sys' is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with 'pe.audio.sys'.  If not, see <https://www.gnu.org/licenses/>.
*/

// -----------------------------------------------------------------------------
// ------------------------------ CONFIG ---------------------------------------
// -----------------------------------------------------------------------------
const NODEJS_PORT = 8080;   // The listening HTTP PORT
// -----------------------------------------------------------------------------

// Importing modules (require)
const http  = require('http');
const url   = require('url');
const fs    = require('fs');
const net   = require('net');
const yaml  = require('js-yaml')

// Command line '-v' verbose option
var verbose = false;        // Defaults to disable to printing out some details
const opcs = process.argv.slice(2);
if ( opcs.indexOf('-v') != -1 ){
    verbose = true;
}

// Reading addresses and ports from the pe.audio.sys config.yml file
try {
    const UHOME = require('os').homedir();
    let fileContents = fs.readFileSync(UHOME + '/pe.audio.sys/config.yml', 'utf8');
    let CFG = yaml.safeLoad(fileContents);
    const SVCS = CFG.services_addressing;

    var PREAMP_ADDR =   SVCS.pasysctrl_address;
    var PREAMP_PORT =   SVCS.pasysctrl_port;
    var AUX_ADDR =      SVCS.aux_address;
    var AUX_PORT =      SVCS.aux_port;
    var PLAYERS_ADDR =  SVCS.players_address;
    var PLAYERS_PORT =  SVCS.players_port;

} catch (e) {
    console.log(e);
}

// The files to be HTTP served here
const INDEX_HTML_PATH = __dirname + '/index.html';
const CLISIDE_JS_PATH = __dirname + '/clientside.js';

// Helpers to printout http TX and RX chunks w/o repeating them
var last_cmd_phrase = '';
var last_http_sent  = '';

// This is the MAIN function, it is called from the httpServer
// when some httpRequest is received.
function onHttpReq( httpReq, httpRes ){

    // Serve our HTML code index.html as an http response
    if (httpReq.url === '/' || httpReq.url === '/index.html') {

        console.log( '(node) httpServer TX: text/html' );

        httpRes.writeHead(200,  {'Content-Type': 'text/html'} );
        fs.readFile(INDEX_HTML_PATH, 'utf8', (err,data) => {
            if (err) throw err;
            httpRes.write(data);
            httpRes.end();
        });
    }

    // Serve the JAVASCRIPT source file refered from index.html's <src=...>
    else if (httpReq.url === '/clientside.js') {

        console.log( '(node) httpServer TX: application/javascript' );

        httpRes.writeHead(200, {'Content-Type': 'application/javascript'});
        fs.readFile(CLISIDE_JS_PATH, 'utf8', (err,data) => {
            if (err) throw err;
            httpRes.write(data);
            httpRes.end();
        });
    }

    // processing a CLIENT QUERY (url = /?xxxxx)
    else if (httpReq.url.slice(0,2) === '/?'){

        let q = url.parse(httpReq.url, true).query;
        let cmd_phrase = q.command;
        let cli_addr, cli_port;


        if ( cmd_phrase ){

            // debugging received commands but no repeating :-)
            if (last_cmd_phrase !== cmd_phrase){
                if (verbose){
                    console.log('(node) httpServer RX: /?command=' + cmd_phrase);
                }
                last_cmd_phrase = cmd_phrase;
            }

            // if prefix 'aux', remove prefix and point to the AUX server
            if ( cmd_phrase.slice(0,4) == 'aux ' ){
                cmd_phrase = cmd_phrase.slice(4,);
                cli_addr = AUX_ADDR;
                cli_port = AUX_PORT;

            }
            // if prefix 'players', remove prefix and point to the PLAYERS server
            else if ( cmd_phrase.slice(0,8) == 'players ' ){
                cmd_phrase = cmd_phrase.slice(8,);
                cli_addr = PLAYERS_ADDR;
                cli_port = PLAYERS_PORT;

            }
            // else: a regular preamp command will point to the PREAMP server
            else {
                cli_addr = PREAMP_ADDR;
                cli_port = PREAMP_PORT;
            }

            // Create a socket client to PREAMP, AUX or PLAYERS TCP servers
            const client = net.createConnection( { port:cli_port,host:cli_addr },
                                                 () => {
            });

            // If the TCP server is unavailable, then do nothing but ending the http stuff
            client.on('error', function(err){
                httpRes.end();
                client.destroy();
            });

            client.write( cmd_phrase + '\r\n' );
            if (verbose){
                console.log( '(node) ' + cli_addr + ':' +
                             cli_port + ' TX: ' + cmd_phrase );
            }

            // The key (*) - the handler for socket received data -
            client.on('data', (data) => {

                const ans = data.toString();
                if (verbose){
                    if ( ans.length > 40 ){
                        console.log( '(node) ' + cli_addr + ':' +
                                     cli_port + ' RX: ' + ans.slice(0,40) +
                                     ' ... ...' );
                    }
                    else {
                        console.log( '(node) ' + cli_addr + ':' +
                                     cli_port + ' RX: ' + ans);
                    }
                }

                client.end();

                // (*) Important to write and end the httpResponse
                //     here INSIDE the client.on('data') HANDLER
                //     because of the handler (and all JS) is asynchronous
                httpRes.writeHead(200, {'Content-Type':'text/plain'});
                if (ans){
                    httpRes.write(ans);
                    // debugging sent chunks but no repeating :-)
                    if (last_http_sent !== ans){
                        if (verbose){
                            if ( ans.length > 40 ){
                                console.log( '(node) httpServer TX: ' + ans.slice(0,40) );
                            }
                            else {
                                console.log( '(node) httpServer TX: ' + ans );
                            }
                        }
                        last_http_sent = ans;
                    }
                }
                httpRes.end();
            });
        }
    }
}

// Starts an HTTP SERVER, which automagically will trigger
// a function when a 'request' event occurs.
http.createServer( onHttpReq ).listen( NODEJS_PORT );

console.log('Server running at http://localhost:' + NODEJS_PORT + '/');
