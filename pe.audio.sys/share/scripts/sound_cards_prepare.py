#!/usr/bin/env python3

# Copyright (c) 2019 Rafael Sánchez
# This file is part of 'pe.audio.sys', a PC based personal audio system.
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

    Cards to be prepared are 'system_card' and 'external_cards'
    as defined under pe.audio.sys (config.yml)

    ALSA mixer setting must be previously available under

        ~/pe.audio.sys/.asound.XXXXX

    where XXXXX stands for the alsa card name (without 'hw:' prefix)

    Example:

    Prepare your alsamixer settings for MYCARD, then execute the following:

        alsactl -f ~/pe.audio.sys/.asound.MYCARD store MYCARD

"""
import os
import sys
UHOME = os.path.expanduser("~")
MAINFOLDER  = f'{UHOME}/pe.audio.sys'
sys.path.append(MAINFOLDER)

from share.miscel import Fmt, CONFIG
import subprocess as sp
import yaml


def get_pulse_cards():
    pa_cards = {}
    try:
        # if 'pactl' command not available will except
        tmp = sp.check_output( 'which pactl'.split() )
        tmp = sp.check_output( 'export LANG=en_US.UTF-8 && pactl list cards',
                                shell=True ).decode().split('\n' )
        new_card = False
        for line in tmp:

            if line.startswith("Card #"):
                new_card = True
                cardN = line.strip()
                pa_cards[ cardN ] = {}

            if new_card and 'Name: ' in line:
                pa_cards[cardN]['pa_name'] = line.split(':')[-1].strip()

            if new_card and 'alsa.card_name' in line:
                pa_cards[cardN]['alsa_name'] = line.split('=')[-1].strip() \
                                                .replace('"', '')

    except:
        pass

    return pa_cards


def get_config_yml_cards():
    cards = []
    cards.append( CONFIG["system_card"] )
    if CONFIG["external_cards"]:
        for ecard in CONFIG["external_cards"]:
            cards.append( CONFIG["external_cards"][ecard]["alsacard"] )
    return cards


def PA_release_card( pa_name ):
    """ Release the card from pulseaudio """
    try:
        sp.Popen( f'pactl set-card-profile {pa_name} off'.split() )
    except:
        print(  f'{Fmt.RED}'
                f'(sound_cards_prepare) PROBLEMS releasing '
                f'\'{pa_name}\' in pulseaudio{Fmt.END}' )


if __name__ == "__main__":

    if sys.argv[1:]:
        if sys.argv[1] == 'start':
            pass
        if sys.argv[1] == 'stop':
            sys.exit()
        elif '-h' in sys.argv[1]:
            print(__doc__)
            sys.exit()

    pa_cards        = get_pulse_cards()
    config_cards    = get_config_yml_cards()

    # Release cards from pulseaudio
    if pa_cards:
        for pa_card in pa_cards:
            for config_card in config_cards:
                if config_card.replace('hw:', '').split(',')[0] in \
                                        pa_cards[pa_card]["alsa_name"]:
                    PA_release_card( pa_cards[pa_card]["pa_name"] )

    # Restore ALSA mixer settigs for pa.audio.sys cards (config.yml)
    for card in config_cards:
        bareCardName = card.split(':')[-1].split(',')[0]

        asound_file = f'{MAINFOLDER}/.asound.{bareCardName}'
        try:
            if os.path.isfile( asound_file ):
                sp.Popen( f'alsactl -f {asound_file} \
                            restore {bareCardName}'.split() )
            else:
                raise
        except:
            print(  f'{Fmt.RED}'
                    f'(sound_cards_prepare) PROBLEMS restoring alsa: '
                    f'\'{bareCardName}\'{Fmt.END}' )
