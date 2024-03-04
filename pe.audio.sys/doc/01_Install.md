## Required

You need **Python>=3.6** and all python stuff as indicated in **[02_Python 3.md](./02_Python%203.md)**. Relogin when done.


## First install:

1) If you comes from the old version of this distro, please remove any stuff under `~/tmp`

    `rm -r ~/tmp/pe.audio.sys-*`

2) Download manually a copy of `bin/peaudiosys_upgrade.sh`, and run it as folows:

    ```
    cd
    mkdir -p bin
    wget -O bin/peaudiosys_upgrade.sh https://raw.githubusercontent.com/AudioHumLab/pe.audio.sys/master/bin/peaudiosys_upgrade.sh
    bash ./bin/peaudiosys_upgrade.sh
    ```

**IMPORTANT:**

Say **`N`** when prompted  **`keep your current config ?`**.


## Update:

Manual updates can be done whenever you want:

    ./bin/peaudiosys_upgrade.sh

This procedure involves two internal steps:

- Download the last repo from github: `sh tmp/download_peaudiosys.sh branch`
- Update your `pe.audio.sys` folder: `sh tmp/update_peaudiosys.sh branch`

**IMPORTANT:**

Say **`Y`** when prompted  **`keep your current config ?`**.


## Automatic updates (beta):

Be sure that your Linux has `anacron` installed in order to support automatic updates.

Run this only on the first install:

    sh ~/tmp/pe.audio.sys-master/.install/crontab/set_auto_update_cronjob.sh --force

(i) You can disable `auto_update` inside the config file.


## The control web page

You can access to the control web from some LAN computer or smartphone.

    http://yourMachineHostname.local

### Node.js (user space service)

You need to install the Node.js package,

    sudo apt install nodejs node-js-yaml


The only needed configuration is the `URL_PREXIX` under `share/www/js/main.js` so that the web page runs when served from our Node.js server.

(i) Anyway the script `tmp/update_peaudiosy.sh` will auto configure this properly when updating your system.


To test the server, login as your regular user and run:

    node /home/YourUser/pe.audio.sys/share/www/peasys_node.js &

then browse http://yourIP:8080

#### Running the Node.js server at start up:

Please add this under your `plugins:` section inside `config.yml`

    # Launchs the pe.audio.sys web page Node.js server
    - node_web_server.py


### Apache + PHP (system wide service)

Last step in installing/updating script will update your pe.audio.sys web site configuration under Apache (you'll need sudo credentials).

So, please install the Apache-PHP module:

    sudo apt install apache2 libapache2-mod-php

Prior to enable the module you need to know its version, for instance:

    $ ls /etc/apache2/mods-available/php*
    /etc/apache2/mods-available/php7.4.conf  /etc/apache2/mods-available/php7.4.load


So to enable apache-php run:

    sudo a2enmod php7.4

