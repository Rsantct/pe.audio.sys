## Streaming audio from a BT device

Although we prefer to avoid using BT audio sources, you can enable pe.audio.sys to receive audio from any BT device.

### Requirements

A BT receiver, on-board or an usb BT dongle.

Install BT standard software:

    sudo apt install bluez bluetooth pi-bluetooth bluealsa

The key package is `bluealsa`, a Bluetooth to ALSA bridge. This is intended to be used in a 'headless' pe.audio.sys machine.

For a 'desktop' machine, you can go to Pulseaudio bluetooth plugins. This is not covered here.

### Enable bluetooth audio sink profile (receiver):
    
    sudo nano /lib/systemd/system/bluealsa.service
          ExecStart=/usr/bin/bluealsa --profile=a2dp-sink

    sudo systemctl reboot

### Adding your user to the `bluetooth` group

    sudo adduser YOURUSERNAME audio bluetooth
    
    (relogin is needed)


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
    

### Configure pe.audio.sys `config.yml`

    # ============================  SOURCES  =======================================
    sources:
        ...
        ...
        BT:
            gain: 0
            capture_port:   alsa_loop

    # ========================= MISCEL CONFIGURATIONS ==============================
    ...
    ...
    # BT devices MAC addresses enabled to stream audio to pe.audio.sys
    BT_devices: 80:82:23:AA:BB:CC, D4:61:DA:DD:EE:FF


### Listening to BT devices

Please copy **`macros/examples/x_BT`** for example to `macros/9_BT`

Got to your device bluetooth settings, then connect it to your hostname pe.audio.sys machine.

Run the macro to toggle to listening to BT devices, by command line or by using the control web page.
