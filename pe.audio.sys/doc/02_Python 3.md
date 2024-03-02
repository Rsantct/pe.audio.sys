## Requires Python >= 3.6 (recommended >= 3.10)

### Python3 standard packages (Numpy, Jack, MPD, etc):

#### Recommended: Debian packages manager (APT):

Check if packages are available by using the '--simulate' flag:

    sudo apt install --simulate python3-pip python3-yaml python3-jack-client python3-mpd \
         python3-pydbus python3-numpy python3-scipy python3-matplotlib libffi-dev

If so, simply repeat the above command **without the `--simulate`** flag.


#### alternative Python packages manager (PIP):

**NOTICE:**

As per PEP 668, Python packages outside your O.S. distribution must be installed in a Python Virtual Enviroment (aka **`venv`**)

The easiest way to do this is to prepare a `venv` for your user profile, then use `pip3` inside it to install Python packages that are not included within your O.S. distribution, as for example `sounddevice`.

Even O.S. distribution driven Python packages can be instaled separatelly in your Python `venv`, but we prefer use Debian packages when possible. So let's create a `venv` by inheriting the system packages:

    $ python -m venv --system-site-packages ~/.env

Lets activate and working inside the `venv`:

    $ source ~/.env/bin/activate
    (.env) $

From now on we can use `pip3` to install packages, example:

    # BUT WE PREFER INSTALLING ALL THE FOLLOWING STUFF BY USING APT AS ABOVE
    #
    # upgrading PIP first of all
    (.env) $ python3 -m pip install --upgrade setuptools
    #
    # General usage packages
    (.env) $ pip3 install pyaml
    (.env) $ pip3 install python-mpd2
    (.env) $ pip3 install pydbus
    (.env) $ pip3 install numpy
    (.env) $ pip3 install scipy
    (.env) $ pip3 install matplotlib
    #
    # And Jack-Client  https://jackclient-python.readthedocs.io
    (.env) $ pip3 install cffi
    (.env) $ pip3 install JACK-Client
    #


### Recommended if you wan to run `plugins/loudness_monitor.py`:

    sudo apt install libportaudio2 python3-watchdog
    (.env) $ pip3 install sounddevice 

### CD-Audio:

    # CD Audio Metadata search

    # Debian available:
    sudo apt install python3-libdiscid python3-musicbrainzngs
    
    # outside Debian:
    (.env) $ pip3 install discid

    # Automatic detection of inserted disc
    sudo apt install python3-pyudev


### optional Serial port extensions to run the IR receiver:

    sudo apt install python3-serial
    # or pip3 install pyserial

### optional to manage volume through by the sound card ALSA mixer:

More info at: `config.yml.sample`

(!) The Debian `python3-alsaaudio` package is likely to be **outdated**, so we use **pip**:

    sudo apt-get install python3-dev
    (.env) $ pip3 install pyalsaaudio

