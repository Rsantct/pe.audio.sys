#!/usr/bin/env python3
"""
    Adds Brutefir's outputs delay.

    This tool is intended to compensate for multiroom listening.

    Usage:

        peaudiosys_add_delay.py  <additional delay> | --list

    You can reserve a 'maxdelay' value in samples inside 'brutefir_config'.

    More details here:
        https://torger.se/anders/brutefir.html#config_4

"""
import sys
import os
UHOME = os.path.expanduser("~")
sys.path.append(f'{UHOME}/pe.audio.sys')
sys.path.append(f'{UHOME}/pe.audio.sys/share')
from miscel import *


def print_delays():
    """ Prints out the delays on Brutefir outputs.
    """
    FS          = int( bf_get_sample_rate() )
    outs        = bf_get_current_outputs()
    maxdelay    = outs['maxdelay']
    maxdelay_ms = int( maxdelay / FS  * 1e3)

    print( f'Brutefir max available outputs delay: {maxdelay} samples ({maxdelay_ms} ms)' )
    print

    for o in outs:
        # skipping the maxdelay dict field
        if not o.isdigit():
            continue
        oname = outs[o]['name']
        delay = outs[o]['delay']
        ms =    round( delay / 44100 * 1000, 3 )
        print( o, oname.ljust(8), f'{str(delay).rjust(5)} samples', f'({ms} ms)' )


if __name__ == '__main__':

    # Test if Brutefir is available
    test = bf_cli('')
    if not test:
        print( 'Brutefir not available')
        sys.exit()


    # Reading command line
    for opc in sys.argv[1:]:

        if   '-h' in opc:
            print(__doc__)
            sys.exit()

        elif '-l' in opc:
            print_delays()
            sys.exit()

        elif opc.isdigit():
            delay = float(sys.argv[1])
            print( bf_add_delay(delay) )

