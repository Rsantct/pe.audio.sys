## Streaming audio from a BT device

Although we prefer to avoid using BT audio sources, you can enable pe.audio.sys to receive audio from any BT device.

### Requirements

- A BT receiver, on-board or an usb BT dongle.

- Install BT standard software:

    ```sudo apt install bluez bluetooth pi-bluetooth # pi-bluetooth if you use a Raspberry Pi machine```


### Adding your user to the `bluetooth` group

    sudo adduser YOURUSERNAME bluetooth

    (relogin is needed)


### Enable bluetooth audio sink profile (receiver):

    sudo nano /lib/systemd/system/bluealsa.service
          ExecStart=/usr/bin/bluealsa --profile=a2dp-sink

    sudo systemctl reboot


### Pairing and trusting a BT device

Commands that you need to pair a BT device (e.g: 80:82:23:AA:BB:CC my_iphone)

    ~ $ bluetoothctl
    Agent registered
    [bluetooth]# agent on
    Agent is already registered

    [bluetooth]# scan on
    Discovery started
    [CHG] Controller B8:27:EB:28:42:EE Discovering: yes
    ...
    ...
    [NEW] Device 80:82:23:AA:BB:CC my_iphone
    ...
    ...
    [bluetooth]# scan off
    [CHG] Controller B8:27:EB:28:42:EE Discovering: no
    Discovery stopped

    [bluetooth]# pair 80:82:23:AA:BB:CC
    Attempting to pair with 80:82:23:AA:BB:CC
    [CHG] Device 80:82:23:AA:BB:CC Connected: yes
    Request confirmation

        *** now confirm pairing on your device ***
        *** then say 'yes' below

    [agent] Confirm passkey 090582 (yes/no): yes
    [CHG] Device 80:82:23:AA:BB:CC Modalias: bluetooth:v004Cp710000000
    [CHG] Device 80:82:23:AA:BB:CC UUIDs: 00000000-deca-fade-deca-deaf00000000
    [CHG] Device 80:82:23:AA:BB:CC UUIDs: 00001000-0000-1000-8000-008000000000
    [CHG] Device 80:82:23:AA:BB:CC UUIDs: 0000110a-0000-1000-8000-008000000000
    [CHG] Device 80:82:23:AA:BB:CC UUIDs: 0000110c-0000-1000-8000-008000000000
    [CHG] Device 80:82:23:AA:BB:CC UUIDs: 0000110e-0000-1000-8000-008000000000
    [CHG] Device 80:82:23:AA:BB:CC UUIDs: 00001116-0000-1000-8000-008000000000
    [CHG] Device 80:82:23:AA:BB:CC UUIDs: 0000111f-0000-1000-8000-008000000000
    [CHG] Device 80:82:23:AA:BB:CC UUIDs: 0000112f-0000-1000-8000-008000000000
    [CHG] Device 80:82:23:AA:BB:CC UUIDs: 00001132-0000-1000-8000-008000000000
    [CHG] Device 80:82:23:AA:BB:CC UUIDs: 00001200-0000-1000-8000-008000000000
    [CHG] Device 80:82:23:AA:BB:CC UUIDs: 00001801-0000-1000-8000-008000000000
    [CHG] Device 80:82:23:AA:BB:CC UUIDs: 02030302-1d19-415f-86f2-22a210000000
    [CHG] Device 80:82:23:AA:BB:CC ServicesResolved: yes
    [CHG] Device 80:82:23:AA:BB:CC Paired: yes
    Pairing successful
    [CHG] Device 80:82:23:AA:BB:CC ServicesResolved: no
    [CHG] Device 80:82:23:AA:BB:CC Connected: no

    [bluetooth]# trust 80:82:23:AA:BB:CC
    [CHG] Device 80:82:23:AA:BB:CC Trusted: yes
    Changing 80:82:23:AA:BB:CC trust succeeded
    [bluetooth]# exit
    ~ $


### Testing

    arecord  -D bluealsa:DEV=80:82:23:AA:BB:CC,PROFILE=a2dp  --vumeter=stereo  -f cd  /dev/null

(if it doesn't seem to detect any levels, check your mobile device volume)


## The PULSEAUDIO option (preferred)

Pulseaudio provides an easy to use interface to BT devives with a very low latency.

Please refer to **`doc/80_Pulseaudio`**

#### `config.yml`

    # ============================= PLUGINS =======================================
    plugins:
        ...
        ...
        ## Set Pulseaudio apps to sound through by JACK:
        - pulseaudio-jack-sink.py
        ## Enables Pulseaudio to get sound from paired BT devices:
        - pulseaudio-BT.py


    # ============================  SOURCES  =======================================
    sources:
        ...
        ...
        BT:
            gain:       0
            jack_pname: pulse_sink

    # ========================= MISCEL CONFIGURATIONS ==============================
    ...
    ...
    # BT devices MAC addresses enabled to stream audio to pe.audio.sys
    BT_devices: 80:82:23:AA:BB:CC, D4:61:DA:DD:EE:FF


### Listening to BT devices

Please copy **`macros/examples/x_BT_pulse`** for example to `macros/9_BT`

Go to your device bluetooth settings, then connect it to your hostname pe.audio.sys machine.

Select the **BT** input or run the macro to listening to BT devices, by command line or by using the control web page.


## The ALSA option

    sudo apt install bluealsa

Bluealsa provides a Bluetooth to ALSA bridge, but its performance can be limited on SoC based systems such a Raspberry Pi 3.


#### `~/.asoundrc`

Please use the provided `.asoundrc.sample` file in order to enable the ALSA to JACK plugin.


#### `config.yml`

    # ============================  SOURCES  =======================================
    sources:
        ...
        ...
        BT:
            gain:       0
            jack_pname: alsa_loop

    # ========================= MISCEL CONFIGURATIONS ==============================
    ...
    ...
    # BT devices MAC addresses enabled to stream audio to pe.audio.sys
    BT_devices: 80:82:23:AA:BB:CC, D4:61:DA:DD:EE:FF


### Listening to BT devices

Please copy **`macros/examples/x_BT_alsa`** for example to `macros/9_BT`

Go to your device bluetooth settings, then connect it to your hostname pe.audio.sys machine.

Run the macro to toggle to listening to BT devices, by command line or by using the control web page.


### alsaloop high CPU%

    top -p $(pidof alsaloop)

If you experience high CPU% loading from the `alsaloop` process when running the BT macro, try to adjust -n (--nperiods) or -p (--period) value for jackd (under `pe.audio.sys/config.yml`)


