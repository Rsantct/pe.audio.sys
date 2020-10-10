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

""" MAIN SERVICE MODULE that controls the whole system:
        preamp, players and auxiliary functions.
    This module is loaded by 'server.py'
"""

import os
import sys
UHOME = os.path.expanduser("~")
sys.path.append(f'{UHOME}/pe.audio.sys')

from share.miscel import *
import preamp
import players

import yaml
import json
from subprocess import Popen
from time import sleep, strftime
#   https://watchdog.readthedocs.io/en/latest/
from watchdog.observers import Observer
from watchdog.events    import FileSystemEventHandler

ME                  = __file__.split('/')[-1]
MACROS_FOLDER       = f'{MAINFOLDER}/macros'
LOUD_MON_CTRL_FILE  = f'{MAINFOLDER}/.loudness_control'
LOUD_MON_VAL_FILE   = f'{MAINFOLDER}/.loudness_monitor'
AMP_STATE_FILE      = f'{UHOME}/.amplifier'
STATE_FILE          = f'{MAINFOLDER}/.state.yml'

AUX_INFO = {    'amp':              'off',
                'loudness_monitor': 0.0,
                'user_macros':      [],
                'last_macro':       '-',    # cannot be empty
                'web_config':       {}
            }


# COMMAND LOG FILE
logFname = f'{UHOME}/pe.audio.sys/.peaudiosys_cmd.log'
if os.path.exists(logFname) and os.path.getsize(logFname) > 2e6:
    print ( f"{Fmt.RED}(peaudiosys) log file exceeds ~ 2 MB '{logFname}'{Fmt.END}" )
print ( f"{Fmt.BLUE}(peaudiosys) logging commands in '{logFname}'{Fmt.END}" )


# Read the amplifier state file, if it exists:
def get_amp_state():
    curr_sta = 'off'
    try:
        with open( f'{AMP_STATE_FILE}', 'r') as f:
            curr_sta =  f.read().strip()
    except:
        pass
    if not curr_sta or curr_sta.lower() in ('0', 'off'):
        curr_sta = 'off'
    elif curr_sta.lower() in ('1', 'on'):
        curr_sta = 'on'
    return curr_sta


# Set the amplifier switch:
def set_amp_state(mode):
    if not AMP_MANAGER:
        return
    print( f'({ME}) running \'{AMP_MANAGER.split("/")[-1]} {mode}\'' )
    Popen( f'{AMP_MANAGER} {mode}'.split(), shell=False )


def amp_player_manager(mode):
    """ An auxiliary function for controlling playback
        from the amplifier switch.
    """

    if mode == 'off':

        # Do stop playback when switching off the amplifier
        players.do('stop')

        # Special case: librespot doesn't have playback control feature
        if 'librespot.py' in CONFIG['scripts']:
            print(f'{Fmt.BLUE}({ME}) AMP OFF: shutting down librespot process{Fmt.END}')
            Popen( f'{MAINFOLDER}/share/scripts/librespot.py stop', shell=True)
            sleep(.5)

    elif mode == 'on':
        # Do not resume playback when switching on the amplifier

        # Special case: librespot doesn't have playback control feature
        if 'librespot.py' in CONFIG['scripts']:
            print(f'{Fmt.BLUE}({ME}) AMP ON: restarting librespot process{Fmt.END}')
            Popen( f'{MAINFOLDER}/share/scripts/librespot.py start', shell=True)
            sleep(.5)


# LIST OF MACROS under macros/ folder (numeric sorted)
def get_macros(only_web_macros=True):

    macro_files = []

    with os.scandir( f'{MACROS_FOLDER}' ) as entries:

        for entrie in entries:
            fname = entrie.name

            # Only executables files
            if os.path.isfile(f'{MACROS_FOLDER}/{fname}') and \
               os.access(f'{MACROS_FOLDER}/{fname}', os.X_OK):

                # Web macros are the ones named NN_xxxxxx
                if only_web_macros:
                    if fname.split('_')[0].isdigit():
                        macro_files.append(fname)
                else:
                    macro_files.append(fname)

    # (i) The web page needs a sorted list
    if only_web_macros:
        return sorted(macro_files, key=lambda x: int(x.split('_')[0]))
    else:
        return sorted(macro_files)


# Main function for PREAMP/CONVOLVER commands processing
def process_preamp( cmd, arg='' ):
    if arg:
        cmd  = ' '.join( (cmd, arg) )
    return preamp.do(cmd)


# Main function for PLAYERS commands processing
def process_players( cmd, arg='' ):
    if arg:
        cmd  = ' '.join( (cmd, arg) )
    return players.do(cmd)


