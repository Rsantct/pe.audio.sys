#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pe.audio.sys'
# 'pe.audio.sys', a PC based personal audio system.

""" This module provides common usage functions
"""

import  socket
import  ipaddress
from    json import loads as json_loads, dumps as json_dumps
from    time import sleep
import  subprocess as sp
import  configparser
import  os
import  threading

from    config      import *
from    fmt         import Fmt

# --- pe.audio.sys common usage functions:

def dump_aux_info(AUX_INFO):
    """ A helper to write AUX_INFO dict to a file to be accesible
        by third party processes
    """
    # Dynamic updates
    AUX_INFO['amp'] =               manage_amp_switch( 'state' )
    AUX_INFO['loudness_monitor'] =  get_loudness_monitor()
    # Dumping to disk
    with open(AUX_INFO_PATH, 'w') as f:
        f.write( json_dumps(AUX_INFO) )


def process_is_running(pattern):
    """ check for a system process to be running by a given pattern
        (bool)
    """
    try:
        # do NOT use shell=True because pgrep ...  will appear it self.
        plist = sp.check_output(['pgrep', '-fla', pattern]).decode().split('\n')
    except:
        return False
    for p in plist:
        if pattern in p:
            return True
    return False


def server_is_running(who_asks='miscel'):
    """ (bool)
    """
    print(f'{Fmt.BLUE}({who_asks}) waiting for the server to be alive ...{Fmt.END}')
    tries = 60  # up to 30 seconds
    while tries:
        if 'loudspeaker' in send_cmd('state'):
            break
        sleep(.5)
        tries -= 1
    if tries:
        print(f'{Fmt.BLUE}({who_asks}) server.py is RUNNIG{Fmt.END}')
        return True
    else:
        print(f'{Fmt.BOLD}({who_asks}) server.py NOT RUNNIG{Fmt.END}')
        return False


def manage_amp_switch(mode):

    def get_amp_state():
        result = 'n/a'
        try:
            with open( f'{AMP_STATE_PATH}', 'r') as f:
                tmp =  f.read().strip()
            if tmp.lower() in ('0', 'off'):
                result = 'off'
            elif tmp.lower() in ('1', 'on'):
                result = 'on'
        except:
            pass
        return result


    def set_amp_state(mode):
        if 'amp_manager' in CONFIG:
            AMP_MANAGER     = CONFIG['amp_manager']
        else:
            return '(aux) amp_manager not configured'
        print( f'(aux) running \'{AMP_MANAGER.split("/")[-1]} {mode}\'' )
        sp.Popen( f'{AMP_MANAGER} {mode}', shell=True )
        sleep(1)
        return get_amp_state()


    def wait4_convolver_on():
        cmax = 30
        while True:
            conv_on = read_state_from_disk()["convolver_runs"]
            if conv_on == True:
                sleep(3)
                send_cmd('aux warning clear', timeout=1)
                break
            cmax -= 1
            if not cmax:
                send_cmd('aux warning clear', timeout=1)
                break
            sleep(1)


    cur_state = get_amp_state()
    new_state  = '';

    if mode == 'state':
        result = cur_state

    elif mode == 'toggle':
        # if unknown state, this switch defaults to 'on'
        new_state = {'on': 'off', 'off': 'on'}.get( cur_state, 'on' )

    elif mode in ('on', 'off'):
        new_state = mode

    else:
        result = '(aux) bad amp_switch option'

    if new_state:
        result = set_amp_state( new_state )

    # Wake up the convolver if sleeping:
    if new_state == 'on':
        send_cmd('aux warning set ( waking up ... )', timeout=1)
        sleep(1)
        send_cmd('preamp convolver on', timeout=1)
        job = threading.Thread(target=wait4_convolver_on)
        job.start()

    # Optionally will stop the current player as per CONFIG
    if new_state == 'off':
        if 'amp_off_stops_player' in CONFIG and CONFIG['amp_off_stops_player']:
            curr_input = read_state_from_disk()['input']
            if not curr_input.startswith('remote'):
                send_cmd('player pause', timeout=1)

    return result


