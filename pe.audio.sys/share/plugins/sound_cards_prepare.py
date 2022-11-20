#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pe.audio.sys'
# 'pe.audio.sys', a PC based personal audio system.

"""
    Restore mixer settings for the sound cards used in pe.audio.sys.

    This is optional, but recommended.

    Cards to be prepared are 'system_card' and 'external_cards'
    as defined under config.yml

    ALSA mixer setting must be previously available under

        ~/pe.audio.sys/config/asound.XXXXX

    where XXXXX stands for the alsa card name (without the 'hw:' prefix)

    Example:

    1. Get your sound card ALSA name:

        $ aplay -l
        ...
        card 1: CODEC [USB Audio CODEC], device 0: USB Audio [USB Audio]
        ...

    2. Prepare your alsamixer settings for the 'CODEC' card:

        $ alsamixer -c CODEC

    3. Once done, save the 'CODEC' mixer setting to a file:

        $ alsactl   --file ~/pe.audio.sys/config/asound.CODEC   store CODEC

    For FFADO, see details in doc/00_firewire_audio_interface.md

"""
import  subprocess as sp
import  os
import  sys

UHOME = os.path.expanduser("~")
sys.path.append(f'{UHOME}/pe.audio.sys/share/miscel')

from    sound_cards  import  *


if __name__ == "__main__":

    if sys.argv[1:]:
        if sys.argv[1] == 'start':
            pass
        elif sys.argv[1] == 'stop':
            sys.exit()
        else:
            print(__doc__)
            sys.exit()
    else:
        print(__doc__)
        sys.exit()

    restore_all_cards_mixers()
