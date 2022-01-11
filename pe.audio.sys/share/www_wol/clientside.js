/*
    Copyright (c) Rafael Sánchez
    This file is part of 'pe.audio.sys'
    'pe.audio.sys', a PC based personal audio system.
*/

/*
   (i) debug trick: console.log(something);
       NOTICE: remember do not leaving any console.log active
*/

//  (i) Set URL_PREFIX ='/' if you use the provided peasys_node.js server script,
//      or set it '/functions.php' if you use Apache+PHP at server side.
//  (!!!) CURRENTLY ONLY SUPORTED BY APACHE+PHP NOT NODE.JS
const URL_PREFIX = '/functions.php';


// DICT OF CONFIGURED MACHINES
try{
    var machines = JSON.parse( send_cmd('get_machines') );
}catch(e){
    console.log('problems with \'get_machines\' command', e.name, e.message);
    var machines = { '- -': ''};
}


// TALKING TO THE SERVER
function send_cmd( cmd ) {
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
        return 'server not available ' + ans;
    }
}


// PAGE INITIATE
function page_initiate(){
    fill_in_wol_buttons();
}

// ACTION ON BUTTON CLICKED
function button_do(buttonID){
    send_cmd('wol ' + buttonID);
    // Highlights the button for a second
    document.getElementById("b_" + buttonID).className = 'machine_button_highlighted';
    setTimeout(function(){
            document.getElementById("b_" + buttonID).className = 'machine_button';
        }, 1000);
}


// FILLING IN WOL BUTTONS
function fill_in_wol_buttons() {

    // If empty macros list, do nothing
    var machines_list = Object.keys(machines);
    if ( machines_list.length == 0 ){
        console.log( '(i) empty machines dict')
        document.getElementById( "main_table").style.display = 'none';
        return
    }

    var mtable = document.getElementById("main_table");
    var row  = mtable.insertRow(index=-1);

    for (i in machines_list) {

        var machine = machines_list[i];

        // Insert a cell
        var cell = row.insertCell(index=-1);
        cell.className = 'machine_cell';
        // Create a button Element
        var btn = document.createElement('button');
        btn.type = "button";
        btn.className = "machine_button";
        //machines_list.push(machine);
        btn.id = 'b_' + machine;
        btn.innerHTML = machine;
        btn.setAttribute( "onclick", "button_do\('"+ machine +"'\)" );
        // Put the button inside the cell
        cell.appendChild(btn);

        row  = mtable.insertRow(index=-1);
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
