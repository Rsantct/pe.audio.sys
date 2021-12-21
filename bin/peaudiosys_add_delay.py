#!/usr/bin/env python3
"""
    Adds Brutefir's outputs delay.

    This tool is intended to compensate for multiroom listening tuning,
    anyway you can use the command 'aux add_delay X'

    Usage:

        peaudiosys_add_delay.py  <additional delay> | --list

    You can reserve a 'maxdelay' value in samples inside 'brutefir_config'.

    More details here:
        https://torger.se/anders/brutefir.html#config_4

"""
import  sys
import  os

UHOME = os.path.expanduser("~")
sys.path.append(f'{UHOME}/pe.audio.sys/share')

print( 'importing modules takes a while ...')
from  miscel_mod    import brutefir_mod as bf
from  miscel        import send_cmd, get_bf_samplerate


def print_delays():
    """ Prints out the delays on Brutefir outputs.
    """
    FS          = int( get_bf_samplerate() )
    outs        = bf.get_current_outputs()
    maxdelay    = int( bf.get_config()['maxdelay'] )
    maxdelay_ms = int( maxdelay / FS  * 1e3)

    print( f'Brutefir max available outputs delay: {maxdelay} samples ({maxdelay_ms} ms)' )
    print

    for o in outs:
        if not o.isdigit():    # currently not necessary
            continue
        oname = outs[o]['name']
        delay = outs[o]['delay']
        ms =    round( delay / 44100 * 1000, 3 )
        print( o, oname.ljust(8), f'{str(delay).rjust(5)} samples', f'({ms} ms)' )


if __name__ == '__main__':


    # Resuming Brutefir from powesave
    if not bf.is_running():
        print( 'resuming Brutefir from powersave ...')
        print( send_cmd('convolver on') )

    # Test if Brutefir is available
    test = bf.cli('')
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

        else:
            try:
                delay = float(opc)
                print( 'adding delay: ', bf.add_delay(delay) )
            except:
                print( f'bad delay \'{opc}\'' )

