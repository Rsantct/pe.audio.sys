This folder hosts the web page that manages your pe.audio.sys, for instance from your smartphone, tablet or PC web browser. 

Please mind that an HTML5 capable browser is needed. 

## HTTP Server configuration: Apache+PHP or Node.js

It is possible to use two server side backend flavours:

- **Apache+PHP (system wide service)**
- **Node.js (user space service)**

The only needed configuration has to be done inside the `clientside.js` file:

     Set URL_PREFIX ='/' if you use the provided peasys_node.js server script,
     or set it '/functions.php' if you use Apache+PHP at server side.
     
Above changes are automatically made when running the `tmp/uptade_peaudiosys.sh` installing script.

Last, the **HTTP port** needs to be configured under

- your Apache's `sites-available/` configuration, 
- or inside the `peaudio_node.js` file, as appropriate, for instance `NODEJS_PORT = 8080;` 


## HTTP server launcher

If you use **Apache + PHP**, you need to set properly a `sites-available/` file under your system wide Apache2 configuration. See [FIRtro's Wiki](https://github.com/AudioHumLab/FIRtro/wiki/04a-Instalación-de-Linux-y-paquetes-de-SW#6-página-web-de-control-remoto-opcional-pero-recomendable).

If you prefer to run **Node.js** as server side backend, you can run Node.js under your user space, for instance you can launch it at startup through by adding a line inside `/etc/rc.local` as follows:

    su -l YourUser -c "node /home/YourUser/pe.audio.sys/share/www/peasys_node.js"


## Screenshots
First screenshot shows advanced controls (hidden by default, toggled by the gear button)

When 'iradio' or 'istreams' input, it appears an url link button [ &#9901; ] to the user to enter an url stream address to be played

![](https://github.com/Rsantct/pe.audio.sys/blob/master/pe.audio.sys/share/www/images/control%20web%20v1.1a.jpg)
![](https://github.com/Rsantct/pe.audio.sys/blob/master/pe.audio.sys/share/www/images/control%20web%20v1.1b.jpg)
![](https://github.com/Rsantct/pe.audio.sys/blob/master/pe.audio.sys/share/www/images/control%20web%20v1.1c.jpg)
![](https://github.com/Rsantct/pe.audio.sys/blob/master/pe.audio.sys/share/www/images/control%20web%20v1.1d.jpg)

