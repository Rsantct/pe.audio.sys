#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pe.audio.sys'
# 'pe.audio.sys', a PC based personal audio system.

""" auxiliary services: not preamp-core neither players related
"""

#   https://watchdog.readthedocs.io/en/latest/
from watchdog.observers     import  Observer
from watchdog.events        import  FileSystemEventHandler
import  jack
from    subprocess          import  Popen
from    time                import  sleep
import  os
import  sys
import  threading

UHOME = os.path.expanduser("~")
sys.path.append(f'{UHOME}/pe.audio.sys/share/miscel')

from    config      import  CONFIG, MAINFOLDER, MACROS_FOLDER, \
                            AMP_STATE_PATH, LDMON_PATH, LDCTRL_PATH

from    miscel      import  *

from    peq_mod     import eca_bypass, eca_load_peq


def dump_aux_info():
    """ A helper to write AUX_INFO dict to a file to be accesible
        by third party processes
    """
    # Dynamic updates
    AUX_INFO['amp'] =               manage_amp_switch( 'state' )
    AUX_INFO['loudness_monitor'] =  get_loudness_monitor()
    # Dumping to disk
    with open(AUX_INFO_PATH, 'w') as f:
        f.write( json_dumps(AUX_INFO) )


def get_web_config():
    """ used by the control web page client
    """

    wconfig = CONFIG['web_config']

    # Macros used by the web page
    wconfig['user_macros'] = get_macros(only_web_macros=True)

    # Main selector manages inputs or macros
    if not 'main_selector' in wconfig:
        wconfig['main_selector'] = 'inputs';
    else:
        if wconfig['main_selector'] not in ('inputs', 'macros'):
            wconfig['main_selector'] = 'inputs'

    # Adding LU_monitor_enabled
    wconfig['LU_monitor_enabled'] = True if 'loudness_monitor.py' \
                                              in CONFIG['plugins'] else False

    return wconfig


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


def zita_j2n(args):
    """ This internal function is always issued from a multiroom receiver.

        Feeds the preamp audio to a zita-j2n port pointing to the receiver.

        args: a json tuple string "(dest, udpport, do_stop)"
    """

    dest, udpport, do_stop = json_loads(args)

    # BAD ADDRESS
    if not is_IP(dest):
        return 'bad address'

    zitajname = f'zita_j2n_{ dest.split(".")[-1] }'

    # STOP mode
    if do_stop == 'stop':
        zitapattern  = f'zita-j2n --jname {zitajname}'
        Popen( ['pkill', '-KILL', '-f',  zitapattern] )
        sleep(.2)
        return f'killing {zitajname}'

    # NORMAL mode
    jcli = jack.Client(name='zitatmp', no_start_server=True)
    jports = jcli.get_ports()
    result = ''
    if not [x for x in jports if zitajname in x.name]:
        zitacmd     = f'zita-j2n --jname {zitajname} {dest} {udpport}'
        with open('/dev/null', 'w') as fnull:
            Popen( zitacmd.split(), stdout=fnull, stderr=fnull )

    wait4ports(zitajname, timeout=3)

    try:
        jcli.connect( 'pre_in_loop:output_1', f'{zitajname}:in_1' )
        jcli.connect( 'pre_in_loop:output_2', f'{zitajname}:in_2' )
        result = 'done'
    except Exception as e:
        result = str(e)

    jcli.close()

    return result


def peq_load(peqpath):
    """ a wrapper to load a PEQ file and updating .aux_info

        returns: 'done' or some error string
    """
    res = eca_load_peq(peqpath)

    # updatting .aux_info
    if res == 'done':
        AUX_INFO["peq_set"] = os.path.basename(peqpath).replace('.peq','')
        AUX_INFO['peq_bypassed'] = eca_bypass('get')
        dump_aux_info()

    return res


def peq_bypass(mode):
    """ a wrapper to manage Ecasound chains bypass
        mode:       on | off | toggle | get
        return:     [L_mode, R_mode]
    """

    newmode = eca_bypass(mode)

    AUX_INFO['peq_bypassed'] = newmode
    dump_aux_info()

    return f'{newmode}'


