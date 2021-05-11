#!/usr/bin/env python3

# Copyright (c) 2019 Rafael Sánchez
# This file is part of 'pe.audio.sys', a PC based personal audio system.
#
# 'pe.audio.sys' is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# 'pe.audio.sys' is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with 'pe.audio.sys'.  If not, see <https://www.gnu.org/licenses/>.

import  socket              # (i) do not use from socket import socket see below
import  ipaddress
from    json import loads as json_loads
from    time import sleep
import  subprocess as sp
import  yaml
from    numpy import loadtxt as np_loadtxt, zeros as np_zeros
import  configparser
import  os

UHOME       = os.path.expanduser("~")
MAINFOLDER  = f'{UHOME}/pe.audio.sys'


# Config, server addressing and common usage paths and variables
with open(f'{MAINFOLDER}/config.yml', 'r') as f:
    CONFIG = yaml.safe_load(f)
try:
    SRV_HOST, SRV_PORT = CONFIG['peaudiosys_address'], CONFIG['peaudiosys_port']
except:
    print(f'{Fmt.RED}(share.miscel) ERROR reading address/port in '
          f'\'config.yml\'{Fmt.END}')
    exit()

if 'amp_manager' in CONFIG:
    AMP_MANAGER = CONFIG['amp_manager']
else:
    AMP_MANAGER = ''
LOUDSPEAKER     = CONFIG['loudspeaker']
LSPK_FOLDER     = f'{MAINFOLDER}/loudspeakers/{LOUDSPEAKER}'
STATE_PATH      = f'{MAINFOLDER}/.state.yml'
EQ_FOLDER       = f'{MAINFOLDER}/share/eq'
LDMON_PATH      = f'{MAINFOLDER}/.loudness_monitor'
BFCFG_PATH      = f'{LSPK_FOLDER}/brutefir_config'
BFDEF_PATH      = f'{UHOME}/.brutefir_defaults'


# Some nice ANSI formats for printouts
# (PLEASE KEEP THIS CLASS AT THE VERY BEGINNING)
class Fmt:
    """
    # CREDITS: https://github.com/adoxa/ansicon/blob/master/sequences.txt

    0           all attributes off
    1           bold (foreground is intense)
    4           underline (background is intense)
    5           blink (background is intense)
    7           reverse video
    8           concealed (foreground becomes background)
    22          bold off (foreground is not intense)
    24          underline off (background is not intense)
    25          blink off (background is not intense)
    27          normal video
    28          concealed off
    30          foreground black
    31          foreground red
    32          foreground green
    33          foreground yellow
    34          foreground blue
    35          foreground magenta
    36          foreground cyan
    37          foreground white
    38;2;#      foreground based on index (0-255)
    38;5;#;#;#  foreground based on RGB
    39          default foreground (using current intensity)
    40          background black
    41          background red
    42          background green
    43          background yellow
    44          background blue
    45          background magenta
    46          background cyan
    47          background white
    48;2;#      background based on index (0-255)
    48;5;#;#;#  background based on RGB
    49          default background (using current intensity)
    90          foreground bright black
    91          foreground bright red
    92          foreground bright green
    93          foreground bright yellow
    94          foreground bright blue
    95          foreground bright magenta
    96          foreground bright cyan
    97          foreground bright white
    100         background bright black
    101         background bright red
    102         background bright green
    103         background bright yellow
    104         background bright blue
    105         background bright magenta
    106         background bright cyan
    107         background bright white
    """

    BLACK           = '\033[30m'
    RED             = '\033[31m'
    GREEN           = '\033[32m'
    YELLOW          = '\033[33m'
    BLUE            = '\033[34m'
    MAGENTA         = '\033[35m'
    CYAN            = '\033[36m'
    WHITE           = '\033[37m'

    BRIGHTBLACK     = '\033[90m'
    BRIGHTRED       = '\033[91m'
    BRIGHTGREEN     = '\033[92m'
    BRIGHTYELLOW    = '\033[93m'
    BRIGHTBLUE      = '\033[94m'
    BRIGHTMAGENTA   = '\033[95m'
    BRIGHTCYAN      = '\033[96m'
    BRIGHTWHITE     = '\033[97m'

    BOLD            = '\033[1m'
    UNDERLINE       = '\033[4m'
    BLINK           = '\033[5m'
    END             = '\033[0m'


