# SAFFIRE LE (1746) FFADO DBUS MIXER RESTORING FOR "SOUND CARD" REGULAR MODE
# http://subversion.ffado.org/wiki/ffadoMixerGuides


# ffado dbus server is needed for dbus-send commands below, as well for ffado-mixer GUI to work
if pgrep -fa ffado-dbus-server; then
    echo "ffado-dbus-server detected :-)"
else
    ffado-dbus-server 1>/dev/null 2>&1 &
    echo "running ffado-dbus-server ..."
    sleep 3
fi


echo "uploading mixer settings ...."

# UNMUTE
dbus-send --print-reply --dest=org.ffado.Control /org/ffado/Control/DeviceManager/00130e01000406d2/Mixer/Out12Mute org.ffado.Control.Element.Discrete.setValue int32:0
dbus-send --print-reply --dest=org.ffado.Control /org/ffado/Control/DeviceManager/00130e01000406d2/Mixer/Out34Mute org.ffado.Control.Element.Discrete.setValue int32:0
dbus-send --print-reply --dest=org.ffado.Control /org/ffado/Control/DeviceManager/00130e01000406d2/Mixer/Out56Mute org.ffado.Control.Element.Discrete.setValue int32:0

# Out1 Input Mix (6 faders) + DAW Return Mix (8 faders) TOTAL 14 faders <FADER #6 MAX>
dbus-send --print-reply --dest=org.ffado.Control /org/ffado/Control/DeviceManager/00130e01000406d2/Mixer/LEMix48 org.ffado.Control.Element.MatrixMixer.setValue int32:0 int32:0 double:0
dbus-send --print-reply --dest=org.ffado.Control /org/ffado/Control/DeviceManager/00130e01000406d2/Mixer/LEMix48 org.ffado.Control.Element.MatrixMixer.setValue int32:1 int32:0 double:0
dbus-send --print-reply --dest=org.ffado.Control /org/ffado/Control/DeviceManager/00130e01000406d2/Mixer/LEMix48 org.ffado.Control.Element.MatrixMixer.setValue int32:2 int32:0 double:0
dbus-send --print-reply --dest=org.ffado.Control /org/ffado/Control/DeviceManager/00130e01000406d2/Mixer/LEMix48 org.ffado.Control.Element.MatrixMixer.setValue int32:3 int32:0 double:0
dbus-send --print-reply --dest=org.ffado.Control /org/ffado/Control/DeviceManager/00130e01000406d2/Mixer/LEMix48 org.ffado.Control.Element.MatrixMixer.setValue int32:4 int32:0 double:0
dbus-send --print-reply --dest=org.ffado.Control /org/ffado/Control/DeviceManager/00130e01000406d2/Mixer/LEMix48 org.ffado.Control.Element.MatrixMixer.setValue int32:5 int32:0 double:0
dbus-send --print-reply --dest=org.ffado.Control /org/ffado/Control/DeviceManager/00130e01000406d2/Mixer/LEMix48 org.ffado.Control.Element.MatrixMixer.setValue int32:6 int32:0 double:32768
dbus-send --print-reply --dest=org.ffado.Control /org/ffado/Control/DeviceManager/00130e01000406d2/Mixer/LEMix48 org.ffado.Control.Element.MatrixMixer.setValue int32:7 int32:0 double:0
dbus-send --print-reply --dest=org.ffado.Control /org/ffado/Control/DeviceManager/00130e01000406d2/Mixer/LEMix48 org.ffado.Control.Element.MatrixMixer.setValue int32:8 int32:0 double:0
dbus-send --print-reply --dest=org.ffado.Control /org/ffado/Control/DeviceManager/00130e01000406d2/Mixer/LEMix48 org.ffado.Control.Element.MatrixMixer.setValue int32:9 int32:0 double:0
dbus-send --print-reply --dest=org.ffado.Control /org/ffado/Control/DeviceManager/00130e01000406d2/Mixer/LEMix48 org.ffado.Control.Element.MatrixMixer.setValue int32:10 int32:0 double:0
dbus-send --print-reply --dest=org.ffado.Control /org/ffado/Control/DeviceManager/00130e01000406d2/Mixer/LEMix48 org.ffado.Control.Element.MatrixMixer.setValue int32:11 int32:0 double:0
dbus-send --print-reply --dest=org.ffado.Control /org/ffado/Control/DeviceManager/00130e01000406d2/Mixer/LEMix48 org.ffado.Control.Element.MatrixMixer.setValue int32:12 int32:0 double:0
dbus-send --print-reply --dest=org.ffado.Control /org/ffado/Control/DeviceManager/00130e01000406d2/Mixer/LEMix48 org.ffado.Control.Element.MatrixMixer.setValue int32:13 int32:0 double:0


