## Requires Python >= 3.6

### Python3 GENERAL USE, JACK and MPD packages:

#### Debian packages manager (apt):

First check if packages are available `apt-list python3-xxxx`. If so, simpli do:


    sudo apt install python3-pip python3-yaml python3-jack-client python3-mpd
    sudo apt install python3-numpy python3-scipy python3-matplotlib
    sudo python3 -m pip install --upgrade setuptools


#### Python standard packages manager (PIP) alternative:

    sudo python3 -m pip install --upgrade setuptools
    python3 -m pip install pyaml
    python3 -m pip install python-mpd2
    python3 -m pip install numpy
    python3 -m pip install scipy
    python3 -m pip install matplotlib

    # And Jack-Client  https://jackclient-python.readthedocs.io
    sudo apt install libffi-dev
    sudo python3 -m pip install cffi
    sudo python3 -m pip install JACK-Client


### Python3 CD-Audio packages:

    # Metadata search
    sudo pip3 install discid musicbrainzngs

    # Automatic detection of inserted disc
    sudo apt install python3-pyudev

and maybe:

    sudo apt install libdiscid0

### Optionaly recommended if you wan to run `scripts/loudness_monitor.py`:

    sudo pip3 install sounddevice watchdog
    sudo apt install libportaudio2
    
### Optional the serial port extensions to run the IR receiver:

    sudo apt install python3-serial
    (or python3 -m pip install pyserial)

