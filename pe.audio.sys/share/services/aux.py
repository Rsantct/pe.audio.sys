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

""" auxiliary services: not preamp-core neither players related
"""

#   https://watchdog.readthedocs.io/en/latest/
from watchdog.observers     import  Observer
from watchdog.events        import  FileSystemEventHandler
import  jack
import  json
from    subprocess          import  Popen
from    time                import  sleep
import  os
import  sys
import  threading

UHOME = os.path.expanduser("~")
sys.path.append(f'{UHOME}/pe.audio.sys/share/miscel')

from    config          import  CONFIG, MAINFOLDER, MACROS_FOLDER,      \
                                AMP_STATE_PATH, LDMON_PATH, LDCTRL_PATH

from    miscel          import  read_state_from_disk, send_cmd, is_IP,  \
                                wait4ports, process_is_running, Fmt

from    brutefir_mod    import  add_delay as bf_add_delay,              \
                                is_running as bf_is_running


def dump_aux_info():
    # Dynamic updates
    AUX_INFO['amp'] =               manage_amp_switch( 'state' )
    AUX_INFO['loudness_monitor'] =  get_loudness_monitor()
    # Dumping to disk
    with open(f'{MAINFOLDER}/.aux_info', 'w') as f:
        f.write( json.dumps(AUX_INFO) )


def get_web_config():

    wconfig = CONFIG['web_config']

    # Macros used by the web page
    wconfig['user_macros'] = get_macros(only_web_macros=True)

    # Main selector manages inputs or macros
    if not 'main_selector' in wconfig:
        wconfig['main_selector'] = 'inputs';
    else:
        if wconfig['main_selector'] not in ('inputs', 'macros'):
            wconfig['main_selector'] = 'inputs'

    # Complete some additional info
    wconfig['restart_cmd_info']   = CONFIG['restart_cmd']
    wconfig['LU_monitor_enabled'] = True if 'loudness_monitor.py' \
                                              in CONFIG['scripts'] else False

    return wconfig


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
        Popen( f'{AMP_MANAGER} {mode}', shell=True )
        sleep(1)
        return get_amp_state()


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

    # Optionally will stop the current player as per CONFIG
    if new_state == 'off':
        if 'amp_off_stops_player' in CONFIG and CONFIG['amp_off_stops_player']:
            curr_input = read_state_from_disk()['input']
            if not curr_input.startswith('remote'):
                send_cmd('player pause', timeout=1)

    return result


def get_macros(only_web_macros=False):
    """ Return the list of executable files under macros folder. The list
        can be restricted to web macros NN_xxxxxx, then numeric sorted.
    """
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

    macro_files.sort()

    # (i) The web page needs a sorted list (numeric sorting only if NN_xxxxxx items)
    if only_web_macros:
        macro_files.sort( key=lambda x: int(x.split('_')[0]) )

    return macro_files


def run_macro(mname):
    if mname in get_macros():
        print( f'(aux) running macro: {mname}' )
        Popen( f'"{MACROS_FOLDER}/{mname}"', shell=True)
        AUX_INFO["last_macro"] = mname
        # for others to have fresh 'last_macro'
        dump_aux_info()
        return 'ordered'
    else:
        return 'macro not found'


def get_loudness_monitor():
        try:
            with open(LDMON_PATH, 'r') as f:
                result = json.loads( f.read() )
        except:
            if 'LU_reset_scope' in CONFIG:
                result = {'LU_I': 0.0, 'LU_M':0.0,
                          'scope': CONFIG["LU_reset_scope"]}
            else:
                result = {'LU_I': 0.0, 'LU_M':0.0, 'scope': 'album'}
        return result


def available_commands():
    """ List of end user commands managed under this module
    """
    cmd_list = ['amp_switch', 'get_macros', 'get_last_macro', 'run_macro',
                'play_url', 'loudness_monitor_reset', 'lu_monitor_reset' ,
                'set_loudness_monitor_scope', 'set_lu_monitor_scope',
                'get_loudness_monitor', 'get_lu_monitor',
                'restart', 'get_aux_info', 'info', 'add_delay', 'warning'
                ]
    return cmd_list


