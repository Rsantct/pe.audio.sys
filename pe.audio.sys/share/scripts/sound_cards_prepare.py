#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pe.audio.sys'
# 'pe.audio.sys', a PC based personal audio system.

"""
    Prepapare sound cards to be used under pe.audio.sys.

    This is optional, but recommended.

    Cards to be prepared are 'system_card' and 'external_cards'
    as defined under config.yml

    ALSA mixer setting must be previously available under

        ~/pe.audio.sys/config/asound.XXXXX

    where XXXXX stands for the alsa card name (without 'hw:' prefix)

    Example:

    Prepare your alsamixer settings for MYCARD, then execute the following:

        alsactl -f ~/pe.audio.sys/config/asound.MYCARD store MYCARD

"""
import  difflib
import  subprocess as sp
import  os
import  sys

UHOME = os.path.expanduser("~")
sys.path.append(f'{UHOME}/pe.audio.sys/share/miscel')

from    config  import CONFIG
from    miscel  import Fmt


def simmilar_strings(a, b):
    ratio =  difflib.SequenceMatcher(a=a.lower(), b=b.lower()).ratio()
    if ratio >= 0.75:
        return True
    else:
        return False


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
        print(  f'{Fmt.BLUE}'
                f'(sound_cards_prepare) releasing '
                f'\'{pa_name}\' in pulseaudio{Fmt.END}' )
    except:
        print(  f'{Fmt.RED}'
                f'(sound_cards_prepare) PROBLEMS releasing '
                f'\'{pa_name}\' in pulseaudio{Fmt.END}' )


def restore_alsa_card(card):

        bareCardName = card.split(':')[-1].split(',')[0]

        asound_file = f'{UHOME}/pe.audio.sys/config/asound.{bareCardName}'
        try:
            if os.path.isfile( asound_file ):
                sp.Popen( f'alsactl -f {asound_file} \
                            restore {bareCardName}'.split() )
                print(  f'{Fmt.BLUE}'
                        f'(sound_cards_prepare) restoring alsa settings: '
                        f'\'{asound_file}\'{Fmt.END}' )
            else:
                print(  f'{Fmt.RED}'
                        f'(sound_cards_prepare) restoring alsa settings: '
                        f'\'{asound_file}\' NOT FOUND{Fmt.END}' )
        except:
            print(  f'{Fmt.RED}'
                    f'(sound_cards_prepare) PROBLEMS restoring alsa: '
                    f'\'{bareCardName}\'{Fmt.END}' )


def restore_ffado_card(card):
    ''' FFADO firewire cards needs a custom made script, named like:

            ~/pe.audio.sys/config/ffado.0x00130e01000406d2.sh

        where 0x...... is the firewire GUID (see ffado-test ListDevices)

        For details about this script see the 'doc/' folder.
    '''

    guid = card.replace('guid:','')
    scriptPath = f'{UHOME}/pe.audio.sys/config/ffado.{guid}.sh'

    if os.path.isfile( scriptPath ):
        print(  f'{Fmt.BLUE}'
                f'(sound_cards_prepare) restoring ffado settings for: '
                f'\'{card}\'{Fmt.END}' )
        sp.Popen( f'sh {scriptPath} 1>/dev/null 2>&1', shell=True)

    else:
        print(  f'{Fmt.RED}'
                f'(sound_cards_prepare) ERROR restoring ffado settings: '
                f'\'{scriptPath}\' NOT FOUND.{Fmt.END}' )


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
    for pa_card in pa_cards:
        for config_card in config_cards:

            # alsa
            ccname = config_card.replace('hw:', '').split(',')[0]
            # firewire
            ccname = config_card.replace('guid:', '').split(',')[0]

            for paname in pa_cards[pa_card]["alsa_name"], \
                          pa_cards[pa_card]["pa_name"]:

                if simmilar_strings(ccname, paname):
                    PA_release_card( pa_cards[pa_card]["pa_name"] )
                    break

    # Restore ALSA mixer settigs for pa.audio.sys cards (config.yml)
    for card in config_cards:

        if 'hw:' in card:
            restore_alsa_card(card)

        elif 'guid:' in card:
            restore_ffado_card(card)

        else:
            print(  f'{Fmt.RED}'
                    f'(sound_cards_prepare) UNKNOWN card type: '
                    f'\'{card}\'{Fmt.END}' )