# Out2 Input Mix (6 faders) + DAW Return Mix (8 faders) TOTAL 14 faders <FADER #7 MAX>
dbus-send --print-reply --dest=org.ffado.Control /org/ffado/Control/DeviceManager/00130e01000406d2/Mixer/LEMix48 org.ffado.Control.Element.MatrixMixer.setValue int32:0 int32:1 double:0
dbus-send --print-reply --dest=org.ffado.Control /org/ffado/Control/DeviceManager/00130e01000406d2/Mixer/LEMix48 org.ffado.Control.Element.MatrixMixer.setValue int32:1 int32:1 double:0
dbus-send --print-reply --dest=org.ffado.Control /org/ffado/Control/DeviceManager/00130e01000406d2/Mixer/LEMix48 org.ffado.Control.Element.MatrixMixer.setValue int32:2 int32:1 double:0
dbus-send --print-reply --dest=org.ffado.Control /org/ffado/Control/DeviceManager/00130e01000406d2/Mixer/LEMix48 org.ffado.Control.Element.MatrixMixer.setValue int32:3 int32:1 double:0
dbus-send --print-reply --dest=org.ffado.Control /org/ffado/Control/DeviceManager/00130e01000406d2/Mixer/LEMix48 org.ffado.Control.Element.MatrixMixer.setValue int32:4 int32:1 double:0
dbus-send --print-reply --dest=org.ffado.Control /org/ffado/Control/DeviceManager/00130e01000406d2/Mixer/LEMix48 org.ffado.Control.Element.MatrixMixer.setValue int32:5 int32:1 double:0
dbus-send --print-reply --dest=org.ffado.Control /org/ffado/Control/DeviceManager/00130e01000406d2/Mixer/LEMix48 org.ffado.Control.Element.MatrixMixer.setValue int32:6 int32:1 double:0
dbus-send --print-reply --dest=org.ffado.Control /org/ffado/Control/DeviceManager/00130e01000406d2/Mixer/LEMix48 org.ffado.Control.Element.MatrixMixer.setValue int32:7 int32:1 double:32768
dbus-send --print-reply --dest=org.ffado.Control /org/ffado/Control/DeviceManager/00130e01000406d2/Mixer/LEMix48 org.ffado.Control.Element.MatrixMixer.setValue int32:8 int32:1 double:0
dbus-send --print-reply --dest=org.ffado.Control /org/ffado/Control/DeviceManager/00130e01000406d2/Mixer/LEMix48 org.ffado.Control.Element.MatrixMixer.setValue int32:9 int32:1 double:0
dbus-send --print-reply --dest=org.ffado.Control /org/ffado/Control/DeviceManager/00130e01000406d2/Mixer/LEMix48 org.ffado.Control.Element.MatrixMixer.setValue int32:10 int32:1 double:0
dbus-send --print-reply --dest=org.ffado.Control /org/ffado/Control/DeviceManager/00130e01000406d2/Mixer/LEMix48 org.ffado.Control.Element.MatrixMixer.setValue int32:11 int32:1 double:0
dbus-send --print-reply --dest=org.ffado.Control /org/ffado/Control/DeviceManager/00130e01000406d2/Mixer/LEMix48 org.ffado.Control.Element.MatrixMixer.setValue int32:12 int32:1 double:0
dbus-send --print-reply --dest=org.ffado.Control /org/ffado/Control/DeviceManager/00130e01000406d2/Mixer/LEMix48 org.ffado.Control.Element.MatrixMixer.setValue int32:13 int32:1 double:0

