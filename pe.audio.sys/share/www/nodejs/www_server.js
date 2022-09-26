#!/usr/bin/env node

/*
# Copyright (c) Rafael Sánchez
# This file is part of 'pe.audio.sys'
# 'pe.audio.sys', a PC based personal audio system.
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
var vv      = false;        // very vervose mode
const opcs = process.argv.slice(2);
if ( opcs.indexOf('-v') != -1 ){
    verbose = true;
}
if ( opcs.indexOf('-vv') != -1 ){
    verbose = true;
    vv      = true;
}


// Reading address & port to communicate to pe.audio.sys
try {
    const UHOME = require('os').homedir();
    let fileContents = fs.readFileSync(UHOME + '/pe.audio.sys/config/config.yml', 'utf8');
    let CFG = yaml.safeLoad(fileContents);
    var PAS_ADDR =   CFG.peaudiosys_address; // PAS ~> pe.audio.sys
    var PAS_PORT =   CFG.peaudiosys_port;
} catch (e) {
    console.log(e);
}


// Helpers to printout http TX and RX chunks w/o repeating them
var last_cmd_phrase = '';
var last_http_sent  = '';


// Color escape sequences for console.log usage
// https://stackoverflow.com/questions/9781218/how-to-change-node-jss-console-font-color

const Reset = "\x1b[0m";
const Bright = "\x1b[1m";
const Dim = "\x1b[2m";
const Underscore = "\x1b[4m";
const Blink = "\x1b[5m";
const Reverse = "\x1b[7m";
const Hidden = "\x1b[8m";

const FgBlack = "\x1b[30m";
const FgRed = "\x1b[31m";
const FgGreen = "\x1b[32m";
const FgYellow = "\x1b[33m";
const FgBlue = "\x1b[34m";
const FgMagenta = "\x1b[35m";
const FgCyan = "\x1b[36m";
const FgWhite = "\x1b[37m";

const BgBlack = "\x1b[40m";
const BgRed = "\x1b[41m";
const BgGreen = "\x1b[42m";
const BgYellow = "\x1b[43m";
const BgBlue = "\x1b[44m";
const BgMagenta = "\x1b[45m";
const BgCyan = "\x1b[46m";
const BgWhite = "\x1b[47m";


// This is the MAIN function, it is called from the httpServer
// when some httpRequest is received.
function onHttpReq( httpReq, httpRes ){

    // DEBUG
    if (vv) console.log( FgCyan, '(node) httpServer RX:', httpReq.url, Reset );

    const docRoot = __dirname + '/../'

    let server_header = 'pe.audio.sys / Node.js ' + process.version
    httpRes.setHeader('server', server_header);

    var fpath = '';
    var ctype = ''


    // HTML code index.html as an http response
    // (i) index_big.html is used for better layout in a landscape tablet screen.
    if (httpReq.url === '/' || httpReq.url === '/index.html'
                            || httpReq.url === '/index_big.html') {

        ctype = 'text/html';
        fpath = docRoot + 'index.html';

        if (httpReq.url === '/index_big.html'){
            fpath = fpath.replace('index', 'index_big');
        }

        httpRes.writeHead(200,  {'Content-Type': ctype} );
        fs.readFile(fpath, 'utf8', (err,data) => {
            if (err) throw err;
            httpRes.write(data);
            httpRes.end();
            if (vv) console.log( FgBlue, '(node) httpServer TX: ', ctype, '('+fpath+')', Reset );
        });
    }


    // MANIFEST FILE
    else if (httpReq.url.match(/site\.webmanifest/g)) {

        ctype = 'text/plain';
        fpath = docRoot + httpReq.url;

        httpRes.writeHead(200,  {'Content-Type': ctype} );
        fs.readFile(fpath, 'utf8', (err,data) => {
            if (err) throw err;
            httpRes.write(data);
            httpRes.end();
            if (vv) console.log( FgBlue, '(node) httpServer TX: ', ctype, '('+fpath+')', Reset  );
        });
    }


    // CSS
    else if (httpReq.url.match("\.css$")) {

        ctype = 'text/css';
        fpath = docRoot + httpReq.url;

        httpRes.writeHead(200,  {'Content-Type': ctype} );
        fs.readFile(fpath, 'utf8', (err,data) => {
            if (err) throw err;
            httpRes.write(data);
            httpRes.end();
            if (vv) console.log( FgBlue, '(node) httpServer TX: ', ctype, '('+fpath+')', Reset  );
        });
    }


    // JAVASCRIPT
    else if (httpReq.url === '/js/main.js') {

        ctype = 'application/javascript';
        fpath = docRoot + 'js/main.js';

        httpRes.writeHead(200, {'Content-Type': ctype});
        fs.readFile(fpath, 'utf8', (err,data) => {
            if (err) throw err;
            httpRes.write(data);
            httpRes.end();
            if (vv) console.log( FgBlue, '(node) httpServer TX: ', ctype, '('+fpath+')', Reset  );
        });
    }


    // FAVICON.ICO for Mozilla and Chrome like browsers
    else if (httpReq.url === '/favicon.ico') {

        ctype = 'image/vnd.microsoft.icon';
        fpath = docRoot + 'favicon.ico';

        httpRes.writeHead(200, {'Content-Type': ctype});
        fs.readFile(favicon_path, (err, data) => {
            if (! err) {
                httpRes.write(data);
                httpRes.end();
                if (vv) console.log( FgBlue, '(node) httpServer TX: ', ctype, '('+fpath+')', Reset  );
            }
        });
    }


    // IMAGES
    //      Pending to use ETag to allow browsers to cache images at client end.
    //      By now, we will use Cache-Control 60 seconds for Safary to chache the
    //      sent image. Firefox uses cached image even if omitted this header.
    else if ( httpReq.url.match(/\/images/g) ) {

        ctype = 'image';
        if       ( httpReq.url.slice(-4, ) === '.png' ) {
            ctype = 'image/png';
        }else if ( httpReq.url.slice(-4, ) === '.jpg' ) {
            ctype = 'image/jpg';
        }

        fpath = docRoot + httpReq.url;

        // The browser's clientside javascript will request some stamp ?xxxx
        // after the filename, e.g: images/brutefir_eq.png?xxxx
        fpath = fpath.split('?').slice(0, 1)[0]

        httpRes.writeHead(200, {'Content-Type': ctype,
                                'Cache-Control': 'max-age=60'});
        fs.readFile(fpath, (err, data) => {
            if (! err) {
                httpRes.write(data);
                httpRes.end();
               if (vv)  console.log( FgBlue, '(node) httpServer TX: ', ctype, '('+fpath+')', Reset  );
            }
        });
    }


    // A CLIENT QUERY (url = ....?command=....)
    else if (httpReq.url.match(/\?command=/g)){

        let q = url.parse(httpReq.url, true).query;
        let cmd_phrase = q.command;

        if ( cmd_phrase ){

            // debugging received commands but not repeating :-)
            if (last_cmd_phrase !== cmd_phrase){
                if (verbose){
                    console.log(FgGreen, '(node) httpServer RX: ' + httpReq.url);
                }
                last_cmd_phrase = cmd_phrase;
            }

            // Create a socket client to the pe.audio.sys TCP server
            const client = net.createConnection( { port:PAS_PORT,
                                                   host:PAS_ADDR },
                                                   () => {
            });

            // If the TCP server is unavailable, then do nothing but ending the http stuff
            client.on('error', function(err){
                httpRes.end();
                client.destroy();
                console.log( FgRed, '(node) cannot connect to pe.audio.sys at '
                             + PAS_ADDR + ':' + PAS_PORT, Reset );
            });

            // Will use timeout when connecting as a client to the pe.audio.sys server
            // (i) It is a must to ending the socket if timeout happens
            //     https://nodejs.org/api/net.html#net_socket_settimeout_timeout_callback
            //     As per this is a local connection, it is enough about 100 ms
            client.setTimeout(100);
            client.on('timeout', () => {
              console.log( FgRed, '(node) client socket timeout to pe.audio.sys at '
                           + PAS_ADDR + ':' + PAS_PORT, Reset );
              client.end();
            });

            client.write( cmd_phrase + '\r\n' );
            if (verbose){
                console.log( FgGreen, '(node) ' + PAS_ADDR + ':' +
                             PAS_PORT + ' TX: ' + cmd_phrase, Reset );
            }

            // The key (*) - the handler for socket received data -
            client.on('data', (data) => {

                const ans = data.toString();
                if (verbose){
                    if ( ans.length > 40 ){
                        console.log( FgGreen, '(node) ' + PAS_ADDR + ':' +
                                     PAS_PORT + ' RX:', ans.slice(0,40) +
                                     ' ... ...', Reset );
                    }
                    else {
                        console.log( FgGreen, '(node) ' + PAS_ADDR + ':' +
                                     PAS_PORT + ' RX:', ans, Reset);
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
                                console.log( FgGreen, '(node) httpServer TX: ' + ans.slice(0,40), Reset );
                            }
                            else {
                                console.log( FgGreen, '(node) httpServer TX: ' + ans, Reset );
                            }
                        }
                        last_http_sent = ans;
                    }
                }
                httpRes.end();
            });
        }
    }


    // IGNORING the httpRequest
    else {
        const ans = 'NACK'
        ctype = 'text/plain'
        httpRes.writeHead(200, {'Content-Type': ctype});
        httpRes.write(ans + '\n');
        httpRes.end();
        console.log( FgBlue, '(node) httpServer TX: ', ctype, ans, Reset);
    }
}

// Starts an HTTP SERVER, which automagically will trigger
// a function when a 'request' event occurs.
http.createServer( onHttpReq ).listen( NODEJS_PORT );

console.log('Node.js', process.version);
console.log('Server running at http://localhost:' + NODEJS_PORT + '/');
