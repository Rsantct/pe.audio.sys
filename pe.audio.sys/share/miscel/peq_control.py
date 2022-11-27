#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pe.audio.sys'
# 'pe.audio.sys', a PC based personal audio system.

"""
    Control module of a parametric equalizer.

    The parametric EQ is based on the 'fil' plugin (LADSPA) hosted under Ecasound.

    'fil' plugin is an excellent 4-band parametric eq from Fons Adriaensen,
    for more info see:
        http://kokkinizita.linuxaudio.org/



    Command line usage:             peq_control.py  cmd  arg1  arg2 ....

    Available commands and arguments:

    - PEQ_dump2peq                  Prints running parametric filters,
                                    also dumps them to LSPK_FOLDER/eca_dump.peq

    - PEQ_dump2ecs                  Prints running .ecs structure
                                    also dumps it to LSPK_FOLDER/eca_dump.ecs

    - PEQ_load_peq  file            Loads a .peq file of parameters in Ecasound

    - PEQ_bypass  on|off|toggle     Bypass the EQ

    - PEQ_gain  XX                  Sets EQ gain

    - ECA_cmd  cmd1 ... cmdN        Native ecasound-iam commands.
                                    (See man ecasound-iam)


    NOTE: .peq files are HUMAN READABLE PEQ settings,
          .ecs files are standard Ecasound chainsetup files.

"""

import  sys
import  os
from    time    import sleep
import  socket
import  yaml

from    miscel  import  LSPK_FOLDER, get_peq_in_use, \
                        read_bf_config_fs, wait4ports

import  jack_mod as jc


# The default file where running settins will be dumped
DUMPPATH =  f'{LSPK_FOLDER}/eca_dump.peq'

def ecanet(command):
    """ Sends commands to ecasound

        return: Ecasound response
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
        (void)
    """

    for chain in ("left", "right"):
        ecanet("c-select " + chain) # select channel
        ecanet("cop-select 1")      # select first filter stage
        ecanet("copp-select 2")     # select global gain
        ecanet("copp-set " + level) # set level


def eca_bypass(mode):
    """ mode: on | off | toggle
        (void)
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
    """ Dumps the RUNNIG chainsetup to a HUMAN READABLE FILE <fpath>

        returns: the HUMAN READABLE PEQ dictionary for later use.
    """

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
        res += f'#       global: [OnOff,            Gain]\n'
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
        print(f'\n(saved to: {fpath})')

    return d


def eca_dump2ecs(fpath=DUMPPATH.replace('.peq', '.ecs'), verbose=False):
    """ Dumps the RUNNING chainsetup to a file ECASOUND CHAINSTUP FILE <fpath>

        (i) This is a BUILT-IN Ecasound feature
    """
    ecanet( f'cs-save-as {fpath}')

    if verbose:
        with open(fpath, 'r') as f:
            print( f.read() )
        print(f'\n(saved to: {fpath})')


def peq_dump2ecs(d, csname):
    """ Dumps the GIVEN PEQ DICT to a chainsetup file '<csname>.ecs'

        Returns the string '<csname>.ecs' for later use.
    """
    chainsetup  = eca_make_chainsetup(d, csname=csname)
    ecspath     = f'{LSPK_FOLDER}/{csname}.ecs'
    with open(ecspath, 'w') as f:
        f.write( chainsetup)
    return ecspath


def peq_read(fpath=DUMPPATH):
    """ Reads a PEQ filter set from a given human readable file

        returns: a dictionary with filters setup
    """
    d = {}

    with open(fpath, 'r') as f:
        c = f.read()

    try:
        d = yaml.safe_load(c)
    except Exception as e:
        print(str(e))

    return d


def eca_make_chainsetup(d, csname):
    """ d:       Dictionary with fil plugin parameters

        returns: Text chainsetup to be saved to a file
                 for ecasound cs-load usage
    """

    def make_header():
        res =  '# ecasound chainsetup file'
        res += '\n\n'
        return res


    def make_general():
        res =   '# general\n'
        res += f'-b:2048 -r:50 -z:intbuf -z:db,100000 -n:"{csname}" -X -z:noxruns -z:nopsr -z:mixmode,avg'
        res += '\n\n'
        return res


    def make_audio_io(fs=441000):
        res  = f'# audio inputs\n'
        res += f'-a:left -f:f32_le,1,{fs} -i:jack,,\n'
        res += f'-a:right -f:f32_le,1,{fs} -i:jack,,\n'
        res += f'\n'
        res += f'# audio outputs\n'
        res += f'-a:left -f:f32_le,1,{fs} -o:jack,,\n'
        res += f'-a:right -f:f32_le,1,{fs} -o:jack,,\n'
        res += '\n'
        return res


    def make_chain(cname):
        res = f'-a:{cname}'
        for fil in d[cname]:
            res += f' -eli:1970'
            for k in d[cname][fil]:
                for x in d[cname][fil][k]:
                    res += f',{x}'
        return res


    res =  make_header()

    res += make_general()

    res += make_audio_io( fs=read_bf_config_fs() )

    res += '# chain operators and controllers\n'
    for cname in d:
        res += f'{make_chain(cname)}\n'

    return res


def eca_load_peq(peqpath=DUMPPATH):
    """ Loads a .peq file of parameters in ecasound

        returns: the Ecasound responses after loading, connecting
                 and restarting the engine

        (WARNING)   Ecasound will stop engine and will release all I/O
                    when loading a chainsetup
    """

    d = peq_read(peqpath)

    csname = os.path.basename(peqpath)

    # Ecasound needs a file to load a chainsetup from,
    # so let's make a temporary one
    tmppath = peq_dump2ecs(d, csname)

    res =  ecanet( f'cs-load {tmppath}' )
    res += ecanet( f'cs-select {csname}' )
    res += ecanet(  'cs-connect' )
    res += ecanet(  'start' )
    sleep(.5)
    res += ecanet(  'engine-status' )

    return res


def insert_ecasound(verbose=False):

    wait4ports('ecasound', timeout=5)
    wait4ports('brutefir', timeout=60)

    jc.connect_bypattern('pre_in_loop', 'brutefir', 'disconnect')
    jc.connect_bypattern('pre_in_loop', 'ecasound')
    jc.connect_bypattern('ecasound',    'brutefir')

    if verbose:
        print( f'(peq_control) inserting pre_in --> ecasound --> brutefir' )


if __name__ == '__main__':

    # is ecasound listening?
    if not ecanet(''):
        print("(!) no answer from Ecasound server")
        sys.exit()

    # we can pass more than one command from command line to ecasound
    if sys.argv[1:]:

        cmd  = sys.argv[1]
        args = sys.argv[2:]

        if   cmd == "ECA_cmd":
            for ecaCmd in args:
                print( ecanet(ecaCmd) )

        elif cmd == "PEQ_dump2peq":
            eca_dump2peq(verbose=True)

        elif cmd == "PEQ_dump2ecs":
            eca_dump2ecs(verbose=True)

        elif cmd == "PEQ_load_peq" and args:
            eca_load_peq(args[0])

        elif cmd == "PEQ_bypass" and args:
            eca_bypass(args[0])

        elif cmd == "PEQ_gain" and args:
            eca_gain(args[0])

        else:
            print(f'(!) Bad command')
            print(__doc__)

    else:
        print(__doc__)
