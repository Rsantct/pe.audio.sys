This folder hosts the web page that manages your pe.audio.sys, for instance from your smartphone, tablet or PC web browser. 

Please mind that an HTML5 capable browser is needed. 

## HTTP Server configuration: Apache+PHP or Node.js

As per it is possible to use two server side backend flavours:

- **Apache+PHP (system wide service)**
- **Node.js (user space service)**

the only needed configuration has to be done under the `clientside.js` file:

     Set URL_PREFIX ='/' if you use the provided peasys_node.js server script,
     or set it '/functions.php' if you use Apache+PHP at server side.

## HTTP server launcher

If you use Apache + PHP, you need to set the sites-enabled under your system wide Apache2 configuration. See [FIRtro's Wiki](https://github.com/AudioHumLab/FIRtro/wiki/04a-Instalación-de-Linux-y-paquetes-de-SW#6-página-web-de-control-remoto-opcional-pero-recomendable).

If you prefer run Node.js as server side backend, you can run Node.js under your user space, e.g. under `/etc/rc.local`:

    su -l YourUser -c "node $HOME/pe.audio.sys/share/www/peasys_node.js"


## Screenshots
First screenshot shows advanced controls (hidden by default, toggled by the gear button)

When 'iradio' or 'istreams' input, it appears an url link button [ &#9901; ] to the user to enter an url stream address to be played

![](https://github.com/Rsantct/pe.audio.sys/blob/master/pe.audio.sys/share/www/images/control%20web%20v1.1a.jpg)
![](https://github.com/Rsantct/pe.audio.sys/blob/master/pe.audio.sys/share/www/images/control%20web%20v1.1b.jpg)
![](https://github.com/Rsantct/pe.audio.sys/blob/master/pe.audio.sys/share/www/images/control%20web%20v1.1c.jpg)
![](https://github.com/Rsantct/pe.audio.sys/blob/master/pe.audio.sys/share/www/images/control%20web%20v1.1d.jpg)

