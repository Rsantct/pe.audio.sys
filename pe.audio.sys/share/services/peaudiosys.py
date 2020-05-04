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

from socket import socket
import yaml
import json
from subprocess import Popen
import os
#   https://watchdog.readthedocs.io/en/latest/
from watchdog.observers import Observer
from watchdog.events    import FileSystemEventHandler

ME                  = __file__.split('/')[-1]
UHOME               = os.path.expanduser("~")
MAIN_FOLDER         = f'{UHOME}/pe.audio.sys'
MACROS_FOLDER       = f'{MAIN_FOLDER}/macros'
LOUD_MON_CTRL_FILE  = f'{MAIN_FOLDER}/.loudness_control'
LOUD_MON_VAL_FILE   = f'{MAIN_FOLDER}/.loudness_monitor'
AMP_STATE_FILE      = f'{UHOME}/.amplifier'
STATE_FILE          = f'{MAIN_FOLDER}/.state.yml'

aux_info = {    'amp':              'off',
                'loudness_monitor': 0.0,
                'user_macros':      [],
                'web_config':       {}
            }

## Reading config.yml
try:
    with open(f'{MAIN_FOLDER}/config.yml', 'r') as f:
        CONFIG = yaml.safe_load(f)
    BASE_PORT = CONFIG['peaudiosys_port']
except:
    print(f'({ME}) ERROR with \'pe.audio.sys/config.yml\'')
    exit()
try:
    AMP_MANAGER =  CONFIG['amp_manager']
except:
    AMP_MANAGER =  'For amp switching please configure config.yml'
WEBCONFIG = CONFIG['web_config']
WEBCONFIG['restart_cmd_info']   = CONFIG['restart_cmd']
WEBCONFIG['LU_monitor_enabled'] = True if 'loudness_monitor.py' \
                                          in CONFIG['scripts'] else False


# Auxiliary client to talk to othes server.py instances (preamp and players)
def cli_cmd(service, cmd):

    # (i) start.py will assign 'preamp' port number this way:
    if service == 'preamp':
        port = BASE_PORT + 1
    elif service == 'players':
        port = BASE_PORT + 2
    else:
        raise Exception(f'({ME}) wrong service \'{service}\'')

    ans = None
    with socket() as s:
        try:
            s.connect( ('localhost', port) )
            s.send( cmd.encode() )
            print( f'({ME}) Tx to {service}:   \'{cmd }\'' )
            ans = ''
            while True:
                tmp = s.recv(1024).decode()
                if not tmp:
                    break
                ans += tmp
            print( f'({ME}) Rx from {service}: \'{ans }\' ' )
            s.close()
        except:
            print( f'({ME}) service \'peaudiosys\' socket error on port {port}' )
    return ans


# Main function for PREDIC commands processing
def process_preamp( cmd, arg='' ):
    if arg:
        cmd  = ' '.join( (cmd, arg) )
    return cli_cmd( service='preamp', cmd=cmd )


# Main function for PLAYERS commands processing
def process_players( cmd, arg='' ):
    if arg:
        cmd  = ' '.join( (cmd, arg) )
    return cli_cmd( service='players', cmd=cmd )


# Main function for AUX commands processing
def process_aux( cmd, arg='' ):
    """ input:  a tuple (prefix, command, arg)
        output: a result string
    """
    result = ''

    # AMPLIFIER SWITCHING
    if cmd == 'amp_switch':

        # current switch state
        try:
            with open( f'{AMP_STATE_FILE}', 'r') as f:
                tmp =  f.read().strip()
            if tmp.lower() in ('0', 'off'):
                curr_sta = 'off'
            elif tmp.lower() in ('1', 'on'):
                curr_sta = 'on'
            else:
                curr_sta = '-'
                raise
        except:
            print( f'({ME}) UNKNOWN status in \'{AMP_STATE_FILE}\'' )

        if arg == 'state':
            return curr_sta

        if arg == 'toggle':
            # if unknown state, this switch defaults to 'on'
            new_sta = {'on': 'off', 'off': 'on'}.get(curr_sta, 'on')

        if arg in ('on', 'off'):
            new_sta = arg

        print( f'({ME}) running \'{AMP_MANAGER.split("/")[-1]} {new_sta}\'' )
        Popen( f'{AMP_MANAGER} {new_sta}'.split(), shell=False )
        return new_sta

    # LIST OF MACROS under macros/ folder
    elif cmd == 'get_macros':
        macro_files = []
        with os.scandir( f'{MACROS_FOLDER}' ) as entries:
            for entrie in entries:
                fname = entrie.name
                if fname.split('_')[0].isdigit():
                    macro_files.append(fname)
        # (i) The web page needs a sorted list
        result = sorted(macro_files, key=lambda x: int(x.split('_')[0]))

    # RUN MACRO
    elif cmd == 'run_macro':
        print( f'({ME}) running macro: {arg}' )
        Popen( f'"{MACROS_FOLDER}/{arg}"', shell=True)
        result = 'tried'

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
            result = {"LU_I": 0, "scope": CONFIG["LU_reset_md_field"]}

    # RESTART
    elif cmd == 'restart':
        try:
            restart_action = CONFIG["restart_cmd"]
        except:
            restart_action = 'peaudiosys_restart.sh'

        try:
            Popen( f'{restart_action}'.split() )
        except:
            print( f'({ME}) Problems running \'{restart_action}\'' )

    # Get the WEB.CONFIG dictionary
    elif cmd == 'get_web_config':
        result = WEBCONFIG

    # HELP
    elif '-h' in cmd:
        print(__doc__)
        result =  'done'

    return result


