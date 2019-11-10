(Download and install scripts from AudioHumLab/FIRtro, adapted to pe.audio.sys)

## Required

You need **Python>=3.6** and all python stuff as indicated in **[README.md](https://github.com/Rsantct/pe.audio.sys/blob/master/pre.di.c/README.md)**. Relogin when done.

## First install:

0- If you comes from the old version of this distro, please remove any stuff under `~/tmp` 

    rm -r ~/tmp/pe.audio.sys-*

1- Under your home folder, download manually a copy of `download_peaudiosys.sh`, an run it:

```
wget https://raw.githubusercontent.com/Rsantct/pe.audio.sys/master/.install/download_peaudiosys.sh
sh download_peaudiosys.sh master
```

At this point, the install scripts and the whole 'master' repo will be located under `~/tmp` (and also deleted the above downloaded)

2- Install all stuff:

`sh tmp/update_peaudiosys.sh master`

Say **'N'** to keep your current config.

## Maintenance:
 
1- Download the last repo from github:

`sh tmp/download_peaudiosys.sh <my_brach>`

where `my_branch` can be 'master' or whatever branch name you want to test

2- Update your system:

`sh tmp/update_peaudiosys.sh <my_brach>`

Say **'Y'** to keep your current config.


### The web page

Last step in installing/updating script will update your Apache web server: you'll need sudo credentials.

Once done you can check the control web from some LAN computer or smartphone.

    http://yourMachineHostname.local

If the control web page seems not to work, please be sure you have:

    sudo apt install apache2 libapache2-mod-php

