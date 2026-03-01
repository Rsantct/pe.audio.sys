/*
    Copyright (c) Rafael Sánchez
    This file is part of 'pe.audio.sys'
    'pe.audio.sys', a PC based personal audio system.
*/

//  (i) Set URL_PREFIX ='/' if you use the provided nodejs/www_server.js script,
//      or set it '/php/main.php' if you use Apache+PHP at server side.
//
const URL_PREFIX = '/php/main.php';

export function send_cmd( cmd ) {

    // We use synchronous mode (async=false), althougt it is not recommended

    // Encoding special chars in the value of the 'command' parameter
    const url = URL_PREFIX + '?command=' + encodeURIComponent(cmd);

    const myREQ = new XMLHttpRequest();


    myREQ.open("GET", url, false);

    myREQ.send();
    let ans = myREQ.responseText;

    //console.log('httpTX: ' + cmd);
    //console.log('httpRX: ' + ans);

    try {
        // response as JSON Object
        return JSON.parse(ans.replaceAll(': null', ': ""'));
    } catch {
        // response as plain text
        return ans;
    }
}

export function flash_element(e, timeout=950){
    e.classList.add('btn-flash');
    setTimeout(() => {
        e.classList.remove('btn-flash');
    }, timeout);
}