# Out3 Input Mix (6 faders) + DAW Return Mix (8 faders) TOTAL 14 faders <FADER #8 MAX>
dbus-send --print-reply --dest=org.ffado.Control /org/ffado/Control/DeviceManager/00130e01000406d2/Mixer/LEMix48 org.ffado.Control.Element.MatrixMixer.setValue int32:0 int32:2 double:0
dbus-send --print-reply --dest=org.ffado.Control /org/ffado/Control/DeviceManager/00130e01000406d2/Mixer/LEMix48 org.ffado.Control.Element.MatrixMixer.setValue int32:1 int32:2 double:0
dbus-send --print-reply --dest=org.ffado.Control /org/ffado/Control/DeviceManager/00130e01000406d2/Mixer/LEMix48 org.ffado.Control.Element.MatrixMixer.setValue int32:2 int32:2 double:0
dbus-send --print-reply --dest=org.ffado.Control /org/ffado/Control/DeviceManager/00130e01000406d2/Mixer/LEMix48 org.ffado.Control.Element.MatrixMixer.setValue int32:3 int32:2 double:0
dbus-send --print-reply --dest=org.ffado.Control /org/ffado/Control/DeviceManager/00130e01000406d2/Mixer/LEMix48 org.ffado.Control.Element.MatrixMixer.setValue int32:4 int32:2 double:0
dbus-send --print-reply --dest=org.ffado.Control /org/ffado/Control/DeviceManager/00130e01000406d2/Mixer/LEMix48 org.ffado.Control.Element.MatrixMixer.setValue int32:5 int32:2 double:0
dbus-send --print-reply --dest=org.ffado.Control /org/ffado/Control/DeviceManager/00130e01000406d2/Mixer/LEMix48 org.ffado.Control.Element.MatrixMixer.setValue int32:6 int32:2 double:0
dbus-send --print-reply --dest=org.ffado.Control /org/ffado/Control/DeviceManager/00130e01000406d2/Mixer/LEMix48 org.ffado.Control.Element.MatrixMixer.setValue int32:7 int32:2 double:0
dbus-send --print-reply --dest=org.ffado.Control /org/ffado/Control/DeviceManager/00130e01000406d2/Mixer/LEMix48 org.ffado.Control.Element.MatrixMixer.setValue int32:8 int32:2 double:32768
dbus-send --print-reply --dest=org.ffado.Control /org/ffado/Control/DeviceManager/00130e01000406d2/Mixer/LEMix48 org.ffado.Control.Element.MatrixMixer.setValue int32:9 int32:2 double:0
dbus-send --print-reply --dest=org.ffado.Control /org/ffado/Control/DeviceManager/00130e01000406d2/Mixer/LEMix48 org.ffado.Control.Element.MatrixMixer.setValue int32:10 int32:2 double:0
dbus-send --print-reply --dest=org.ffado.Control /org/ffado/Control/DeviceManager/00130e01000406d2/Mixer/LEMix48 org.ffado.Control.Element.MatrixMixer.setValue int32:11 int32:2 double:0
dbus-send --print-reply --dest=org.ffado.Control /org/ffado/Control/DeviceManager/00130e01000406d2/Mixer/LEMix48 org.ffado.Control.Element.MatrixMixer.setValue int32:12 int32:2 double:0
dbus-send --print-reply --dest=org.ffado.Control /org/ffado/Control/DeviceManager/00130e01000406d2/Mixer/LEMix48 org.ffado.Control.Element.MatrixMixer.setValue int32:13 int32:2 double:0

