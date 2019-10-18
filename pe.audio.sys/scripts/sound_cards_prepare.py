#!/usr/bin/env python3
"""
    Prepapare sound cards to be used under pe.audio.sys.

    This is optional, but recommended.

    Cards to be prepared are declared under 'sound_cards_prepare.yml'

    ALSA mixer setting must be available under share/asound.XXXXX
    where XXXXX stands for the card name.
    
"""
import os, sys
import subprocess as sp
import yaml

UHOME = os.path.expanduser("~")
THISPATH = os.path.dirname(os.path.abspath(__file__))
with open(f'{THISPATH}/sound_cards_prepare.yml', 'r') as f:
    cfg = yaml.load(f)

for card in cfg:

    card = cfg[card]

    # Release the card from pulseaudio
    try:
        sp.Popen( f'pactl set-card-profile {card["pulse_name"]} off'.split() )
    except:
        print(  f'(sound_cards_prepare) PROBLEMS releasing '
                f'\'{card["pulse_name"]}\' in pulseaudio' )

    # Restore our ALSA mixer settigs for the card
    asound_file = f'{UHOME}/pe.audio.sys/share/asound.{card["alsa_name"]}'
    try:
        if os.path.isfile( asound_file ):
            sp.Popen( f'alsactl -f {asound_file} \
                        restore {card["alsa_name"]}'.split() )
        else:
            raise
    except:
        print(  f'(sound_cards_prepare) PROBLEMS restoring alsa: '
                f'\'{card["alsa_name"]}\'' )
    
