# Firewire audio interfaces

## FFADO for firewire audio interfaces

If you plan to use a JACK with a firewire audio interface, please install the Firewire Audio Drivers stuff (aka FFADO):

    sudo apt install libffado2 ffado-tools ffado-mixer-qt4 jackd2-firewire


More info here

http://subversion.ffado.org/wiki

http://subversion.ffado.org/wiki/StepByStepUbuntu12.04


## config.yml

**Configure** your card under `config.yml` like this, by using `-n 3` as recommended for serial interfaces:

    system_card: guid:0x00130e01000406d2
    ...
    ...
    jack_options:           -R -d firewire
    jack_backend_options:   -d $autoCard -r $autoFS -p 1024 -n 3

Use `ffado-test ListDevices` to find your card's firewire GUID.


## brutefir_config

No modifications are needed.

The Jack ports for your system card will have a new naming, but don't worry because the Jack firewire backend automagically creates aliases for regular naming `system:playback...`:


    $ jack_lsp firewire -A
    firewire_pcm:00130e01000406d2_Rec 1_in
       system:capture_1
    firewire_pcm:00130e01000406d2_Rec 2_in
       system:capture_2
    firewire_pcm:00130e01000406d2_Rec 3_in
       system:capture_3
    firewire_pcm:00130e01000406d2_Rec 4_in
       system:capture_4
    firewire_pcm:00130e01000406d2_Rec 5_in
       system:capture_5
    firewire_pcm:00130e01000406d2_Rec 6_in
       system:capture_6
    firewire_pcm:00130e01000406d2_Midi In_in
    firewire_pcm:00130e01000406d2_Play 1_out
       system:playback_1
    firewire_pcm:00130e01000406d2_Play 2_out
       system:playback_2
    firewire_pcm:00130e01000406d2_Play 3_out
       system:playback_3
    firewire_pcm:00130e01000406d2_Play 4_out
       system:playback_4
    firewire_pcm:00130e01000406d2_Play 5_out
       system:playback_5
    firewire_pcm:00130e01000406d2_Play 6_out
       system:playback_6
    firewire_pcm:00130e01000406d2_Play 7_out
       system:playback_7
    firewire_pcm:00130e01000406d2_Play 8_out
       system:playback_8
    firewire_pcm:00130e01000406d2_Midi Out_out



## Firewire sound card mixer settings

For ALSA cards, we use `alsactl` to save our sound card settings to a file `pe.audio.sys/.asound.MYCARD`, as prepared in advance with `alsamixer`.

So these cards settings will be restored when running `pe.audio.sys/scripts/sound_cards_prepare.py` at system restart.

For FFADO cards, this needs more manual work :-/

Basically, it is spected to found a custom made bash script for your card settings to be restored. This script does run several dbus-send commands to the fireaudio dbus system, see the provided sample file:

    ~/pe.audio.sys/.ffado.0x00130e01000406d2.sh

        dbus-send --print-reply --dest=org.ffado.Control /org/ffado/Control/DeviceManager/00130e01000406d2/Mixer/Out12Mute org.ffado.Control.Element.Discrete.setValue int32:0
        dbus-send --print-reply --dest=org.ffado.Control /org/ffado/Control/DeviceManager/00130e01000406d2/Mixer/Out34Mute org.ffado.Control.Element.Discrete.setValue int32:0
        dbus-send --print-reply --dest=org.ffado.Control /org/ffado/Control/DeviceManager/00130e01000406d2/Mixer/Out56Mute org.ffado.Control.Element.Discrete.setValue int32:0
        ...
        ...
        ...

**You'll need to make your own script** by monitorig dBus messages in a terminal while playing with the ffado-mixer GUI, please refer to:

**http://subversion.ffado.org/wiki/ffadoMixerGuides**

<a href="url"><img src="https://github.com/Rsantct/pe.audio.sys/blob/master/pe.audio.sys/doc/images/ffado-mixer.png" align="center" width="480" ></a>