# Out4 Input Mix (6 faders) + DAW Return Mix (8 faders) TOTAL 14 faders <FADER #9 MAX>
dbus-send --print-reply --dest=org.ffado.Control /org/ffado/Control/DeviceManager/00130e01000406d2/Mixer/LEMix48 org.ffado.Control.Element.MatrixMixer.setValue int32:0 int32:3 double:0
dbus-send --print-reply --dest=org.ffado.Control /org/ffado/Control/DeviceManager/00130e01000406d2/Mixer/LEMix48 org.ffado.Control.Element.MatrixMixer.setValue int32:1 int32:3 double:0
dbus-send --print-reply --dest=org.ffado.Control /org/ffado/Control/DeviceManager/00130e01000406d2/Mixer/LEMix48 org.ffado.Control.Element.MatrixMixer.setValue int32:2 int32:3 double:0
dbus-send --print-reply --dest=org.ffado.Control /org/ffado/Control/DeviceManager/00130e01000406d2/Mixer/LEMix48 org.ffado.Control.Element.MatrixMixer.setValue int32:3 int32:3 double:0
dbus-send --print-reply --dest=org.ffado.Control /org/ffado/Control/DeviceManager/00130e01000406d2/Mixer/LEMix48 org.ffado.Control.Element.MatrixMixer.setValue int32:4 int32:3 double:0
dbus-send --print-reply --dest=org.ffado.Control /org/ffado/Control/DeviceManager/00130e01000406d2/Mixer/LEMix48 org.ffado.Control.Element.MatrixMixer.setValue int32:5 int32:3 double:0
dbus-send --print-reply --dest=org.ffado.Control /org/ffado/Control/DeviceManager/00130e01000406d2/Mixer/LEMix48 org.ffado.Control.Element.MatrixMixer.setValue int32:6 int32:3 double:0
dbus-send --print-reply --dest=org.ffado.Control /org/ffado/Control/DeviceManager/00130e01000406d2/Mixer/LEMix48 org.ffado.Control.Element.MatrixMixer.setValue int32:7 int32:3 double:0
dbus-send --print-reply --dest=org.ffado.Control /org/ffado/Control/DeviceManager/00130e01000406d2/Mixer/LEMix48 org.ffado.Control.Element.MatrixMixer.setValue int32:8 int32:3 double:0
dbus-send --print-reply --dest=org.ffado.Control /org/ffado/Control/DeviceManager/00130e01000406d2/Mixer/LEMix48 org.ffado.Control.Element.MatrixMixer.setValue int32:9 int32:3 double:32768
dbus-send --print-reply --dest=org.ffado.Control /org/ffado/Control/DeviceManager/00130e01000406d2/Mixer/LEMix48 org.ffado.Control.Element.MatrixMixer.setValue int32:10 int32:3 double:0
dbus-send --print-reply --dest=org.ffado.Control /org/ffado/Control/DeviceManager/00130e01000406d2/Mixer/LEMix48 org.ffado.Control.Element.MatrixMixer.setValue int32:11 int32:3 double:0
dbus-send --print-reply --dest=org.ffado.Control /org/ffado/Control/DeviceManager/00130e01000406d2/Mixer/LEMix48 org.ffado.Control.Element.MatrixMixer.setValue int32:12 int32:3 double:0
dbus-send --print-reply --dest=org.ffado.Control /org/ffado/Control/DeviceManager/00130e01000406d2/Mixer/LEMix48 org.ffado.Control.Element.MatrixMixer.setValue int32:13 int32:3 double:0

# Output Level (value is -dBFS)
dbus-send --print-reply --dest=org.ffado.Control /org/ffado/Control/DeviceManager/00130e01000406d2/Mixer/Out12Level org.ffado.Control.Element.Discrete.setValue int32:0
dbus-send --print-reply --dest=org.ffado.Control /org/ffado/Control/DeviceManager/00130e01000406d2/Mixer/Out34Level org.ffado.Control.Element.Discrete.setValue int32:0
dbus-send --print-reply --dest=org.ffado.Control /org/ffado/Control/DeviceManager/00130e01000406d2/Mixer/Out56Level org.ffado.Control.Element.Discrete.setValue int32:0

# Output Ignore Slider
dbus-send --print-reply --dest=org.ffado.Control /org/ffado/Control/DeviceManager/00130e01000406d2/Mixer/Out12HwCtrl org.ffado.Control.Element.Discrete.setValue int32:0
dbus-send --print-reply --dest=org.ffado.Control /org/ffado/Control/DeviceManager/00130e01000406d2/Mixer/Out34HwCtrl org.ffado.Control.Element.Discrete.setValue int32:0
dbus-send --print-reply --dest=org.ffado.Control /org/ffado/Control/DeviceManager/00130e01000406d2/Mixer/Out56HwCtrl org.ffado.Control.Element.Discrete.setValue int32:0

# Hi gain for input 3 & 4
dbus-send --print-reply --dest=org.ffado.Control /org/ffado/Control/DeviceManager/00130e01000406d2/Mixer/HighGainLine3 org.ffado.Control.Element.Discrete.setValue int32:0
dbus-send --print-reply --dest=org.ffado.Control /org/ffado/Control/DeviceManager/00130e01000406d2/Mixer/HighGainLine4 org.ffado.Control.Element.Discrete.setValue int32:0

# SPDIF Transp OFF
dbus-send --print-reply --dest=org.ffado.Control /org/ffado/Control/DeviceManager/00130e01000406d2/Mixer/SpdifTransparent org.ffado.Control.Element.Discrete.setValue int32:0

# MIDI THRU OFF
dbus-send --print-reply --dest=org.ffado.Control /org/ffado/Control/DeviceManager/00130e01000406d2/Mixer/MidiThru org.ffado.Control.Element.Discrete.setValue int32:0

###############
# SAVE SETTINGS
###############
dbus-send --print-reply --dest=org.ffado.Control /org/ffado/Control/DeviceManager/00130e01000406d2/Mixer/SaveSettings org.ffado.Control.Element.Discrete.setValue int32:1

echo "mixer settings uploaded, bye!"
