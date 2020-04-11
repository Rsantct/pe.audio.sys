## Required

You need **Python>=3.6** and all python stuff as indicated in **[README.md](https://github.com/Rsantct/pe.audio.sys/blob/master/pre.di.c/README.md)**. Relogin when done.

## First install:

1) If you comes from the old version of this distro, please remove any stuff under `~/tmp` 

    `rm -r ~/tmp/pe.audio.sys-*`

2) Under your home folder, download manually a copy of `download_peaudiosys.sh`, an run it:

    ```cd
    wget https://raw.githubusercontent.com/Rsantct/pe.audio.sys/master/.install/download_peaudiosys.sh
    sh download_peaudiosys.sh master```

At this point, the install scripts and the whole 'master' repo will be located under `~/tmp` (and also deleted the above downloaded)

3) Install all stuff:

    `sh tmp/update_peaudiosys.sh master`

Say **'N'** when asked *keep your current config?*.

## Maintenance:
 
1) Download the last repo from github:

    `sh tmp/download_peaudiosys.sh <my_brach>`

where `my_branch` can be 'master' or whatever branch name you want to test

2) Update your system:

    `sh tmp/update_peaudiosys.sh <my_brach>`

Say **'Y'** when asked *keep your current config?*.


### The web page

You can access to the control web from some LAN computer or smartphone.

    http://yourMachineHostname.local

#### Node.js (user space service)

You need to install the Node.js package, 

    sudo apt install nodejs
    sudo apt install node-js-yaml

then login as your regular user and run:

    node /home/YourUser/pe.audio.sys/share/www/peasys_node.js &

Configure the `URL_PREXIX` under `share/www/clientside.js` so that the web page. 

When updating your system, the script `tmp/update_peaudiosy.sh` will auto configure it properly.


#### Apache + PHP (system wide service)

Last step in installing/updating script will update your Apache web server (you'll need sudo credentials).

Also please be sure you have the Apache's PHP module:

    sudo apt install apache2 libapache2-mod-php





