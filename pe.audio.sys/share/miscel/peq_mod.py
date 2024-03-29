#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pe.audio.sys'
# 'pe.audio.sys', a PC based personal audio system.

"""
    Module to manage a parametric equalizer hosted in Ecasound.

    The parametric EQ is based on the 'fil' plugin (LADSPA).

    'fil' plugin is an excellent 4-band parametric eq from Fons Adriaensen,
    for more info see:
        http://kokkinizita.linuxaudio.org/


    NOTE: .peq files are HUMAN READABLE PEQ settings,
          .ecs files are standard Ecasound chainsetup files.

    ( A command line tool is provided at ~/bin/peaudiosys_peq.py )
"""

import  sys
import  os
from    time    import sleep
import  socket
import  yaml

from    miscel  import  LSPK_FOLDER, get_peq_in_use, \
                        read_bf_config_fs, wait4ports


# The default dump files where running settins will be dumped
PEQDUMPPATH = f'{LSPK_FOLDER}/eca_dump.peq'
ECSDUMPPATH = f'{LSPK_FOLDER}/eca_dump.ecs'


def ecanet(command):
    """ Sends commands to ecasound

        return: Ecasound response
    """

    # Note:   - ecasound needs CRLF
    #         - socket send and receive bytes (not strings),
    #           hence .encode() and .decode()
    #         - filename or chain-setup-name spaces needs to be escaped

    data = b''
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect( ('localhost', 2868) )
        s.send( (command + '\r\n').encode() )
        data = s.recv( 8192 )
        s.close()
    except Exception as e:
        pass

    return data.decode().strip()


def eca_gain(level):
    """ set gain in last 'fil' stage
        (void)
    """
    def get_last_fil_index():
        tmp = ecanet("cop-list").split('\r\n')
        cops = tmp[1].split(',')
        i = -1
        for cop in cops:
            if '4-band parametric filter' in cop:
                i += 1
        return i

    for chain in ('left', 'right'):
        ecanet('c-select ' + chain)     # select channel chain
        last = get_last_fil_index()
        ecanet(f'cop-select {last}')    # select last fil stage
        ecanet('copp-select 2')         # select global gain
        ecanet(f'copp-set {level}')     # set level


def eca_bypass(mode='get'):
    """ mode: on | off | toggle | get

        returns: the new bypass mode [L, R]
    """

    newmode= [False, False]

    # making changes
    if mode in ('on','off','toggle'):
        for chain in ("left", "right"):
            ecanet("c-select " + chain)
            ecanet("c-bypass " + mode)

    # getting state
    lines = ecanet("c-status").split('\n')
    for line in lines:
        if '[bypassed]' in line:
            if 'Chain "left"' in line:
                newmode[0] = True
            if 'Chain "right"' in line:
                newmode[1] = True

    return newmode