def calc_eq( state ):
    """ Calculate the eq curves to be applied in the Brutefir EQ module,
        as per the provided dictionary of state values.
    """
    zeros = np_zeros( EQ_CURVES["freqs"].shape[0] )

    # getting loudness and tones curves
    loud_mag, loud_pha = get_eq_curve( 'loud', state )
    bass_mag, bass_pha = get_eq_curve( 'bass', state )
    treb_mag, treb_pha = get_eq_curve( 'treb', state )

    # getting target curve
    target_name = state["target"]
    if target_name == 'none':
        targ_mag = zeros
        targ_pha = zeros
    else:
        if target_name != 'target':     # see doc string on find_target_sets()
            target_name += '_target'
        targ_mag = np_loadtxt( f'{EQ_FOLDER}/{target_name}_mag.dat' )
        targ_pha = np_loadtxt( f'{EQ_FOLDER}/{target_name}_pha.dat' )

    # Compose
    eq_mag = targ_mag + loud_mag * state["equal_loudness"] \
                                                + bass_mag + treb_mag

    if CONFIG["bfeq_linear_phase"]:
        eq_pha = zeros
    else:
        eq_pha = targ_pha + loud_pha * state["equal_loudness"] \
                 + bass_pha + treb_pha

    return eq_mag, eq_pha


def calc_gain( state ):
    """ Calculates the gain from:   level,
                                    ref_level_gain
                                    source gain offset
    """

    gain    = state["level"] + float(CONFIG["ref_level_gain"]) \
                             - state["lu_offset"]

    # Adding here the specific source gain:
    if state["input"] != 'none':
        gain += float( CONFIG["sources"][state["input"]]["gain"] )

    return gain


def get_eq_curve(cname, state):
    """ Retrieves the tone or loudness curve.
        Tone curves depens on state bass & treble.
        Loudness compensation curve depens on the configured refSPL.
    """
    # (i) Former FIRtro curves array files xxx.dat were stored in Matlab way,
    #     so when reading them with numpy.loadtxt() it was needed to transpose
    #     and flipud in order to access to the curves data in a natural way.
    #     Currently the curves are stored in pythonic way, so numpy.loadtxt()
    #     will read directly usable data.

    # Tone eq curves are given [-span...0...-span]
    if cname == 'bass':
        bass_center_index = (EQ_CURVES["bass_mag"].shape[0] - 1) // 2
        index = int(round(state["bass"]))   + bass_center_index

    elif cname == 'treb':
        treble_center_index = (EQ_CURVES["treb_mag"].shape[0] - 1) // 2
        index = int(round(state["treble"])) + treble_center_index

    # Using the previously detected flat curve index and
    # also limiting as per the eq_loud_ceil boolean inside config.yml
    elif cname == 'loud':

        index_max   = EQ_CURVES["loud_mag"].shape[0] - 1
        index_flat  = CONFIG['refSPL']
        index_min   = 0
        if CONFIG["eq_loud_ceil"]:
            index_max = index_flat

        if state["equal_loudness"]:
            index = CONFIG['refSPL'] + state["level"]
        else:
            index = index_flat
        index = int(round(index))

        # Clamp index to the available "loudness deepness" curves set
        index = max( min(index, index_max), index_min )

    return EQ_CURVES[f'{cname}_mag'][index], \
           EQ_CURVES[f'{cname}_pha'][index]


