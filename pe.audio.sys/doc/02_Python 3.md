## Requires Python >= 3.6

### Python3 GENERAL USE, JACK and MPD packages:

#### Debian packages manager (apt):

Check if packages are available by using the '--simulate' flag:

    sudo apt install --simulate python3-pip python3-yaml python3-jack-client python3-mpd \
         python3-pydbus python3-numpy python3-scipy python3-matplotlib

If so, simply repeat the above command **without the `--simulate`** flag.

Update python setuptools:

    sudo python3 -m pip install --upgrade setuptools


#### Python standard packages manager (PIP) alternative:

(Be sure you have installed at least `python3-pip` as per the instructions above)

    sudo python3 -m pip install --upgrade setuptools
    python3 -m pip install pyaml
    python3 -m pip install python-mpd2
    python3 -m pip install pydbus
    python3 -m pip install numpy
    python3 -m pip install scipy
    python3 -m pip install matplotlib

    # And Jack-Client  https://jackclient-python.readthedocs.io
    sudo apt install libffi-dev
    sudo python3 -m pip install cffi
    sudo python3 -m pip install JACK-Client


### Python3 CD-Audio packages:

    # Metadata search
    sudo apt install libdiscid0
    sudo pip3 install discid musicbrainzngs

    # Automatic detection of inserted disc
    sudo apt install python3-pyudev

### Optionaly recommended if you wan to run `plugins/loudness_monitor.py`:

    sudo pip3 install sounddevice watchdog
    sudo apt install libportaudio2

### Optional the serial port extensions to run the IR receiver:

    sudo apt install python3-serial
    (or python3 -m pip install pyserial)

### Optional to manage volume through by the sound card ALSA mixer:

More info at: `config.yml.sample`

The distribution (APT) `pyalsaaudio` package is likely to be outdated, so we use **pip**:

    sudo apt-get install python3-dev
    sudo pip3 install pyalsaaudio