def play_url(arg):
    """ Aux for playback an url stream
    """
    # As per this function is a compound function, I have decided
    # to hold it here instead of inside the players module

    def istreams_query(url):
        """ Order the istreams daemon plugin to playback an internet stream url
        """
        error = False

        # Tune the radio station (Mplayer jack ports will dissapear for a while)
        Popen( f'{MAINFOLDER}/share/plugins/istreams.py url {url}'.split() )

        # Waits a bit to Mplayer ports to dissapear from jack while loading a new stream.
        sleep(2)

        # Waiting for mplayer ports to re-emerge
        if not wait4ports( f'mplayer_istreams' ):
            print(f'(aux) ERROR jack ports \'mplayer_istreams\''
                   ' not found' )
            error = True

        if not error:
            # Switching the preamp input
            # PATCH: using timeout is needed unless send_cmd was modified
            send_cmd('preamp input istreams', 'aux play_url ...', True, 1)
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


def warning_expire(timeout=5):
    """ Threads a timer to clear the warning message field inside .aux_info
    """
    def mytimer(timeout):
        sleep(timeout)
        AUX_INFO['warning'] = ''
        dump_aux_info()
    job = threading.Thread(target=mytimer, args=(timeout,))
    job.start()


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

    if args[0] == 'perm':

        if AUX_INFO['warning']:
            result = 'warning message in use'
        else:
            AUX_INFO['warning'] = ' '.join(args[1:])
            dump_aux_info()
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


def alert_new_eq_graph(timeout=1):
    """ This sets the 'new_eq_graph' field to True for a while
        so that the web page can realize when the graph is dumped.
        This helps on slow machines because the PNG graph takes a while
        after the 'done' is received when issuing some audio command.

        (i) Dumping this to the aux_info file is not needed because web
            clients pulls this AUX_INFO run time variable not from disk.
    """
    def mytimer(timeout):
        sleep(timeout)
        AUX_INFO['new_eq_graph'] = False
    job = threading.Thread(target=mytimer, args=(timeout,))
    job.start()
    AUX_INFO['new_eq_graph'] = True
    return f'alerting for {timeout} s'


def get_help():
    """ List of end user available commands
    """
    cmds = ['amp_switch', 'get_macros', 'run_macro', 'play_url',
            'reset_loudness_monitor', 'reset_lu_monitor' ,
            'set_loudness_monitor_scope', 'set_lu_monitor_scope',
            'get_loudness_monitor', 'get_lu_monitor', 'info', 'warning']
    return ', '.join( cmds )


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
                    'last_macro':           '',
                    'warning':              '',
                    'peq_set':              get_peq_in_use(),
                    'peq_bypassed':         eca_bypass('get')
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
def do( cmd, arg=None ):
    """ input:  command [, arg]
        output: an execution result string
    """

    cmd = cmd.lower()

    if   cmd == 'amp_switch':
        result = manage_amp_switch(arg)

    elif cmd == 'get_macros':
        result = get_macros()

    elif cmd == 'run_macro':
        result = run_macro(arg)

    elif cmd == 'play_url':
        result = play_url(arg)

    elif cmd == 'reset_loudness_monitor' or cmd == 'reset_lu_monitor':
        result = manage_lu_monitor('reset')

    elif cmd == 'set_loudness_monitor_scope' or cmd == 'set_lu_monitor_scope':
        result = manage_lu_monitor(f'scope={arg}')

    elif cmd == 'get_loudness_monitor' or cmd == 'get_lu_monitor':
        result = get_loudness_monitor()

    elif cmd == 'info':
        result = AUX_INFO

    elif cmd == 'zita_j2n':
        result = zita_j2n(arg)

    elif cmd == 'peq_bypass':
        result = peq_bypass(arg)

    elif cmd == 'peq_load':
        result = peq_load(arg)

    elif cmd == 'warning':
        result = manage_warning_msg(arg)

    elif cmd == 'get_web_config':
        result = get_web_config()

    elif cmd == 'alert_new_eq_graph':
        result = alert_new_eq_graph()

    elif cmd == 'help':
        result = get_help()

    else:
        result = f'(aux) bad command \'{cmd}\''

    return result


# Will AUTO-START init() when loading this module
init()