def get_loudness_monitor():

        result = read_json_from_file(LDMON_PATH)

        if not result:
            if 'LU_reset_scope' in CONFIG:
                result = {'LU_I': 0.0, 'LU_M':0.0,
                          'scope': CONFIG["LU_reset_scope"]}
            else:
                result = {'LU_I': 0.0, 'LU_M':0.0,
                          'scope': 'album'}

        return result


def read_bf_config_fs():
    """ Reads the sampling rate configured in Brutefir
            - from         brutefir_config    (the loudspeaker config file),
            - or from   ~/.brutefir_defaults  (the default config file).
        (int)
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


def get_peq_in_use():
    """ Finds out the PEQ (parametic eq) filename used by an inserted
        Ecasound sound processor, if included inside config.yml scripts.
        (filepath: string)
    """
    for item in CONFIG["scripts"]:
        if type(item) == dict and 'ecasound_peq.py' in item.keys():
            return item["ecasound_peq.py"].replace('.ecs', '')
    return 'none'


def get_remote_selected_source(addr, port=9990):
    """ Gets the selected source from a remote pe.audio.sys server at <addr:port>
        (string)
    """
    remote_source = ''
    remote_state = send_cmd('state', host=addr, port=port, timeout=1)
    try:
        remote_source = json_loads(remote_state)["input"]
    except:
        pass
    return remote_source


def get_remote_sources_info():
    ''' Retrieves the remoteXXXXXX sources found under the 'sources:' section
        inside config.yml.

        (list of tuples <srcName,srcIp,srcPort>)
    '''
    # Retrieving the remote sender address from 'config.yml'.
    # For a 'remote.....' named source, it is expected to have
    # an IP address kind of in its jack_pname field:
    #   jack_pname:  X.X.X.X
    # so this way we can query the remote sender to run 'zita-j2n'

    remotes = []
    for source in CONFIG["sources"]:
        if 'remote' in source:
            addr = ''
            port = 9990
            tmp = CONFIG["sources"][source]["jack_pname"]
            tmp_addr = tmp.split(':')[0]
            tmp_port = tmp.split(':')[-1]
            if is_IP(tmp_addr):
                addr = tmp_addr
            else:
                print(f'(miscel) source: \'{source}\' address: \'{tmp_addr}\' not valid')
                continue
                if tmp_port.isdigit():
                    port = int(tmp_port)
            remotes.append( (source, addr, port ) )

    if not remotes:
        print(f'(miscel) Cannot get remote sources')

    return remotes


def wait4ports( pattern, timeout=10 ):
    """ Waits for jack ports with name *pattern* to be available.
        Default timeout 10 s
        (bool)
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


def send_cmd( cmd, sender='', verbose=False, timeout=60,
              host=CONFIG['peaudiosys_address'], port=CONFIG['peaudiosys_port'] ):
    """ send commands to a pe.audio.sys server
        (answer: string)
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
        ans = str(e)
        if verbose:
            print( f'{Fmt.RED}({sender}) {host}:{port} \'{ans}\' {Fmt.END}' )

    return ans


def check_Mplayer_config_file(profile='istreams'):
    """ Checks the Mplayer config file
        (result: string)
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


def detect_spotify_client(timeout=10):
    """ Detects the Spotify Client in use: desktop or librespot
        (string)
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


def read_state_from_disk():
    """ wrapper for reading the state dict
        (dictionary)
    """
    return read_json_from_file(STATE_PATH)


def read_metadata_from_disk():
    """ wrapper for reading the playing metadata dict
        (dictionary)
    """
    return read_json_from_file(PLAYER_META_PATH)


def read_cdda_info_from_disk():
    """ wrapper for reading the cdda info dict
        (dictionary)
    """
    return read_json_from_file(CDDA_INFO_PATH)


def read_json_from_file(fname, tries=5):
    """ read json dicts from disk files
        (dictionary)
    """
    d = {}
    if fname == STATE_PATH:
        d = {'input':'none', 'level':'0.0'}

    # It is possible to fail while the file is updating :-/
    while tries:
        try:
            with open( fname, 'r') as f:
                d = json_loads( f.read() )
            break
        except:
            tries -= 1
        sleep(.25)
    return d


# --- generic purpose functions:

def kill_bill(pid=0):
    """ Killing previous instances of a process as per its <pid>.
        (void)
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