def warning_expire(timeout=5):
    """ Threads a timer to clear the warning message field inside .aux_info
    """
    def mytimer(timeout):
        sleep(timeout)
        AUX_INFO['warning'] = ''
        dump_aux_info()
    job = threading.Thread(target=mytimer, args=(timeout,))
    job.start()


def zita_client(argvs):
    """ Sends audio to a zita-njbridge (issued from a multiroom receiver)
    """
    addr = ''
    stop = False

    # Reading arguments
    for argv in argvs.split(' '):
        if is_IP(argv):
            addr = argv
        elif argv == 'stop':
            stop = True

    # Bad address
    if not addr:
        return 'bad address'

    jcli        = jack.Client(name='zitatmp', no_start_server=True)
    udpport     = addr.split('.')[-1]
    zitajname   = f'zita-{udpport}'

    # if stop
    if stop:
        Popen( f'pkill -KILL -f {zitajname}'.split() )
        return f'{zitajname} killed'

    jports = jcli.get_ports()
    if not [x for x in jports if zitajname in x.name]:
        zitacmd     = f'zita-j2n --jname {zitajname} {addr} 65{udpport}'
        Popen( zitacmd.split() )
        sleep(1)

    try:
        jcli.connect( 'pre_in_loop:output_1', f'zita-{udpport}:in_1' )
        jcli.connect( 'pre_in_loop:output_2', f'zita-{udpport}:in_2' )
    except:
        pass

    jcli.close()

    return 'done'


def play_url(arg):
    """ Aux for playback an url stream
    """
    # As per this function is a compound function, I have decided
    # to hold it here instead of inside the players module

    def istreams_query(url):
        """ Order the istreams daemon script to playback an internet stream url
        """
        error = False

        # Tune the radio station (Mplayer jack ports will dissapear for a while)
        Popen( f'{UHOME}/pe.audio.sys/share/scripts/istreams.py url {url}'
                .split() )
        # Waits a bit to Mplayer ports to dissapear from jack while loading a new stream.
        sleep(2)
        # Waiting for mplayer ports to re-emerge
        if not wait4ports( f'mplayer_istreams' ):
            print(f'(aux) ERROR jack ports \'mplayer_istreams\''
                   ' not found' )
            error = True
        if not error:
            # Switching the preamp input
            send_cmd('preamp input istreams')
            return True
        else:
            return False

    if arg.startswith('http://') or arg.startswith('https://'):
        if istreams_query(arg):
            result = 'ordered'
        else:
            result = 'failed'
    else:
        result = f'(aux) bad url: {arg}'

    return result


def manage_lu_monitor(string):
    """ Manages the loudness_monitor.py daemon through by its fifo
    """
    #   As per LDCTRL_PATH is a namedpipe (FIFO), it is needed that
    #   'loudness_monitor.py' was alive in order to release any write to it.
    #   If not alive, any f.write() to LDCTRL_PATH will HANG UP
    #   :-(
    if not process_is_running('loudness_monitor.py'):
        return 'ERROR loudness_monitor.py NOT running'
    try:
        with open(LDCTRL_PATH, 'w') as f:
            f.write(string)
        return 'ordered'
    except Exception as e:
        return f'ERROR writing .loudness_control FIFO: {str(e)}'


def manage_warning_msg(arg):
    """ Manages the warning field under .aux_info than can be used
        from the control web page interface
    """
    args = arg.split()

    if args[0] == 'set':

        if AUX_INFO['warning']:
            result = 'warning message in use'
        else:
            AUX_INFO['warning'] = ' '.join(args[1:])
            dump_aux_info()
            warning_expire(timeout=60)
            result = 'done'

    elif args[0] == 'clear':
        AUX_INFO['warning'] = ''
        dump_aux_info()
        result = 'done'

    elif args[0] == 'get':
        result = AUX_INFO['warning']

    elif args[0] == 'expire':
        if args[1:] and args[1].isdigit():
            warning_expire(timeout=int(args[1]))
            result = 'done'
        else:
            result = 'bad expire timeout'
    else:
        result = 'usage: warning set message | warning clear'

    return result