def eca_dump2peq(fpath=PEQDUMPPATH, verbose=False):
    """ Dumps the RUNNING chainsetup to a HUMAN READABLE FILE <fpath>

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
        res +=  '#\n\n'

        res += f'cs-name: {d["cs-name"]}\n'

        channels = ('left', 'right')
        for c in channels:
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
        Parses an Ecasound "chainsetup status" printout string, to
        a dictionary.

        Example from 'fil-plugin' 8-band dual mono Ecasound chainsetup

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

        { 'cs-name': 'fil_8_band_dualMono',

          'left':
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

        # Chainsetup name
        csname = ''
        for line in ecaList:
            if 'Chainsetup' in line and '"' in line:
                csname = line.split('"')[1].strip()
                break
        d['cs-name'] = csname


        # Chains
        for ch in 'left', 'right':

            tmp = [x for x in ecaList if f'Chain "{ch}"'  in x]

            if tmp:
                tmp = tmp[0]

            if tmp:
                tmp = [x for x in tmp.split() if '-eli:1970' in x]

            if tmp:
                tmp = [x.replace('-eli:1970,','') for x in tmp]

            d[ch] = {}
            for i in range(len(tmp)):
                d[ch][f'fil_{i}'] = tmp[i].split(',')

        # Let's parse the detailed global and 4-bands for each fil
        for ch in 'left', 'right':

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


def eca_dump2ecs(fpath=ECSDUMPPATH, verbose=False):
    """ Dumps the RUNNING chainsetup to a file ECASOUND CHAINSTUP FILE <fpath>

        (void)
    """
    # Dumping a chainsetop is a BUILT-IN Ecasound feature
    ecanet( f'cs-save-as {fpath}')

    if verbose:
        with open(fpath, 'r') as f:
            print( f.read() )
        print(f'\n(saved to: {fpath})')


def eca_make_chainsetup(d):
    """ d:       Dictionary with fil plugin parameters

        returns: Text chainsetup to be saved to a file
                 for ecasound cs-load usage
    """

    def make_header():
        res =  '# ecasound chainsetup file'
        res += '\n\n'
        return res


    def make_general():
        if 'cs-name' in d:
            csname = d["cs-name"]
        else:
            csname = 'noname'
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
    cnames = ('left', 'right')
    for cname in cnames:
        res += f'{make_chain(cname)}\n'

    return res


def peq_dump2ecs(d):
    """ Dumps the GIVEN PEQ DICT to a chainsetup file 'd[csname].ecs'

        Returns: the string '<csname>.ecs' for later use.
    """
    chainsetup  = eca_make_chainsetup(d)

    ecspath     = f'{LSPK_FOLDER}/{d["cs-name"]}.ecs'

    with open(ecspath, 'w') as f:
        f.write( chainsetup)

    return ecspath


def peq_read(peqpath):
    """ Reads a PEQ filter set from a given human readable file  xxxx.peq

        returns: a dictionary with parametric filtering setup
    """

    def custom_parse(d):
        """ YAML needs list square brackets in each parametric settings
            line inside the xxxx.peq file.

            If no brackets, peq settings will be loaded as a bare string.

            But we want to avoid writting brackets for clarity, i.e.:

                # Legend:
                #       pN:     OnOff, Freq,  BW,  Gain

                left:
                    fil_0:
                        global: 1,                  0.0
                        p0:     1,     100,   0.1, -6.5


            So lets convert peq parameters string to a list of numeric values.

            We'll also limit decimal places for some fields

            """

        if not 'cs-name' in d:
            d['cs-name'] = os.path.basename(peqpath).replace('.peq', '')

        channels = ('left', 'right')

        for chId in channels:

            for fil in d[chId]:

                for params in d[chId][fil]:
                    p_old = d[chId][fil][params]

                    # string to list
                    if type(p_old) == str:
                        p_old = [float(x) for x in p_old.split(',')]
                        d[chId][fil][params] = p_old

                    # OnOff as integer 1~0
                    OnOff = d[chId][fil][params][0]
                    d[chId][fil][params][0]  = int(OnOff)

                    # Gain one decimal place
                    Gain  = d[chId][fil][params][-1]
                    d[chId][fil][params][-1] = round(Gain, 1)

                    if params != 'global':

                        # Freq as integer
                        Freq = d[chId][fil][params][1]
                        d[chId][fil][params][1]  = int(round(Freq))

                        # BW three decimal places
                        BW = d[chId][fil][params][2]
                        d[chId][fil][params][2]  = round(BW, 3)

        return d


    d = {}

    if not os.path.isfile(peqpath):
        print( f'(peq_mod) Cannot find PEQ file: {peqpath}' )
        return d

    with open(peqpath, 'r') as f:
        c = f.read()

    try:
        d = yaml.safe_load(c)
    except Exception as e:
        print(f'(peq_mod) YAML ERROR reading {os.path.basename(peqpath)}')

    if d:
        d = custom_parse(d)

    return d


def eca_load_peq(peqpath):
    """ Loads a .peq file of parameters in ecasound

        returns: the Ecasound responses after loading, connecting
                 and restarting the engine, and reconnecting jack ports

        returns: 'done' or some error string

        (i) Ecasound will stop engine and will release all I/O
            when loading a chainsetup
    """

    d   = peq_read(peqpath)
    res = ''

    if not d:
        return f'ERROR loading file \'{peqpath}\''

    # Ecasound needs a file to load a chainsetup from,
    # so let's make a temporary one
    tmppath = peq_dump2ecs(d)

    # (i) filename or chain-setup-name spaces needs to be escaped
    #     F-strings cannot have "\"
    tmppath = tmppath.replace(' ', '\\ ')
    res = ecanet(f'cs-load {tmppath}').strip()
    if not '0 -' in res:
        return res

    csname = d["cs-name"].replace(' ', '\\ ')
    res = ecanet(f'cs-select {csname}').strip()
    if not '0 -' in res:
        return res

    res = ecanet('cs-connect').strip()
    if not '0 -' in res:
        return res

    # After connecting, the engine remains stopped
    res = ecanet('start').strip()
    if not '0 -' in res:
        return res

    # When connecting a chainsetup all audio I/O was released
    try:
        import jack_mod as jack
        jack.connect_bypattern('pre_in_loop', 'ecasound')
        jack.connect_bypattern('ecasound', 'brutefir')
    except:
        pass

    # Engine takes a while to be runnig
    sleep(.5)
    res = ecanet('engine-status').strip()

    if 'running' in res:
        return 'done'
    else:
        return 'failed'