# Main function for AUX commands processing
def process_aux( cmd, arg='' ):
    """ input:  a tuple (prefix, command, arg)
        output: a result string
    """

    # Aux to provide the static web configuration options:
    def get_web_config():

        wconfig = CONFIG['web_config']

        # Complete some additional info
        wconfig['restart_cmd_info']   = CONFIG['restart_cmd']
        wconfig['LU_monitor_enabled'] = True if 'loudness_monitor.py' \
                                                  in CONFIG['scripts'] else False

        # main selector manages inputs or macros
        if not 'main_selector' in wconfig:
            wconfig["main_selector"] = 'inputs';
        else:
            if wconfig["main_selector"] not in ('inputs', 'macros'):
                wconfig["main_selector"] = 'inputs'

        return wconfig


    # Aux for playing an url stream
    def play_istream(url):

        error = False

        # Tune the radio station (Mplayer jack ports will dissapear for a while)
        Popen( f'{UHOME}/pe.audio.sys/share/scripts/istreams.py url {url}'
                .split() )
        # Waits a bit to Mplayer ports to dissapear from jack while loading a new stream.
        sleep(2)
        # Waiting for mplayer ports to re-emerge
        if not wait4ports( f'mplayer_istreams' ):
            print(f'(peaudiosys.py) ERROR jack ports \'mplayer_istreams\''
                   ' not found' )
            error = True
        if not error:
            # Switching the preamp input
            preamp.do('input istreams')
            return True
        else:
            return False


    # BEGIN of process_aux
    result = 'bad command'

    # AMPLIFIER SWITCHING
    if cmd == 'amp_switch':

        # current switch state
        if arg == 'state':
            return get_amp_state()

        if arg == 'toggle':
            # if unknown state, this switch defaults to 'on'
            result = {'on': 'off', 'off': 'on'}.get( get_amp_state(), 'on' )

        elif arg in ('on', 'off'):
            result = arg

        set_amp_state( result )

        # optionally will stop the current player
        if 'amp_off_stops_player' in CONFIG and \
           CONFIG['amp_off_stops_player'] == True:
            amp_player_manager(mode=result)

        return result

    # LIST OF MACROS
    elif cmd == 'get_macros':
        if arg == 'web':
            only_web = True
        else:
            only_web = False
        result = get_macros(only_web)

    # LAST EXECUTED MACRO
    elif cmd == 'get_last_macro':
        result = AUX_INFO['last_macro']

    # RUN MACRO
    elif cmd == 'run_macro':
        if arg in get_macros(only_web_macros=False):
            print( f'({ME}) running macro: {arg}' )
            Popen( f'"{MACROS_FOLDER}/{arg}"', shell=True)
            AUX_INFO["last_macro"] = arg
            # This updates disk file .aux_info for others to have fresh 'last_macro'
            dump_aux_info()
            result = 'tried'
        else:
            result = 'macro not found'

    # PLAYS SOMETHING
    elif cmd == 'play':

        # An URL: will be played back by the istreams Mplayer service:
        if arg.startswith('http://') or arg.startswith('https://'):
            if play_istream(arg):
                result = 'done'
            else:
                result = 'failed'
        else:
            result = f'bad: {arg}'

    # RESET the LOUDNESS MONITOR DAEMON:
    elif cmd == 'loudness_monitor_reset' or cmd.lower() == 'lu_monitor_reset':
        try:
            with open(LOUD_MON_CTRL_FILE, 'w') as f:
                f.write('reset')
            result = 'done'
        except:
            result = 'error'

    # Set the LOUDNESS MONITOR SCOPE:
    elif cmd == 'set_loudness_monitor_scope' or \
         cmd.lower() == 'set_lu_monitor_scope':
        try:
            with open(LOUD_MON_CTRL_FILE, 'w') as f:
                f.write(f'scope={arg}')
            result = 'done'
        except:
            result = 'error'

    # Get the LOUDNESS MONITOR VALUE from the
    # loudness monitor daemon's output file:
    elif cmd == 'get_loudness_monitor' or cmd.lower() == 'get_lu_monitor':
        try:
            with open(LOUD_MON_VAL_FILE, 'r') as f:
                result = json.loads( f.read() )
        except:
            if 'LU_reset_scope' in CONFIG:
                result = {'LU_I': 0.0, 'LU_M':0.0,
                          'scope': CONFIG["LU_reset_scope"]}
            else:
                result = {'LU_I': 0.0, 'LU_M':0.0, 'scope': 'album'}

    # RESTART
    elif cmd == 'restart':
        try:
            restart_cmd = CONFIG["restart_cmd"]
        except:
            restart_cmd = f'{UHOME}/start.py all'

        try:
            Popen( f'{restart_cmd}'.split() )
        except:
            print( f'({ME}) Problems running \'{restart_cmd}\'' )

    # Get the WEB.CONFIG dictionary
    elif cmd == 'get_web_config':
        result = get_web_config()

    # Add outputs delay, can be useful for multiroom listening
    elif cmd == 'add_delay':
        print(f'({ME}) ordering adding {arg} ms of delay.')
        Popen(f'{UHOME}/bin/peaudiosys_add_delay.py {arg}'.split())
        result = 'tried'

    # HELP
    elif '-h' in cmd:
        print(__doc__)
        result =  'done'

    return result


