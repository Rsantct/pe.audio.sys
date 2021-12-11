#!/usr/bin/env python3
"""
    A module to tune a Mplayer radio station and listen to it.
"""
from os.path import expanduser
import sys
UHOME = expanduser("~")
sys.path.append(f'{UHOME}/pe.audio.sys')
from share.miscel import *
from time import sleep
from subprocess import Popen


# DEFAULT CONFIG: intended to be modified when importing this module
#                 from a real user macro N_xxxxxxx

mplayer_profile = 'istreams'    # choose an Mplayer profile: "istreams", "dvb"
preset          = 1
lu_offset       = 9
loudness_comp   = 'off'
xo_pattern      = 'mp'
drc_pattern     = 'mp'


def main():

    ME = __file__.split('/')[-1]

    # Prepare to use the proper share/scripts/xxxx.py and preamp input
    if mplayer_profile == 'dvb':
        script   = 'DVB-T.py'
        preinput = 'tdt'
    elif mplayer_profile == 'istreams':
        script   = 'istreams.py'
        preinput = 'istreams'
    else:
        print( f'{Fmt.RED}(macros) Bad Mplayer profile \'{mplayer_profile}\'{Fmt.END}' )
        sys.exit()

    # Pausing the current player
    send_cmd( f'player pause', sender=ME, verbose=True )

    # Warning message
    send_cmd( f'aux warning clear' )
    send_cmd( f'aux warning set tuning takes a while ...' )

    # Tune the radio station (Mplayer jack ports will dissapear for a while)
    Popen( f'{UHOME}/pe.audio.sys/share/scripts/{script} preset {str(preset)}'
            .split() )
    # Wait a bit for current ports to disappear
    sleep(3)

    # Check for Mplayer ports to re-emerge
    if not wait4ports( f'mplayer_{mplayer_profile}', timeout=45):
        print(f'{Fmt.RED}({ME}) ERROR jack ports \'mplayer_{mplayer_profile}\' not found, '
              f'bye :-/{Fmt.END}')
        # Warning message
        send_cmd( f'aux warning clear' )
        sys.exit(-1)

    sleep(.5)

    # Warning message
    send_cmd( f'aux warning clear' )

    # Switching the preamp input
    send_cmd( f'input {preinput}', sender=ME, verbose=True )
    sleep(.5)

    # Loudness compensation on|off
    send_cmd( f'loudness {loudness_comp}', sender=ME, verbose=True )
    sleep(.5)

    # LU level compensation reference
    send_cmd( f'lu_offset {lu_offset}', sender=ME, verbose=True )
    sleep(.5)

    # XO
    if xo_pattern:
        set_as_pattern('xo', xo_pattern, sender=ME, verbose=True)
        sleep(.5)

    # DRC
    if drc_pattern:
        set_as_pattern('drc', drc_pattern, sender=ME, verbose=True)
        sleep(.5)
