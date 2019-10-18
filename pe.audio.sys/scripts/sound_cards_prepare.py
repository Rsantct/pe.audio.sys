#!/usr/bin/env python3

# Copyright (c) 2019 Rafael Sánchez
# This file is part of 'pe.audio.sys', a PC based personal audio system.

# This is based on 'pre.di.c,' a preamp and digital crossover
# https://github.com/rripio/pre.di.c
# Copyright (C) 2018 Roberto Ripio
# 'pre.di.c' is based on 'FIRtro', a preamp and digital crossover
# https://github.com/AudioHumLab/FIRtro
# Copyright (c) 2006-2011 Roberto Ripio
# Copyright (c) 2011-2016 Alberto Miguélez
# Copyright (c) 2016-2018 Rafael Sánchez
#
# 'pe.audio.sys' is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# 'pe.audio.sys' is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with 'pe.audio.sys'.  If not, see <https://www.gnu.org/licenses/>.

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
    
