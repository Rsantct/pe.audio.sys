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

""" Runs miscellaneous local tasks.
    This module is loaded by 'server.py'
"""

from socket import socket
import yaml
import json
from subprocess import Popen, check_output
import os
import sys
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
PLAYER_META_FILE    = f'{MAIN_FOLDER}/.player_metadata'
STATE_FILE          = f'{MAIN_FOLDER}/.state.yml'

aux_info = {    'amp':'off', 
                'loudness_monitor': 0.0,
                'user_macros': [],
                'web_config': {}
            }

## predic service addressing
try:
    with open(f'{MAIN_FOLDER}/config.yml', 'r') as f:
        cfg = yaml.safe_load(f)
        # (i) start.py will assign 'predic' port number this way:
        PRE_PORT = cfg['peaudiosys_port'] + 1
except:
    print(f'({ME}) ERROR with \'pe.audio.sys/config.yml\'')
    exit()

# Gets the amp manager script as defined inside config.yml
try:
    with open( f'{MAIN_FOLDER}/config.yml' , 'r' ) as f:
        tmp = yaml.safe_load( f )
    AMP_MANAGER =  tmp['aux']['amp_manager']
except:
    # This will be printed out to the terminal to advice the user:
    AMP_MANAGER =  'echo For amp switching please configure config.yml'

# Gets the web page config as defined in web.yml
try:
    with open( f'{MAIN_FOLDER}/web.yml' , 'r' ) as f:
        WEBCONFIG = yaml.safe_load( f )
except:
        WEBCONFIG = { 'at_startup':{'hide_macro_buttons':False} }

# Auxiliary to talk to the preamp control service.
def pre_control_cmd(cmd, host='localhost', port=PRE_PORT):
    ans = ''
    with socket() as s:
        try:
            s.connect( (host, port) )
            s.send( cmd.encode() )
            print (f'({ME}) Tx to preamp:   \'{cmd }\'')
            ans = s.recv(1024).decode()
            print (f'({ME}) Rx from preamp: \'{ans }\' ')
            s.close()
        except:
            print (f'({ME}) service \'peaudiosys\' socket error on port {port}')
    return ans

# Auxiliary to parse a command phrase string into a tuple (cmd,arg) 
def read_command_phrase(command_phrase):
    cmd, arg = None, None
    # This is to avoid empty values when there are more
    # than on space as delimiter inside the command_phrase:
    opcs = [x for x in command_phrase.split(' ') if x]
    try:
        cmd = opcs[0]
    except:
        raise
    try:
        # allows spaces inside the arg part, e.g. 'run_macro 2_Radio Clasica'
        arg = ' '.join( opcs[1:] )
    except:
        pass
    return cmd, arg

# Main function for command processing
def process( cmd, arg=None ):
    """ input:  a tuple (command, arg)
        output: a result string
    """
    result = ''
        
    # Get PLAYER METADATA
    if cmd == 'player_get_meta':
        try:
            with open(PLAYER_META_FILE, 'r') as f:
                result = json.loads(f.read())
        except:
            result = {}
        

    # AMPLIFIER SWITCHING
    elif cmd == 'amp_switch':

        # current switch state
        try:
            with open( f'{AMP_STATE_FILE}', 'r') as f:
                tmp =  f.read().strip()
            if tmp.lower() in ('0','off'):
                curr_sta = 'off'
            elif tmp.lower() in ('1','on'):
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
            new_sta = {'on':'off', 'off':'on'}.get(curr_sta, 'on')

        if arg in ('on','off'):
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
                if ( fname[0] in [str(x) for x in range(1,10)] ) and fname[1]=='_':
                    macro_files.append(fname)
        result = macro_files

    # RUN MACRO
    elif cmd == 'run_macro':
        print( f'({ME}) running macro: {arg}' )
        Popen( f'"{MACROS_FOLDER}/{arg}"', shell=True)
        result = 'tried'

    # RESET the LOUDNESS MONITOR DAEMON:
    elif cmd == 'loudness_monitor_reset':
        try:
            with open(LOUD_MON_CTRL_FILE, 'w') as f:
                f.write('reset')
            result = 'done'
        except:
            result = 'error'

    # Get the LOUDNESS MONITOR VALUE from the 
    # loudness monitor daemon's output file:
    elif cmd == 'get_loudness_monitor':
        try:
            with open(LOUD_MON_VAL_FILE, 'r') as f:
                result = round( float(f.read().strip()), 1)
        except:
            result = ''

    # RESTART
    elif cmd == 'restart':
        try:
            restart_action = WEBCONFIG["reboot_button_action"]
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

    # ANY ELSE WILL BE SENT TO THE PREAMP SERVER:
    else:
        result = pre_control_cmd( ' '.join( (cmd, arg) ) )

    return result

# Dumps pe.audio.sys/.aux_info
def dump_aux_info():
    aux_info['amp'] =               process('amp_switch', 'state')
    aux_info['loudness_monitor'] =  process('get_loudness_monitor')
    aux_info['user_macros'] =       process('get_macros')
    aux_info['web_config'] =        process('get_web_config')
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
    cmd, arg = read_command_phrase( command_phrase
                                              .replace('\n','').replace('\r','') )
    result = process( cmd, arg )
    return json.dumps(result).encode()

# command line use (DEPRECATED)
if __name__ == '__main__':

    if sys.argv[1:]:

        command_phrase = ' '.join (sys.argv[1:] )
        cmd, arg = read_command_phrase( command_phrase )
        result = process( cmd, arg )
        print( result )
