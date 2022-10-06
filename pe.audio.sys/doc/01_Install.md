## Required

You need **Python>=3.6** and all python stuff as indicated in **[02_Python 3.md](./02_Python%203.md)**. Relogin when done.


## First install:

1) If you comes from the old version of this distro, please remove any stuff under `~/tmp` 

    `rm -r ~/tmp/pe.audio.sys-*`

2) Under your home folder, download manually a copy of `download_peaudiosys.sh`, an run it as folows:

    ```
    cd
    wget https://raw.githubusercontent.com/AudioHumLab/pe.audio.sys/master/.install/download_peaudiosys.sh
    sh download_peaudiosys.sh master
    ```
At this point, the install scripts and the whole 'master' repo will be located under `~/tmp` (and also deleted the above downloaded)

3) Install all stuff:

    `sh tmp/update_peaudiosys.sh master`

**IMPORTANT** say **'N'** when asked *keep your current config?*.


## Automatic updates:

Be sure that your Linux has `anacron` installed in order to support automatic updates.

Run this only on the first install:

    sh ~/tmp/pe.audio.sys-master/.install/crontab/set_auto_update_cronjob.sh --force

(i) You can disable `auto_update` inside the config file (default enabled). 


## Manual updates:

Manual updates can be done whenever you want, by following the two steps below:
 
**(1)** Download the last repo from github:

    `sh tmp/download_peaudiosys.sh my_brach`

where `my_branch` can be `master` or whatever branch name you want to test

**(2)** Update your system:

    `sh tmp/update_peaudiosys.sh my_brach`

**IMPORTANT** say **'Y'** when asked *keep your current config?*.



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

Please add this under your `scripts:` section inside `config.yml`

    # Launchs the pe.audio.sys web page Node.js server
    - node_web_server.py


### Apache + PHP (system wide service)

Last step in installing/updating script will update your pe.audio.sys web site configuration under Apache (you'll need sudo credentials).

So, please install the Apache-PHP module and enable it:

    sudo apt install apache2 libapache2-mod-php
    sudo a2enmod php7.X     # (i)
    
**(i)** replace 7.X with your installed version:

    apt list libapache2-mod-php*