# Brutefir client socket function
def bf_cli(cmd):
    """ queries commands to Brutefir
    """
    # using 'with' will disconnect the socket when done
    ans = ''
    with socket.socket() as s:
        try:
            s.connect( ('localhost', 3000) )
            s.send( f'{cmd}; quit;\n'.encode() )
            while True:
                tmp = s.recv(1024).decode()
                if not tmp:
                    break
                ans += tmp
            s.close()
        except:
            print( f'(core) unable to connect to Brutefir:3000' )
    return ans


# Brutefir: get configured outputs
def bf_get_config_outputs():
    """ Read outputs from 'brutefir_config' file, then gets a dictionary.
    """
    outputs = {}

    with open(BFCFG_PATH, 'r') as f:
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


# Brutefir: get current outputs
def bf_get_current_outputs():
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

    # Adding maxdelay info from config_file, because not available on runtime
    outputs['maxdelay'] = bf_get_config_outputs()['maxdelay']

    return outputs


# Brutefir: get loudspeaker filters FS from brutefir config file
def bf_get_sample_rate():
    """ Retrieve loudspeaker's filters FS from its 'brutefir_config' file,
        or from '.brutefir_defaults' file
    """
    FS = 0

    for fname in ( BFCFG_PATH, BFDEF_PATH ):
        with open(fname, 'r') as f:
            lines = f.readlines()
        for l in lines:
            if 'sampling_rate:' in l and l.strip()[0] != '#':
                try:
                    FS = int([x for x in l.replace(';', '').split()
                                         if x.isdigit() ][0])
                except:
                    pass
        if FS:
            break   # stops searching if found under lskp folder

    if not FS:
        raise ValueError('unable to find Brutefir sample_rate')

    if 'brutefir_defaults' in fname:
        print(f'{Fmt.RED}{Fmt.BOLD}'
              f'(miscel) *** USING .brutefir_defaults SAMPLE RATE ***'
              f'{Fmt.END}')

    return FS


# Brutefir: add delay to all outputs
def bf_add_delay(ms):
    """ Will add a delay to all outputs, relative to the  delay values
        as configured under 'brutefir_config'.
    """

    result  = 'nothing done'

    outputs = bf_get_config_outputs()
    FS      = int( bf_get_sample_rate() )

    # From ms to samples
    delay = int( FS  * ms / 1e3)

    cmd = ''
    too_much = False
    max_available    = outputs['maxdelay']
    max_available_ms = max_available / FS * 1e3

    for o in outputs:

        # Skip non output number item (i.e. the  maxdelay item)
        if not o.isdigit():
            continue

        cfg_delay = outputs[o]['delay']
        new_delay = int(cfg_delay + delay)
        if new_delay > outputs['maxdelay']:
            too_much = True
            max_available    = outputs['maxdelay'] - cfg_delay
            max_available_ms = max_available / FS * 1e3
        cmd += f'cod {o} {new_delay};'

    # Issue new delay to Brutefir's outputs
    if not too_much:
        #print(cmd) # debug
        result = bf_cli( cmd ).lower()
        #print(result) # debug
        if not 'unknown command' in result and \
           not 'out of range' in result and \
           not 'invalid' in result and \
           not 'error' in result:
                result = 'done'
        else:
                result = 'Brutefir error'
    else:
        print(f'(i) ERROR Brutefir\'s maxdelay is {int(max_available_ms)} ms')
        result = f'max delay {int(max_available_ms)} ms exceeded'

    return result


