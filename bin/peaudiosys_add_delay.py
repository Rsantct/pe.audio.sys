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
sys.path.append(f'{UHOME}/pe.audio.sys/share/services/preamp_mod')
from start import get_Bfir_sample_rate
from core  import bf_cli, LSPK_FOLDER


def get_config_outputs():
    """ Read outputs from 'brutefir_config' file, then gets a dictionary.
    """
    outputs = {}

    bfconfig_file = f'{LSPK_FOLDER}/brutefir_config'
    with open(bfconfig_file, 'r') as f:
        bfconfig = f.read().split('\n')

    output_section = False

    for line in bfconfig:

        line = line.split('#')[0]
        if not line:
            continue

        if   line.strip().startswith('logic') or \
             line.strip().startswith('coeff') or \
             line.strip().startswith('input') or \
             line.strip().startswith('filter'):
                output_section = False
        elif line.strip().startswith('output'):
                output_section = True

        if not output_section:
            continue

        line = line.strip()

        if line.startswith('output') and '{' in line:
            output_section = True
            if output_section:
                outs = line.replace('output', '').replace('{', '').split(',')
                outs = [ x.replace('"', '').strip() for x in outs ]

        if line.startswith('delay:'):
            i = 0
            delays = line.replace('delay:', '').split(';')[0].strip().split(',')
            delays = [ int(x.strip()) for x in delays ]
            for oname, delay in zip(outs, delays):
                outputs[str(i)] = {'name': oname, 'delay': delay}
                i += 1

        if line.startswith('maxdelay:'):
            maxdelay = int( line.split(':')[1].replace(';', '').strip() )
            outputs['maxdelay'] = maxdelay

    return outputs


def get_current_outputs():
    """ Read outputs from running Brutefir, then gets a dictionary.
    """

    lines = bf_cli('lo').split('\n')
    outputs = {}

    i = lines.index('> Output channels:') + 1

    while True:

        onum = lines[i].split(':')[0].strip()

        outputs[str(onum)] = {
            'name':  lines[i].split(':')[1].strip().split()[0].replace('"', ''),
            'delay': int(lines[i].split()[-1].strip().replace(')', '').split(':')[0])
        }

        i += 1
        if not lines[i] or lines[i] == '':
            break

    return outputs


def list_outputs(outs):
    """ Prints out a Brutefir's outputs list
    """
    maxdelay    = outputs['maxdelay']
    maxdelay_ms = int( maxdelay / FS  * 1e3)

    print( f'Brutefir max available outputs delay: {maxdelay} samples ({maxdelay_ms} ms)' )
    print()
    for o in outs:
        oname = outs[o]['name']
        delay = outs[o]['delay']
        ms =    round( delay / 44100 * 1000, 3 )
        print( o, oname.ljust(8), f'{str(delay).rjust(5)} samples', f'({ms} ms)' )


def set_delay(ms):
    """ Will add a delay on all outputs, relative to 'brutefir_config'
        outputs delay array values.
    """

    # From ms to samples
    delay = int( FS  * ms / 1e3)

    cmd = ''
    too_much = False
    max_available = outputs['maxdelay']

    for o in outputs:

        # Skip non output number item (i.e. the  maxdelay item)
        if not o.isdigit():
            continue

        cfg_delay = outputs[o]['delay']
        new_delay = int(cfg_delay + delay)
        if new_delay > outputs['maxdelay']:
            too_much = True
            max_available = outputs['maxdelay'] - cfg_delay
        cmd += f'cod {o} {new_delay};'

    # Issue new delay on Brutefir's outputs
    if not too_much:
        #print(cmd) # debug
        result = bf_cli( cmd ).lower()
        #print(result) # debug
        if not 'unknown command' in result and \
           not 'out of range' in result and \
           not 'invalid' in result and \
           not 'error' in result:
                return 'done'
        else:
                return 'Brutefir error'
    else:
        print(f'(i) Not set because Brutefir\'s maxdelay was exceeded.')
        print(f'    Your limit is {int(max_available / FS * 1e3)} ms')
        return 'exceeded'


if __name__ == '__main__':

    # Getting configured outputs
    outputs = get_config_outputs()

    # Getting FS from start.py module, and redirecting
    # stdout temporary to ignore its printouts.
    original_stdout = sys.stdout
    with open('/dev/null', 'w') as devnull:
        sys.stdout = devnull
        FS = int( get_Bfir_sample_rate() )
    sys.stdout = original_stdout

    # Reading command line
    if sys.argv[1:]:

        if '-l' in sys.argv[1]:
            list_outputs( get_current_outputs() )
            sys.exit()

        delay = float(sys.argv[1])

        print( set_delay(delay) )
        #list_outputs( get_current_outputs() )

    else:
        print(__doc__)
