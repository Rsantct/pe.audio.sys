## Requires Python >= 3.6

### Python3 basic packages

- Distro installation option:

First check if packages are available `apt-list python3-xxxx`. If so, simpli do:

```
    sudo apt install python3-pip python3-yaml python3-jack-client python3-mpd
    sudo apt install python3-numpy python3-scipy python3-matplotlib
    sudo python3 -m pip install --upgrade setuptools
```

- PIP standard installation option:

    ```
    python3 -m pip install pyaml
    python3 -m pip install python-mpd2
    python3 -m pip install numpy
    python3 -m pip install scipy
    python3 -m pip install matplotlib
    ```

  And Jack-Client
  https://jackclient-python.readthedocs.io

    ```
    sudo python3 -m pip install --upgrade setuptools
    
    # maybe necessary:
        sudo apt install libffi-dev
    
    sudo python3 -m pip install cffi
    sudo python3 -m pip install JACK-Client
    ```

### Necessary for CD-AUDIO metadata:

    sudo pip3 install discid musicbrainzngs

and maybe:

    sudo apt install libdiscid0

### Optionaly recommended if you wan to run `scripts/loudness_monitor.py`:

    sudo pip3 install sounddevice watchdog
    sudo apt install libportaudio2
    
### Optional the serial port extensions to run the IR receiver:

    apt install python3-serial
    (or python3 -m pip install pyserial)

