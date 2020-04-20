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

// Reading address & port to communicate to pe.audio.sys
try {
    const UHOME = require('os').homedir();
    let fileContents = fs.readFileSync(UHOME + '/pe.audio.sys/config.yml', 'utf8');
    let CFG = yaml.safeLoad(fileContents);
    var PAS_ADDR =   CFG.peaudiosys_address; // PAS ~> pe.audio.sys
    var PAS_PORT =   CFG.peaudiosys_port;
} catch (e) {
    console.log(e);
}

// The files to be HTTP served here
const INDEX_HTML_PATH = __dirname + '/index.html';
const CLISIDE_JS_PATH = __dirname + '/clientside.js';
const IMG_FOLDER      = __dirname + '/images';

// Helpers to printout http TX and RX chunks w/o repeating them
var last_cmd_phrase = '';
var last_http_sent  = '';

// This is the MAIN function, it is called from the httpServer
// when some httpRequest is received.
function onHttpReq( httpReq, httpRes ){

    let server_header = 'pe.audio.sys / Node.js ' + process.version
    httpRes.setHeader('server', server_header);

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

    // Serve IMAGES.
    // Pending to use ETag to allow browsers to cache images at client end.
    // By now, we will use Cache-Control 60 seconds for Safary to chache the
    // sent image. Firefox uses cached image even if omitted this header.
    else if ( httpReq.url.slice(0,7) === '/images' ) {

        let ct = 'image';
        if       ( httpReq.url.slice(-4, ) === '.png' ) {
            ct = 'image/png';
        }else if ( httpReq.url.slice(-4, ) === '.jpg' ) {
            ct = 'image/jpg';
        }
        console.log( '(node) httpServer TX: ' + ct );

        let img_path = IMG_FOLDER + '/' + httpReq.url.split('/').slice(-1, );

        // The browser's clientside javascript will request some stamp ?xxxx
        // after the filename, e.g: images/brutefir_eq.png?xxxx
        img_path = img_path.split('?').slice(0, 1)[0]

        httpRes.writeHead(200, {'Content-Type': ct,
                                'Cache-Control': 'max-age=60'});
        fs.readFile(img_path, (err, data) => {
            if (! err) {
                httpRes.write(data);
                httpRes.end();
            }
        });
    }

    // processing a CLIENT QUERY (url = /?xxxxx)
    else if (httpReq.url.slice(0,2) === '/?'){

        let q = url.parse(httpReq.url, true).query;
        let cmd_phrase = q.command;


        if ( cmd_phrase ){

            // debugging received commands but not repeating :-)
            if (last_cmd_phrase !== cmd_phrase){
                if (verbose){
                    console.log('(node) httpServer RX: /?command=' + cmd_phrase);
                }
                last_cmd_phrase = cmd_phrase;
            }

            // Create a socket client to pe.audio.sys TCP server
            const client = net.createConnection( { port:PAS_PORT,
                                                   host:PAS_ADDR },
                                                   () => {
            });

            // If the TCP server is unavailable, then do nothing but ending the http stuff
            client.on('error', function(err){
                httpRes.end();
                client.destroy();
            });

            client.write( cmd_phrase + '\r\n' );
            if (verbose){
                console.log( '(node) ' + PAS_ADDR + ':' +
                             PAS_PORT + ' TX: ' + cmd_phrase );
            }

            // The key (*) - the handler for socket received data -
            client.on('data', (data) => {

                const ans = data.toString();
                if (verbose){
                    if ( ans.length > 40 ){
                        console.log( '(node) ' + PAS_ADDR + ':' +
                                     PAS_PORT + ' RX: ' + ans.slice(0,40) +
                                     ' ... ...' );
                    }
                    else {
                        console.log( '(node) ' + PAS_ADDR + ':' +
                                     PAS_PORT + ' RX: ' + ans);
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

console.log('Node.js', process.version);
console.log('Server running at http://localhost:' + NODEJS_PORT + '/');
