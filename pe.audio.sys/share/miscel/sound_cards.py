#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pe.audio.sys'
# 'pe.audio.sys', a PC based personal audio system.

""" sound cards related functions
"""

import  subprocess as sp
import  difflib
from    config  import CONFIG
from    fmt     import Fmt


def simmilar_strings(a, b):
    ratio =  difflib.SequenceMatcher(a=a.lower(), b=b.lower()).ratio()
    if (ratio >= 0.60):
        return True
    else:
        return False


def get_aplay_cards():
    """ Returns a dictionary of cards as listed in 'aplay -l'
    """
    alsa_cards = {}
    try:
        aplay = sp.check_output('aplay -l'.split()).decode().split('\n')
    except:
        aplay = []

    for line in aplay:
        if line.startswith('card '):
            cnum  = line.split(':')[0].split()[1]
            sname = line.split(':')[1].split('[')[0].strip()
            fname = line.split('[')[1].split(']')[0]
            alsa_cards[cnum] = {'short_name':sname, 'long_name':fname}
    return alsa_cards


def get_config_cards():
    """ List of pe.audio.sys 'hx:XXX,N' configured cards (alsa_devices)
    """
    cards = [ CONFIG["system_card"] ]
    if CONFIG["external_cards"]:
        for ecard in CONFIG["external_cards"]:
            cards.append( CONFIG["external_cards"][ecard]["alsacard"] )
    return cards


def alsa_device2short_name(device_string):
    """ Example:
        Given 'hw:Intel,0', then returns 'Intel'
    """
    return device_string.split(':')[-1].split(',')[0]


def alsa_short2long_name(sname):
    """ Example:

            $ aplay -l
            **** List of PLAYBACK Hardware Devices ****
            card 0: PCH [HDA Intel PCH], device 0: ALC889 Analog [ALC889 Analog]

        Given sname='PCH', then returns 'HDA Intel PCH', as used in PA.alsa.card_name
    """
    result = sname
    aplaycards = get_aplay_cards()
    for apc in aplaycards:
        if sname == aplaycards[apc]['short_name']:
            result = aplaycards[apc]['long_name']
    return result


def get_pulse_cards():
    """ Return a dictionary of cards as listed in 'pactl list cards'
    """
    pa_cards = {}

    try:
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

    except Exception as e:
        pass

    return pa_cards


def release_cards_from_pulseaudio():
    """ Release pe.audio.sys cards from Pulseaudio
    """

    def PA_release_card( pa_name ):
        """ Release a card from pulseaudio """
        try:
            sp.Popen( f'pactl set-card-profile {pa_name} off', shell=True )
            print(  f'{Fmt.BLUE}'
                    f'(sound_cards) releasing '
                    f'\'{pa_name}\' in pulseaudio{Fmt.END}' )

        except Exception as e:
            print(  f'{Fmt.RED}'
                    f'(sound_cards) PROBLEMS releasing '
                    f'\'{pa_name}\' in pulseaudio: {str(e)}{Fmt.END}' )


    pulse_cards  = get_pulse_cards()
    for pc in pulse_cards:
        for cc in get_config_cards():
            cc_short_name = alsa_device2short_name(cc)
            cc_long_name = alsa_short2long_name(cc_short_name)
            if pulse_cards[pc]["alsa_name"] == cc_long_name:
                PA_release_card( pulse_cards[pc]["pa_name"] )
                break
