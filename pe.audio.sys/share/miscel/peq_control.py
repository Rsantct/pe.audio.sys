#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pe.audio.sys'
# 'pe.audio.sys', a PC based personal audio system.

"""
    Control module of a parametric ecualizer based on ecasound

    Usage: peq_control.py cmd arg1 arg2 ....

    Avalible commands and arguments:

    - ECAcmd cmd1 ... cmdN     native ecasound-iam command (man ecasound-iam)

    - PEQdump                  prints running parametric filters

    - PEQdump2ecs              prints running .ecs structure

    - PEQbypass on|off|toggle  bypass the EQ

    - PEQgain XX               sets EQ gain

"""

import  sys
import  os
from    time    import sleep
import  socket
import  yaml

from    miscel  import UHOME, LSPK_FOLDER, get_peq_in_use

# The file where init settings will be loaded from
PEQPATH  = ''

# The file where current settins will be dumped
DUMPPATH =  f'{LSPK_FOLDER}/peqdump.peq'

def ecanet(command):
    """ Sends commands to ecasound and accept results
    """

    # Note:   - ecasound needs CRLF
    #         - socket send and receive bytes (not strings),
    #           hence .encode() and .decode()

    data = b''
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect( ('localhost', 2868) )
        s.send( (command + '\r\n').encode() )
        data = s.recv( 8192 )
        s.close()
    except Exception as e:
        pass

    return data.decode()


def eca_gain(level):
    """ set gain in first plugin stage
    """

    for chain in ("left", "right"):
        ecanet("c-select " + chain) # select channel
        ecanet("cop-select 1")      # select first filter stage
        ecanet("copp-select 2")     # select global gain
        ecanet("copp-set " + level) # set level


def eca_bypass(mode):
    """ mode: on | off | toggle
    """

    for chain in ("left", "right"):
        ecanet("c-select " + chain)
        ecanet("c-bypass " + mode)
        sleep(.2)

    for chain in ecanet("c-status").replace("[selected] ", "").split("\n")[2:4]:
        tmp = ""
        if "bypass" in chain.split()[2]:
            tmp = chain.split()[2]
        print((" ".join(chain.split()[:2]) + " " + tmp))