# Retrieves EQ curves for tone and loudness countour
def find_eq_curves():
    """ Scans share/eq/ and try to collect the whole set of EQ curves
        needed for the EQ stage in Brutefir
    """
    EQ_CURVES = {}
    eq_files = os.listdir(EQ_FOLDER)

    # file names ( 2x loud + 4x tones + freq = total 7 curves)
    fnames = (  'loudness_mag.dat', 'bass_mag.dat', 'treble_mag.dat',
                'loudness_pha.dat', 'bass_pha.dat', 'treble_pha.dat',
                'freq.dat' )

    # map dict to get the curve name from the file name
    cnames = {  'loudness_mag.dat'  : 'loud_mag',
                'bass_mag.dat'      : 'bass_mag',
                'treble_mag.dat'    : 'treb_mag',
                'loudness_pha.dat'  : 'loud_pha',
                'bass_pha.dat'      : 'bass_pha',
                'treble_pha.dat'    : 'treb_pha',
                'freq.dat'          : 'freqs'     }

    pendings = len(fnames)  # 7 curves
    for fname in fnames:

        # Only one file named as <fname> must be found

        if 'loudness' in fname:
            prefixedfname = f'ref_{CONFIG["refSPL"]}_{fname}'
            files = [ x for x in eq_files if prefixedfname in x]
        else:
            files = [ x for x in eq_files if fname in x]

        if files:

            if len (files) == 1:
                EQ_CURVES[ cnames[fname] ] = \
                         np_loadtxt( f'{EQ_FOLDER}/{files[0]}' )
                pendings -= 1
            else:
                print(f'(core) too much \'...{fname}\' '
                       'files under share/eq/')
        else:
            print(f'(core) ERROR finding a \'...{fname}\' '
                   'file under share/eq/')

    #if not pendings:
    if pendings == 0:
        return EQ_CURVES
    else:
        return {}


# Retrieves the sets of available target curves under the share/eq folder.
def find_target_sets():
    """
        Retrieves the sets of available target curves under the share/eq folder.

                            file name:              returned set name:
        minimal name        'target_mag.dat'        'target'
        a more usual name   'xxxx_target_mag.dat'   'xxxx'

        A 'none' set name is added as default for no target eq to be applied.
    """
    def extract(x):
        """ Aux to extract a meaningful set name, examples:
                'xxxx_target_mag.dat'   will return 'xxxx'
                'target_mag.dat'        will return 'target'
        """

        if x[:6] == 'target':
            return 'target'
        else:
            x = x[:-14]

        # strip trailing unions if used
        for c in ('.', '-', '_'):
            if x[-1] == c:
                x = x[:-1]

        return x

    result = ['none']

    files = os.listdir( EQ_FOLDER )
    tfiles = [ x for x in files if ('target_mag' in x) or ('target_pha' in x) ]

    for fname in tfiles:
        set_name = extract(fname)
        if not set_name in result:
            result.append( set_name )

    return result


# Retreives an optional PEQ (parametic eq) Ecasound filename if configured
def get_peq_in_use():
    """ Finds out the PEQ (parametic eq) filename used by an inserted
        Ecasound sound processor, if included inside config.yml scripts.
    """
    for item in CONFIG["scripts"]:
        if type(item) == dict and 'ecasound_peq.py' in item.keys():
            return item["ecasound_peq.py"].replace('.ecs', '')
    return 'none'


# Sets a peaudiosys parameter as per a given pattern, useful for user macros.
def set_as_pattern(param, pattern, sender='miscel', verbose=False):
    """ Sets a peaudiosys parameter as per a given pattern.
        This applies only for 'xo', 'drc' and 'target'
    """
    result = ''

    if param not in ('xo', 'drc', 'target'):
        return "parameter mus be 'xo', 'drc' or 'target'"

    sets = send_cmd(f'get_{param}_sets')

    try:
        sets = json_loads( sets )
    except:
        return result

    for setName in sets:

        if pattern in setName:
            result = send_cmd( f'set_{param} {setName}',
                               sender=sender, verbose=verbose )
            break

    return result


# Waiting for jack ports with name *pattern* to be available
def wait4ports( pattern, timeout=10 ):
    """ Waits for jack ports with name *pattern* to be available.
        Default timeout 10 s
    """
    n = timeout * 2
    while n:
        tmp = sp.check_output(['jack_lsp', pattern]).decode().split()
        if len( tmp ) >= 2:
            break
        n -= 1
        sleep(0.5)
    if n:
        return True
    else:
        return False