def read_last_line(filename=''):
    """ Read the last line from a large file, efficiently.
        (string)
    """
    # credits:
    # https://stackoverflow.com/questions/46258499/read-the-last-line-of-a-file-in-python
    # For large files it would be more efficient to seek to the end of the file,
    # and move backwards to find a newline.
    # Note that the file has to be opened in binary mode, otherwise,
    # it will be impossible to seek from the end.
    #
    # https://python-reference.readthedocs.io/en/latest/docs/file/seek.html
    # f.seek( offset, whence )

    if not filename:
        return ''

    try:
        with open(filename, 'rb') as f:
            f.seek(-2, os.SEEK_END)             # Go to -2 bytes from file end

            while f.read(1) != b'\n':           # Repeat reading until find \n
                f.seek(-2, os.SEEK_CUR)

            last_line = f.readline().decode()   # readline reads until \n

        return last_line.strip()

    except:
        return ''


def read_last_lines(filename='', nlines=1):
    """ Read the last N lines from a large file, efficiently.
        (list of strings)
    """
    # credits:
    # https://stackoverflow.com/questions/46258499/read-the-last-line-of-a-file-in-python
    # For large files it would be more efficient to seek to the end of the file,
    # and move backwards to find a newline.
    # Note that the file has to be opened in binary mode, otherwise,
    # it will be impossible to seek from the end.
    #
    # https://python-reference.readthedocs.io/en/latest/docs/file/seek.html
    # f.seek( offset, whence )

    if not filename:
        return ['']

    try:
        with open(filename, 'rb') as f:
            f.seek(-2, os.SEEK_END)

            c = nlines
            while c:
                if f.read(1) == b'\n':
                    c -= 1
                f.seek(-2, os.SEEK_CUR)

            lines = f.read().decode()[2:].replace('\r', '').split('\n')

        return [x.strip() for x in lines if x]

    except:
        return ['']


def force_to_flush_file(fname='', content=''):
    """ A tool to flush some special temporary files
        (!) BE CAREFUL WITH THIS
        (result: string)
    """
    bare_fname = fname.replace(f'{MAINFOLDER}/', '')

    if 'pe.audio.sys' not in fname:
        return f'NOT allowed flushing outside pe.audio.sys'

    if bare_fname.replace(MAINFOLDER, '').count('/') >= 1:
        return f'NOT allowed flushing deeper than \'{MAINFOLDER}\''

    if not bare_fname.startswith('.'):
        return f'ONLY allowed flushing dot-hidden files'

    # It is possible to fail while the file is updating :-/
    times = 5
    while times:
        try:
            with open( fname, 'w') as f:
                f.write(content)
            return 'done'
        except:
            times -= 1
        sleep(.2)
    return 'ERROR flushing \'fname\''


def is_IP(s):
    """ Validate if a given string is a valid IP address
        (bool)
    """
    if type(s) == str:
        try:
            ipaddress.ip_address(s)
            return True
        except:
            return False
    else:
        return False


def get_my_ip():
    """ retrieves the own IP address
        (string)
    """
    try:
        tmp = sp.check_output( 'hostname --all-ip-addresses'.split() ).decode()
        return tmp.split()[0]
    except:
        return ''


def sec2min(s):
    """ Format a given float (seconds) to "XXmYYs"
        (string)
    """
    m = s // 60
    s = s % 60
    return f'{str(m).rjust(2,"0")}m{str(s).rjust(2,"0")}s'


def timesec2string(x):
    """ Format a given float (seconds) to "hh:mm:ss"
        (string)
    """
    # x must be float
    h = int( x / 3600 )         # hours
    x = int( round(x % 3600) )  # updating x to reamining seconds
    m = int( x / 60 )           # minutes from the new x
    s = int( round(x % 60) )    # and seconds
    return f'{h:0>2}:{m:0>2}:{s:0>2}'