# Dumps pe.audio.sys/.aux_info
def dump_aux_info():
    aux_info['amp'] =               process_aux('amp_switch', 'state')
    aux_info['loudness_monitor'] =  process_aux('get_loudness_monitor')
    aux_info['user_macros'] =       process_aux('get_macros')
    aux_info['web_config'] =        process_aux('get_web_config')
    with open(f'{MAIN_FOLDER}/.aux_info', 'w') as f:
        f.write( json.dumps(aux_info) )


# Handler class to do actions when a file change occurs
class My_files_event_handler(FileSystemEventHandler):
    """ will do something when some file changes
    """
    def on_modified(self, event):
        path = event.src_path
        #print( f'({ME}) file {event.event_type}: \'{path}\'' ) # DEBUG
        if path in (AMP_STATE_FILE, LOUD_MON_VAL_FILE):
            dump_aux_info()


# init() will be autostarted from server.py when loading this module
def init():

    # First update
    dump_aux_info()

    # Starts a WATCHDOG to observe file changes
    #   https://watchdog.readthedocs.io/en/latest/
    #   https://stackoverflow.com/questions/18599339/
    #   python-watchdog-monitoring-file-for-changes
    #   Use recursive=True to observe also subfolders
    #  (i) Even observing recursively the CPU load is negligible

    # Will observe for changes in files under $HOME.
    observer = Observer()
    observer.schedule(event_handler=My_files_event_handler(),
                      path=UHOME,
                      recursive=True)
    observer.start()


# Interface function to plug this on server.py
def do( command_phrase ):

    def read_command_phrase(command_phrase):

        # (i) command phrase SYNTAX must start with an appropriate prefix:
        #           preamp  command  arg1 ...
        #           players command  arg1 ...
        #           aux     command  arg1 ...
        #     The 'preamp' prefix can be omited

        pfx, cmd, arg = '', '', ''

        # This is to avoid empty values when there are more
        # than on space as delimiter inside the command_phrase:
        chunks = [x for x in command_phrase.split(' ') if x]

        # If not prefix, will treat as a preamp command kind of
        if not chunks[0] in ('preamp', 'player', 'aux'):
            chunks.insert(0, 'preamp')
        pfx = chunks[0]

        if chunks[1:]:
            cmd = chunks[1]
        else:
            raise Exception(f'({ME}) BAD command: {command_phrase}')
        if chunks[2:]:
            # allows spaces inside the arg part, e.g. 'run_macro 2_Radio Clasica'
            arg = ' '.join( chunks[2:] )

        return pfx, cmd, arg

    if command_phrase.strip():
        pfx, cmd, arg = read_command_phrase( command_phrase.strip() )
        #print('pfx:', pfx, '| cmd:', cmd, '| arg:', arg) # DEBUG
        if cmd == 'help':
            Popen( f'cat {MAIN_FOLDER}/doc/peaudiosys.hlp', shell=True)
            return 'help has been printed to stdout, also available on ' \
                    '\'~/pe.audio.sys/doc/peaudiosys.hlp\''
        result = {  'preamp':   process_preamp,
                    'player':   process_players,
                    'aux':      process_aux }[ pfx ]( cmd, arg )
        if type(result) != str:
            result = json.dumps(result)
        return result
    else:
        return 'nothing done'