# Dumps pe.audio.sys/.aux_info
def dump_aux_info():
    AUX_INFO['amp'] =               process_aux('amp_switch', 'state')
    AUX_INFO['loudness_monitor'] =  process_aux('get_loudness_monitor')
    AUX_INFO['user_macros'] =       process_aux('get_macros', 'web')
    AUX_INFO['web_config'] =        process_aux('get_web_config')
    with open(f'{MAINFOLDER}/.aux_info', 'w') as f:
        f.write( json.dumps(AUX_INFO) )


# Handler class to do actions when a file change occurs.
class files_event_handler(FileSystemEventHandler):
    """ will do something when <wanted_path> file changes
    """
    # (i) This is an inherited class from the imported one 'FileSystemEventHandler',
    #     which provides the 'event' propiertie.
    #     Here we expand the class with our custom parameter 'wanted_path'.

    def __init__(self, wanted_path=''):
        self.wanted_path = wanted_path

    def on_modified(self, event):
        # DEBUG
        #print( f'({ME}) event type: {event.event_type}, file: {event.src_path}' )
        if event.src_path == self.wanted_path:
            dump_aux_info()


# auto-started when loading this module
def init():

    # First update
    dump_aux_info()

    # Starts a WATCHDOG to observe file changes
    #   https://watchdog.readthedocs.io/en/latest/
    #   https://stackoverflow.com/questions/18599339/
    #   python-watchdog-monitoring-file-for-changes
    #   Use recursive=True to observe also subfolders
    #   Even observing recursively the CPU load is negligible,
    #   but we prefer to observe to a single folder.

    # Will observe for changes in AMP_STATE_FILE under HOME folder:
    observer1 = Observer()
    observer1.schedule( files_event_handler(AMP_STATE_FILE),
                        path=UHOME,
                        recursive=False )
    observer1.start()

    # Will observe for changes in LOUD_MON_VAL_FILE under MAINFOLDER folder:
    observer2 = Observer()
    observer1.schedule( files_event_handler(LOUD_MON_VAL_FILE),
                        path=MAINFOLDER,
                        recursive=False )
    observer2.start()


# Interface function to plug this on server.py
def do( cmd_phrase ):

    def read_cmd_phrase(cmd_phrase):

        # (i) command phrase SYNTAX must start with an appropriate prefix:
        #           preamp  command  arg1 ...
        #           players command  arg1 ...
        #           aux     command  arg1 ...
        #     The 'preamp' prefix can be omited

        pfx, cmd, arg = '', '', ''

        # This is to avoid empty values when there are more
        # than on space as delimiter inside the cmd_phrase:
        chunks = [x for x in cmd_phrase.split(' ') if x]

        # If not prefix, will treat as a preamp command kind of
        if not chunks[0] in ('preamp', 'player', 'aux'):
            chunks.insert(0, 'preamp')
        pfx = chunks[0]

        if chunks[1:]:
            cmd = chunks[1]
        else:
            raise Exception(f'({ME}) BAD command: {cmd_phrase}')
        if chunks[2:]:
            # allows spaces inside the arg part, e.g. 'run_macro 2_Radio Clasica'
            arg = ' '.join( chunks[2:] )

        return pfx, cmd, arg

    result = 'nothing done'
    cmd_phrase = cmd_phrase.strip()

    if cmd_phrase.strip():

        # cmd_phrase log
        if 'state' not in cmd_phrase and 'get_' not in cmd_phrase:
            with open(logFname, 'a') as FLOG:
                FLOG.write(f'{strftime("%Y/%m/%d %H:%M:%S")}; {cmd_phrase}; ')

        pfx, cmd, arg = read_cmd_phrase( cmd_phrase )
        #print('pfx:', pfx, '| cmd:', cmd, '| arg:', arg) # DEBUG
        if cmd == 'help':
            Popen( f'cat {MAINFOLDER}/doc/peaudiosys.hlp', shell=True)
            return 'help has been printed to stdout, also available on ' \
                    '\'~/pe.audio.sys/doc/peaudiosys.hlp\''
        result = {  'preamp':   process_preamp,
                    'player':   process_players,
                    'aux':      process_aux }[ pfx ]( cmd, arg )
        if type(result) != str:
            result = json.dumps(result)

        # result log
        if 'state' not in cmd_phrase and 'get_' not in cmd_phrase:
            with open(logFname, 'a') as FLOG:
                FLOG.write(f'{result}\n')

    return result


# Will AUTO-START init() when loading this module
init()