def eca_dump2peq(fpath=DUMPPATH, verbose=False):

    def PEQdic2dump(d):
        """ Makes a human readable multiline string
            Saves it to a <fpath>,
            and returns it.
        """

        def list2str(l):
            """ Stringify a list of Parametric EQ settings
                to be more readable.

                Example:

                    global: [OnOff, Gain]
                    pN:     [OnOff, Frec, BW,  Gain]

                    global: [1,                  0.0]
                    p0:     [0,   4000,   1.0,  -1.0]
            """

            res =  '['

            res += f'{ int(l[0]) }, '                       # OnOff

            if len(l) == 2:                                 # Global:
                res += ' '*16
                res += f'{ str(round(l[1], 1)).rjust(3)}, ' # Gain

            else:                                           # Parametric <pN>
                res += f'{ str(round(l[1]   )).rjust(6)}, ' # Hz
                res += f'{ str(round(l[2], 1)).rjust(5)}, ' # BW
                res += f'{ str(round(l[3], 1)).rjust(4)}, ' # Gain

            res = res[:-2]
            res += ']'
            return res


        spc4 = ' ' * 4
        spc8 = ' ' * 8

        res =   '# Legend:\n'
        res += f'#       global: [OnOff, Gain]\n'
        res += f'#       pN:     [OnOff, Frec, BW,  Gain]\n'
        res +=  '#\n'

        for c in d:
            res += '\n'
            res += f'{c}:\n'

            for fil in d[c]:
                res += f'{spc4}{fil}:\n'

                for x in d[c][fil]:
                    plist = d[c][fil][x]
                    if x == 'global':
                        res += f'{spc8}{x}: {list2str(plist)}\n'
                    else:
                        res += f'{spc8}{x}:     {list2str(plist)}\n'

        try:
            with open(fpath, 'w') as f:
                f.write(res)
            print(f'saved: {fpath}')

        except Exception as e:
            print(f'{Fmt.BOLD}{str(e)}{Fmt.END}')

        return res


    def chainsetup_parse(ecaString):
        """
        Example from 'fil-plugin' 8-band dual mono Ecasound chainsetup:

        256 827 s
        ### Chainsetup status ###
        Chainsetup (1) "fil_8_band_dualMono" [selected] [connected]
         -> Objects..: 2 inputs, 2 outputs, 2 chains
         -> State....: connected to engine (engine status: running)
         -> Position.:  9898.992 / 0.000
         -> Options..: -b:2048 -r:50 -z:intbuf -z:nodb -n:"fil_8_band_dualMono" -X -z:noxruns -z:nopsr -z:mixmode,avg
         -> Chain "left": -i:jack,, -eli:1970,1.00,0.00,0.00,10.00,1.00,0.00,0.00,10.00,1.00,0.00,0.00,10.00,1.00,0.00,0.00,10.00,1.00,0.00 -eli:1970,1.00,0.00,0.00,10.00,1.00,0.00,0.00,10.00,1.00,0.00,0.00,10.00,1.00,0.00,0.00,10.00,1.00,0.00 -o:jack,,
         -> Chain "right": -i:jack,, -eli:1970,1.00,0.00,0.00,10.00,1.00,0.00,0.00,10.00,1.00,0.00,0.00,10.00,1.00,0.00,0.00,10.00,1.00,0.00 -eli:1970,1.00,0.00,0.00,10.00,1.00,0.00,0.00,10.00,1.00,0.00,0.00,10.00,1.00,0.00,0.00,10.00,1.00,0.00 -o:jack,,

        Will return:

        {'left':
            {'fil_0': [ '1.00', '0.00',
                        '0.00', '10.00', '1.00', '0.00',
                        '0.00', '10.00', '1.00', '0.00',
                        '0.00', '10.00', '1.00', '0.00',
                        '0.00', '10.00', '1.00', '0.00'],
             'fil_1': [ '1.00', '0.00',
                        '0.00', '10.00', '1.00', '0.00',
                        '0.00', '10.00', '1.00', '0.00',
                        '0.00', '10.00', '1.00', '0.00',
                        '0.00', '10.00', '1.00', '0.00']},

          'right':
                ...
                ...
        }

        """
        d = {}

        ecaList = ecaString.split("\n")

        for chId in 'left', 'right':

            tmp = [x for x in ecaList if f'Chain "{chId}"'  in x]

            if tmp:
                tmp = tmp[0]

            if tmp:
                tmp = [x for x in tmp.split() if '-eli:1970' in x]

            if tmp:
                tmp = [x.replace('-eli:1970,','') for x in tmp]

            d[chId] = {}
            for i in range(len(tmp)):
                d[chId][f'fil_{i}'] = tmp[i].split(',')

        # Let's parse the detailed global and 4-bands for each fil
        for ch in d:

            for fil in d[ch]:
                tmp = d[ch][fil]
                # redefine the former list as dict
                d[ch][fil] = {}
                d[ch][fil]["global"] = [round(float(x), 2) for x in tmp[:2]]

                for i in range(4):
                    tmp2 = tmp[2+i*4 : 6+i*4]
                    d[ch][fil][f'p{i}'] = [round(float(x), 2) for x in tmp2]

        return d


    d = chainsetup_parse( ecanet("cs-status") )

    dumped = PEQdic2dump( d )

    if verbose:
        print(dumped)

    return d


def eca_dump2ecs():
    """ (i) This is a BUILT-IN Ecasound feature
    """
    ecanet( f"cs-save-as {UHOME}/tmp.ecs" )
    with open( f"{UHOME}/tmp.ecs", "r" ) as f:
        print((f.read()))
    os.remove( f"{UHOME}/tmp.ecs" )


def peq_read(fpath=DUMPPATH):
    """ Reads a PEQ filter set from a given human readable file
    """
    d = {}

    with open(fpath, 'r') as f:
        c = f.read()

    try:
        d = yaml.safe_load(c)
    except Exception as e:
        print(str(e))

    return d


if __name__ == '__main__':

    # is ecasound listening?
    if not ecanet(''):
        print("(!) no answer from ecasound server")
        sys.exit()

    # we can pass more than one command from command line to ecasound
    if sys.argv[1:]:

        cmd  = sys.argv[1]
        args = sys.argv[2:]

        if   cmd == "ECAcmd":
            for ecaCmd in args:
                print( ecanet(ecaCmd) )

        elif cmd == "PEQdump":
            eca_dump2peq(verbose=True)

        elif cmd == "PEQdump2ecs":
            eca_dump2ecs()

        elif cmd == "PEQbypass" and args:
            eca_bypass(args[0])

        elif camd == "PEQgain":
            eca_gain(arg)

        else:
            print(("(!) Bad command: " + command))
            print(__doc__)

    else:
        print(__doc__)