# Send a command to a peaudiosys server
def send_cmd( cmd, sender='', verbose=False, timeout=60,
              host=SRV_HOST, port=SRV_PORT ):
    """ send commands to a pe.audio.sys server
    """
    # (i) socket timeout 60 because Brutefir can need some time
    #     in slow machines after powersave shot it down.

    if not sender:
        sender = 'share.miscel'

    # Default answer: "no answer from ...."
    ans = f'no answer from {host}:{port}'

    # (i) We prefer high-level socket function 'create_connection()',
    #     rather than low level 'settimeout() + connect()'
    try:
        with socket.create_connection( (host, port), timeout=timeout ) as s:
            s.send( cmd.encode() )
            if verbose:
                print( f'{Fmt.BLUE}({sender}) Tx: \'{cmd}\'{Fmt.END}' )
            ans = ''
            while True:
                tmp = s.recv(1024).decode()
                if not tmp:
                    break
                ans += tmp
            if verbose:
                print( f'{Fmt.BLUE}({sender}) Rx: \'{ans}\'{Fmt.END}' )
            s.close()

    except Exception as e:
        ans = e
        if verbose:
            print( f'{Fmt.RED}({sender}) {host}:{port} {e} {Fmt.END}' )

    return ans


# Checks the Mplayer config file
def check_Mplayer_config_file(profile='istreams'):
    """ Checks the Mplayer config file
    """
    cpath = f'{UHOME}/.mplayer/config'

    # This never happens because Mplayer autodumps an empty .mplayer/config file
    if not os.path.exists(cpath):
        return f'ERROR Mplayer config file not found'

    mplayercfg = configparser.ConfigParser()
    try:
        mplayercfg.read( cpath )
    except:
        return f'ERROR bad Mplayer config file'

    if not profile in mplayercfg:
        return f'ERROR Mplayer profile \'{profile}\' not found'
    if 'ao' in mplayercfg[profile] and \
        mplayercfg[profile]['ao'].strip()[:9] == 'jack:name':
        return 'ok'
    else:
        return f'ERROR bad Mplayer profile \'{profile}\''


# Auxiliary to detect the Spotify Client in use: desktop or librespot
def detect_spotify_client(timeout=10):
    """ the timeout will wait some seconds for the client to be running
    """
    result = ''

    # early return if no Spotify script is used:
    if not any( 'spo' in x.lower() for x in CONFIG['scripts'] ):
        return result

    tries = timeout
    while tries:
        try:
            sp.check_output( 'pgrep -f Spotify'.split() )
            result = 'desktop'
        except:
            pass
        try:
            sp.check_output( 'pgrep -f librespot'.split() )
            result = 'librespot'
        except:
            pass
        if result:
            return result
        else:
            tries -= 1
            sleep(1)

    return result


# Kill previous instaces of a process
def kill_bill(pid=0):
    """ Killing previous instances of a process as per its <pid>.
        This is mainly used from start.py.
    """

    if not pid:
        print( f'{Fmt.BOLD}(miscel) ERROR kill_bill() needs <pid> '
               f'(process own pid) as argument{Fmt.END}' )
        return

    # Retrieving the process string that identifies the given pid
    tmp = ''
    try:
        tmp = sp.check_output( f'ps -p {pid} -o command='.split() ).decode()
        # e.g. "python3 pe.audio.sys/start.py all"
    except:
        print( f'{Fmt.BOLD}(miscel) ERROR kill_bill() cannot found pid: {pid} ' )
        return

    # As per this is always used from python3 programs, will remove python3
    # and arguments
    # e.g. "python3 pe.audio.sys/start.py all"  -->  "pe.audio.sys/start.py"
    processString = tmp.replace('python3', '').strip().split()[0]

    # List processes like this one
    rawpids = []
    cmd =   f'ps -eo etimes,pid,cmd' + \
            f' | grep "{processString}"' + \
            f' | grep -v grep'
    try:
        rawpids = sp.check_output(cmd, shell=True).decode().split('\n')
    except sp.CalledProcessError:
        pass
    # Discard blanks and strip spaces:
    rawpids = [ x.strip().replace('\n', '') for x in rawpids if x ]
    # A 'rawpid' element has 3 fields 1st:etimes 2nd:pid 3th:comand_string

    # Removing the own pid
    for rawpid in rawpids:
        if rawpid.split()[1] == str(pid):
            rawpids.remove(rawpid)

    # Just display the processes to be killed, if any.
    print('-' * 21 + f' (miscel) killing \'{processString}\' running before me ' \
           + '-' * 21)
    for rawpid in rawpids:
        print(rawpid)
    print('-' * 80)

    if not rawpids:
        return

    # Extracting just the 'pid' at 2ndfield [1]:
    pids = [ x.split()[1] for x in rawpids ]

    # Killing the remaining pids, if any:
    for pid in pids:
        print(f'(miscel) killing old \'{processString}\' processes:', pid)
        sp.Popen(f'kill -KILL {pid}'.split())
        sleep(.1)
    sleep(.5)


