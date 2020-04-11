## ---------------- THIS IS OBSOLETE --------------------

# Python 3 on Raspberry Pi Raspbian

We need Pyton >=3.6, but currently Raspbian is based on Debian *stretch* that comes with Python 3.5. Hope Raspbian updates to Debian *buster* soon.

Update 2019-feb: please go to **option 3** below.

## option 1: Python 3.6.x from sources

https://realpython.com/installing-python/#compiling-python-from-source

    sudo apt-get update

    sudo apt-get install build-essential tk-dev libncurses5-dev libncursesw5-dev libreadline6-dev libdb5.3-dev libgdbm-dev libsqlite3-dev libssl-dev libbz2-dev libexpat1-dev liblzma-dev zlib1g-dev

    mkdir tmp

    cd tmp

    wget https://www.python.org/ftp/python/3.6.5/Python-3.6.5.tar.xz

    tar xf Python-3.6.5.tar.xz

    cd Python-3.6.5

    ./configure --enable-optimizations

    make

Now, optionally you can resume reading a dozen of chapters of your favourite book :-)
... **about 3 h later**:

    sudo make altinstall

You are done, but now you have both 3.5 and 3.6 (under /usr/local).

Your python3 stills points to 3.5:

    $ ls -lh /usr/bin/python3*
    lrwxrwxrwx 1 root root    9 Jan 20  2017 /usr/bin/python3 -> python3.5
    -rwxr-xr-x 2 root root 3.8M Sep 27 19:25 /usr/bin/python3.5
    -rwxr-xr-x 2 root root 3.8M Sep 27 19:25 /usr/bin/python3.5m
    lrwxrwxrwx 1 root root   10 Jan 20  2017 /usr/bin/python3m -> python3.5m
    
    $ ls /usr/local/bin/pip*
    /usr/local/bin/pip3.6

Replace it to 3.6:

    $ sudo rm /usr/bin/python3
    $ sudo ln -s /usr/local/bin/python3.6 /usr/bin/python3
    $ sudo ln -s /usr/local/bin/pip3.6 /usr/local/bin/pip3


To `pip3` to avoid `lsb_release` errors, google searching proposes the following, and I have done it on my system :-/

    $ sudo mv /usr/bin/lsb_realease /usr/bin/lsb_realease.BAK

Finally remove your `tmp/` stuff.

Removing above packages used for building does not worth it, immo.

## option 2: Berryconda (easy)
I've found Berryconda, a Python3.6 distro for Raspbian based in the well known Python distribution Anaconda that works well.

https://github.com/jjhelmus/berryconda


    Do you wish the installer to prepend the Berryconda3 install location
    to PATH in your /home/predic/.bashrc ? [yes|no]
    [no] >>> yes

I've found that it is needed to move the following `~/.bashrc` added lines to your `~/.profile`

    # added by Berryconda3 installer
    export PATH="/home/predic/berryconda3/bin:$PATH"
    
## option 3: uptade to Raspbian Testing (preferred)

2019-feb. I ve recently succesfully upgraded my RPI3 from the standard stable distribution (*stretch*) to testing (*buster*).

This provides Python 3.7 :-)

- Do `sudo apt update`, `sudo apt upgrade`, repeat until no more updates are announced. Then do `sudo apt dist-upgrade`.
- Edit `/etc/apt/sources.list` and `/etc/apt/sources.list.d\raspi.list`, replacing `stretch` with `buster`.
- Do `sudo apt update`, `sudo apt upgrade`, repeat until no more updates are announced. Be patient, this will take a while, and you'll need to answer some questions, just say 'Y'. 
- Then do `sudo apt dist-upgrade`
- Reboot your RPI
- Reconfigure MPD:
    - Disable MPD default system service behavior:
        ```
        sudo systemctl stop mpd.service
        sudo systemctl disable mpd.service
        sudo systemctl stop mpd.socket
        sudo systemctl disable mpd.socket
        ```
    - Update your MPD database:
        ```
        mpd
        mpc update
        ```
- Check your PYTHONPATH under `~.profile` to point to the standard place `/usr/bin/python3`
- (re)Install the needed Python3.7 packages:
    ```
    sudo apt install python3-pip python3-yaml python3-ruamel.yaml python3-numpy python3-jack-client python3-mpd
    sudo pip3 install sounddevice watchdog
    ```
- Have a look if some audio service is using your sound card:
    ```
    fuser -v /dev/snd/*
    ```
    - If any found disable it, e.g.:
    ```
    sudo systemctl stop timidity
    sudo systemctl disable timidity
    ```
- If the web page seems not to work, please enable PHP on Apache2:
    ```
    sudo a2enmod php7.3
    ```
- If brutefir shows a not up to date version, [compile](https://github.com/AudioHumLab/FIRtro/wiki/911-Brutefir---versiones#compilar-brutefir) Brutefir to newest version.
   
