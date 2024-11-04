#!/bin/bash

# A helper to analyze the real XO output as sent to the sound card DAC,
# so you can decide if more or less convolver gain can be used on each way
# alongside with some analog line attenuator, this way you can probably
# improve the S/N mainly in the tweeter analog chain.
#
# JAAA is a excellent tool from Fons Adriaensen
# https://kokkinizita.linuxaudio.org/linuxaudio/index.html


killall jaaa 1>/dev/null 2>&1

jaaa -J &
sleep 1


jack_connect brutefir:lo.L      jaaa:in_1
jack_connect brutefir:mi.L      jaaa:in_2
jack_connect brutefir:hi.L      jaaa:in_3

jack_connect brutefir:lo.R      jaaa:in_5
jack_connect brutefir:mi.R      jaaa:in_6
jack_connect brutefir:hi.R      jaaa:in_7