def add_delay(arg):
    """ Add outputs delay, can be useful for multiroom listening
    """
    print(f'(aux) ordering adding {arg} ms of delay.')
    # (i) Brutefir must be running
    if not bf_is_running():
        send_cmd('preamp convolver on')
    return bf_add_delay(float(arg))


def do_restart_peaudiosys():
    try:
        restart_cmd = CONFIG["restart_cmd"]
    except:
        restart_cmd = f'{UHOME}/start.py all'
    try:
        Popen( f'{restart_cmd}'.split() )
        result = f'ordered: \'{restart_cmd}\''
        print( f'{Fmt.BOLD}(aux) {result}{Fmt.END}' )
    except:
        result = f'error running \'{restart_cmd}\''
        print( f'{Fmt.BOLD}(aux) {result}{Fmt.END}' )
    return result


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
        #print( f'(aux) event type: {event.event_type}, file: {event.src_path}' )
        if event.src_path == self.wanted_path:
            dump_aux_info()


# auto-started when loading this module
def init():

    global AUX_INFO
    AUX_INFO = {    'amp':                  'off',
                    'loudness_monitor':     0.0,
                    'web_config':           get_web_config(),
                    'last_macro':           '-',                # cannot be empty
                    'warning':              ''
                }

    # First update
    dump_aux_info()

    # Starts a WATCHDOG to observe file changes
    #   https://watchdog.readthedocs.io/en/latest/
    #   https://stackoverflow.com/questions/18599339/
    #   python-watchdog-monitoring-file-for-changes
    #   Use recursive=True to observe also subfolders
    #   Even observing recursively the CPU load is negligible,
    #   but we prefer to observe to a single folder.

    # Will observe for changes in AMP_STATE_PATH:
    observer1 = Observer()
    observer1.schedule( files_event_handler(AMP_STATE_PATH),
                        path=os.path.dirname(AMP_STATE_PATH),
                        recursive=False )
    observer1.start()

    # Will observe for changes in LDMON_PATH:
    observer2 = Observer()
    observer1.schedule( files_event_handler(LDMON_PATH),
                        path=os.path.dirname(LDMON_PATH),
                        recursive=False )
    observer2.start()


# Interface function for this module
def do( cmd, arg ):
    """ input:  command [, arg]
        output: an execution result string
    """

    cmd = cmd.lower()

    if cmd == 'amp_switch':
        result = manage_amp_switch(arg)

    elif cmd == 'get_macros':
        result = get_macros()

    elif cmd == 'get_last_macro':
        result = AUX_INFO['last_macro']

    elif cmd == 'run_macro':
        result = run_macro(arg)

    elif cmd == 'play_url':
        result = play_url(arg)

    elif cmd == 'loudness_monitor_reset' or cmd == 'lu_monitor_reset':
        result = manage_lu_monitor('reset')

    elif cmd == 'set_loudness_monitor_scope' or cmd == 'set_lu_monitor_scope':
        result = manage_lu_monitor(f'scope={arg}')

    elif cmd == 'get_loudness_monitor' or cmd == 'get_lu_monitor':
        result = get_loudness_monitor()

    elif cmd == 'get_aux_info' or cmd == 'info':
        result = AUX_INFO

    elif cmd == 'add_delay':
        result = add_delay(arg)

    elif cmd == 'zita_client':
        result = zita_client(arg)

    elif cmd == 'restart':
        result = do_restart_peaudiosys()

    elif cmd == 'help':
        result = ' '.join( available_commands() )

    elif cmd == 'warning':
        result = manage_warning_msg(arg)

    else:
        result = f'(aux) bad command \'{cmd}\''

    return result


# Will AUTO-START init() when loading this module
init()