# Gets the selected source from a pe.audio.sys server at <addr>
def get_remote_selected_source(addr, port=9990):
    """ Gets the selected source from a remote pe.audio.sys server at <addr:port>
    """
    source = ''
    ans = send_cmd('state', host=addr, port=port, timeout=1)
    try:
        source = json_loads(ans)["input"]
    except:
        pass
    return source


# Read the last line from a large file, efficiently.
def read_last_line(filename=''):
    # source:
    # https://stackoverflow.com/questions/46258499/read-the-last-line-of-a-file-in-python
    # For large files it would be more efficient to seek to the end of the file,
    # and move backwards to find a newline.
    # Note that the file has to be opened in binary mode, otherwise,
    # it will be impossible to seek from the end.

    if not filename:
        return ''

    try:
        with open(filename, 'rb') as f:
            f.seek(-2, os.SEEK_END)
            while f.read(1) != b'\n':
                f.seek(-2, os.SEEK_CUR)
            last_line = f.readline().decode()
        return last_line.strip()

    except:
        return ''


# Validate if a given string is a valid IP address
def is_IP(s):
    try:
        ipaddress.ip_address(s)
        return True
    except:
        return False


# Aux to get my own IP address
def get_my_ip():
    try:
        tmp = sp.check_output( 'hostname --all-ip-addresses'.split() ).decode()
        return tmp.split()[0]
    except:
        return ''


# Gets data from a remoteXXXXX defined source
def get_remote_source_info():
    ''' Retrieves the remoteXXXXXX source found under the 'sources:' section
        inside config.yml.

        input:  --
        output: srcName, srcIp, srcPort:
    '''
    # Retrieving the remote sender address from 'config.yml'.
    # For a 'remote.....' named source, it is expected to have
    # an IP address kind of in its capture_port field:
    #   capture_port:  X.X.X.X
    # so this way we can query the remote sender to run 'zita-j2n'

    remote_addr = ''
    remote_port = 9990

    for source in CONFIG["sources"]:
        if 'remote' in source:
            tmp = CONFIG["sources"][source]["capture_port"]
            tmp_addr = tmp.split(':')[0]
            tmp_port = tmp.split(':')[-1]
            if is_IP(tmp_addr):
                remote_addr = tmp_addr
                if tmp_port.isdigit():
                    remote_port = int(tmp_port)
                break

    if not remote_addr:
        print(f'(zita-n2j) Cannot get remote address from configured sources')
        sys.exit()
    if not is_IP(remote_addr):
        print(f'(zita-n2j) source: \'{source}\' address: \'{remote_addr}\' not valid')
        sys.exit()

    return source, remote_addr, remote_port


# EQ curves for tone and loudness contour are mandatory
# (i) kept last because it depends on the find_eq_curves() funtcion
EQ_CURVES   = find_eq_curves()
if not EQ_CURVES:
    print( '(core) ERROR loading EQ_CURVES from share/eq/' )
    sys.exit()
