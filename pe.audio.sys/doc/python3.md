## Requires Python >= 3.6

## Python3 packages

- Distro installation

First check if packages are available `apt-list python3-xxxx`. If so, simpli do:

```
    sudo apt install python3-pip python3-yaml python3-ruamel.yaml python3-jack-client python3-mpd
    sudo apt install python3-numpy python3-scipy python3-matplotlib
    sudo python3 -m pip install --upgrade setuptools
```

- PIP standard installation:

    ```
    python3 -m pip install numpy
    python3 -m pip install pyaml
    python3 -m pip install ruamel.pyaml
    python3 -m pip install python-mpd2
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

Optionaly recommended:

    sudo pip3 install sounddevice watchdog

