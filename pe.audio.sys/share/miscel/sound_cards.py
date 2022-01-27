#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pe.audio.sys'
# 'pe.audio.sys', a PC based personal audio system.

""" sound cards related functions
"""

import  subprocess as sp
import  os

from    config  import CONFIG, MAINFOLDER
from    fmt     import Fmt


def restore_alsa_mixer(card):
    """ Call 'altactl' to restore mixer settings from a previously saved file.
    """

    asound_file = f'{MAINFOLDER}/config/asound.{card}'

    try:
        if os.path.isfile( asound_file ):
            sp.Popen( f'alsactl -f {asound_file} restore {card}',
                      shell=True )
            print(  f'{Fmt.BLUE}'
                    f'(sound_cards_prepare) restoring alsa settings: '
                    f'\'{asound_file}\'{Fmt.END}' )
        else:
            print(  f'{Fmt.RED}'
                    f'(sound_cards_prepare) restoring alsa settings: '
                    f'\'{asound_file}\' NOT FOUND{Fmt.END}' )

    except Exception as e:
        print(  f'{Fmt.RED}'
                f'(sound_cards_prepare) PROBLEMS restoring alsa '
                f'\'{card}\': {str(e)}{Fmt.END}' )


def restore_ffado_mixer(card):
    ''' Restore mixer settings from a previously saved file.

        FFADO firewire cards need a custom made script, named like:

            ~/pe.audio.sys/config/ffado.0x00130e01000406d2.sh

        where 0x...... is the firewire GUID (see ffado-test ListDevices)

        For details about this script see the 'doc/' folder.
    '''

    guid = card.replace('guid:','')
    scriptPath = f'{MAINFOLDER}/config/ffado.{guid}.sh'

    if os.path.isfile( scriptPath ):
        print(  f'{Fmt.BLUE}'
                f'(sound_cards_prepare) restoring ffado settings for: '
                f'\'{card}\'{Fmt.END}' )
        sp.Popen( f'sh {scriptPath} 1>/dev/null 2>&1', shell=True)

    else:
        print(  f'{Fmt.RED}'
                f'(sound_cards_prepare) ERROR restoring ffado settings: '
                f'\'{scriptPath}\' NOT FOUND.{Fmt.END}' )


def restore_all_cards_mixers():
    """ Restore mixer settigs for all pa.audio.sys cards (config.yml)
    """

    # Avoiding duplicates, such 'hw:PCH,0' (analog section) and 'hw:PCH,1' (digital)
    restored = []

    for dev in get_config_sound_devices():

        card = alsa_device2card(dev)

        if card not in restored:

            # ALSA
            if 'hw:' in dev:
                restore_alsa_mixer(card)
            # FFADO
            elif 'guid:' in dev:
                restore_ffado_mixer(card)
            else:
                print(  f'{Fmt.RED}'
                        f'(sound_cards_prepare) UNKNOWN card type: '
                        f'\'{dev}\'{Fmt.END}' )

            restored.append(card)


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


def get_config_sound_devices():
    """ List of pe.audio.sys 'hx:XXX,N' configured sound devices
    """
    devices = [ CONFIG["jack"]["device"] ]
    ext_cards = CONFIG["jack"]["external_cards"]
    if ext_cards:
        for card in ext_cards:
            devices.append( ext_cards[card]["device"] )
    return devices


def alsa_device2card(device_string):
    """ Example:
        Given an ALSA device 'hw:Intel,0', then returns the card name 'Intel'
    """
    return device_string.split(':')[-1].split(',')[0]


def alsa_card_long_name(card):
    """ Example:

            $ aplay -l
            **** List of PLAYBACK Hardware Devices ****
            card 0: PCH [HDA Intel PCH], device 0: ALC889 Analog [ALC889 Analog]

        Given card='PCH', then returns 'HDA Intel PCH', as used in PA.alsa.card_name
    """
    result = card
    aplaycards = get_aplay_cards()
    for apc in aplaycards:
        if card == aplaycards[apc]['short_name']:
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
        for cdev in get_config_sound_devices():
            cname = alsa_device2card(cdev)
            cname = alsa_card_long_name(cname)
            if pulse_cards[pc]["alsa_name"] == cname:
                PA_release_card( pulse_cards[pc]["pa_name"] )
                break
