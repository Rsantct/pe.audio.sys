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

from    sound_cards  import  get_config_cards, alsa_device2short_name, Fmt


def restore_alsa_card(card):

        asound_file = f'{UHOME}/pe.audio.sys/config/asound.{card}'

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


def restore_cards(alsa_devices):
    """ Restore mixer settigs for pa.audio.sys cards (config.yml)
    """
    # Avoiding duplicates, such 'hw:PCH,0' (analog section) and 'hw:PCH,1' (digital)
    restored = []

    for dev in alsa_devices:

        card = alsa_device2short_name(dev)

        if card not in restored:

            # ALSA
            if 'hw:' in dev:
                restore_alsa_card(card)
            # FFADO
            elif 'guid:' in dev:
                restore_ffado_card(card)
            else:
                print(  f'{Fmt.RED}'
                        f'(sound_cards_prepare) UNKNOWN card type: '
                        f'\'{dev}\'{Fmt.END}' )

            restored.append(card)


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

    restore_cards( get_config_cards() )
