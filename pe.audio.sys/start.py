#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pe.audio.sys'
# 'pe.audio.sys', a PC based personal audio system.

"""
    usage:  start.py <mode> [ --log ]

    mode:
        'all'      :    restart all
        'stop'     :    stop all
        'server'   :    restart tcp server
        'scripts'  :    restart user scripts

    --log   messages redirected to 'pe.audio.sys/log/start.log'

"""

import  subprocess as sp
from    time import sleep, time, ctime
from    json import dumps as json_dumps
import  os
import  sys

UHOME = os.path.expanduser("~")
sys.path.append(f'{UHOME}/pe.audio.sys/share/miscel')

from    config import   CONFIG, STATE_PATH, MAINFOLDER, LOUDSPEAKER, LOG_FOLDER
from    miscel import   read_bf_config_fs, server_is_running, kill_bill,        \
                        read_state_from_disk, force_to_flush_file, Fmt


def prepare_extra_cards(channels=2):
    """ This launch resamplers that connects extra sound cards into Jack
        (void)
    """
    if not CONFIG['external_cards']:
        return

    for card, params in CONFIG['external_cards'].items():
        jack_name = card
        alsacard  = params['alsacard']
        resampler = params['resampler']
        quality   = str(params['resamplingQ'])
        try:
            misc = params['misc_params']
        except KeyError:
            misc = ''

        cmd = f'{resampler} -d {alsacard} -j {jack_name} ' + \
              f'-c {channels} -q {quality} {misc}'
        if 'zita' in resampler:
            cmd = cmd.replace("-q", "-Q")

        print(f'(start) loading resampled extra card: {card}')
        #print(cmd) # DEBUG
        sp.Popen(cmd.split(), stdout=sys.stdout, stderr=sys.stderr)


def run_jloops():
    """ Jack loops launcher
        (void)
    """
    # Jack loops launcher external daemon
    sp.Popen(f'{MAINFOLDER}/share/services/preamp_mod/jloops_daemon.py', shell=True)


def check_jloops():
    """ Jack loops checking
        (bool)
    """
    # The configured loops
    cfg_loops = []
    loop_names = ['pre_in_loop']
    for source in CONFIG['sources']:
        pname = CONFIG['sources'][source]['jack_pname']
        if 'loop' in pname and pname not in loop_names:  # avoids duplicates
            loop_names.append( pname )
    for loop_name in loop_names:
            cfg_loops.append( f'{loop_name}:input_1' )
            cfg_loops.append( f'{loop_name}:input_2' )
            cfg_loops.append( f'{loop_name}:output_1' )
            cfg_loops.append( f'{loop_name}:output_2' )

    if not cfg_loops:
        return True

    # Waiting for all loops to be spawned
    tries = 10
    while tries:
        # The running ones
        run_loops = sp.check_output(['jack_lsp', 'loop']).decode().split()
        if sorted(cfg_loops) == sorted(run_loops):
            break
        sleep(1)
        tries -= 1
    if tries:
        print(f'{Fmt.BLUE}(start) JACK LOOPS RUNNING{Fmt.END}')
        return True
    else:
        print(f'{Fmt.BOLD}(start) JACK LOOPS FAILED{Fmt.END}')
        return False


def jack_is_running():
    """ checks for jackd process to be running
        (bool)
    """
    try:
        sp.check_output('jack_lsp >/dev/null 2>&1'.split())
        return True
    except sp.CalledProcessError:
        return False


def start_jack_stuff():
    """ runs jackd with configured options, jack loops and extrernal cards ports
        (void)
    """
    warnings = ''

    jack_backend_options = CONFIG["jack_backend_options"] \
                    .replace('$autoCard', CONFIG["system_card"]) \
                    .replace('$autoFS', str(read_bf_config_fs()))

    cmdlist = ['jackd']

    if logFlag:
        cmdlist += ['--silent']

    cmdlist += f'{CONFIG["jack_options"]}'.split() + \
               f'{jack_backend_options}'.split()

    # Firewire: reset the Firewire Bus and run ffado-dbus-server
    if 'firewire' in cmdlist:
        print(f'{Fmt.BOLD}(start) resetting the FIREWIRE BUS, sorry for users '
              f'using other FW things :-|{Fmt.END}')
        sp.Popen('ffado-test BusReset'.split())
        sleep(1)
        print(f'{Fmt.BLUE}(start) running FIREWIRE DBUS SERVER ...{Fmt.END}')
        sp.Popen('killall -KILL ffado-dbus-server', shell=True)
        sp.Popen('ffado-dbus-server 1>/dev/null 2>&1', shell=True)
        sleep(2)

    # Pulseaudio
    if 'pulseaudio' in sp.check_output("pgrep -fl pulseaudio",
                                       shell=True).decode():
        cmdlist = ['pasuspender', '--'] + cmdlist

    # Launch JACKD process
    sp.Popen(cmdlist, stdout=sys.stdout, stderr=sys.stderr)
    sleep(1)

    # Will check if JACK ports are available
    tries = 10
    while tries:
        if jack_is_running():
            print(f'{Fmt.BOLD}{Fmt.BLUE}(start) JACKD STARTED{Fmt.END}')
            break
        print(f'(start) waiting for jackd ' + '.' * tries)
        sleep(.5)
        tries -= 1
    # Still will wait a few, convenient for fast CPUs
    sleep(.5)

    if not tries:
        # JACK FAILED :-/
        warnings += ' JACKD FAILED.'

    else:
        # Adding EXTRA SOUND CARDS resampled into jack, aka 'external_cards'
        prepare_extra_cards()

        # Emerging JACKLOOPS (external daemon)
        run_jloops()
        if not check_jloops():
            warnings += ' JACKLOOPS FAILED.'

    if warnings:
        return warnings.strip()
    else:
        return 'done'


def start_brutefir():
    """ runs Brutefir, connects to pream_in_loop and resets
        .state file with extra_delay = 0 ms
    """
    result = core.bf.restart_and_reconnect( ['pre_in_loop:output_1',
                                             'pre_in_loop:output_2'],
                                             delay=0.0 )
    # Ensuring that .state keeps extra_delay = 0 ms from start
    tmp_state = read_state_from_disk()
    tmp_state["extra_delay"] = 0.0
    force_to_flush_file(STATE_PATH, json_dumps(tmp_state))
    return result


def manage_server( mode='', service='peaudiosys'):
    """ Manages the server running in background
        (void)
    """

    try:
        SRV_ADDR, SRV_PORT = CONFIG['peaudiosys_address'], CONFIG['peaudiosys_port']
    except:
        raise Exception(f'{Fmt.RED}(start) ERROR reading address/port '
                        f'in \'config.yml\'{Fmt.END}')

    if mode == 'stop':
        # Stop
        print(f'{Fmt.RED}(start) stopping \'server.py {service}\'{Fmt.END}')
        sp.Popen( f'pkill -KILL -f "server.py {service}" \
                   >/dev/null 2>&1', shell=True, stdout=sys.stdout,
                                                 stderr=sys.stderr)

    elif mode == 'start':
        # Start
        if service == 'restart':
            SRV_PORT += 1
        print(f'{Fmt.BLUE}(start) starting \'server.py ' \
              f'{service} {SRV_ADDR}:{SRV_PORT}\'{Fmt.END}')
        cmd = f'python3 {MAINFOLDER}/share/miscel/server.py ' \
              f'{service} {SRV_ADDR} {SRV_PORT}'
        sp.Popen(cmd, shell=True, stdout=sys.stdout, stderr=sys.stderr)

    else:
        raise Exception(f'bad manage_server call')


def stop_processes(mode):
    """ (void)
    """
    # Killing any previous instance of start.py
    kill_bill( os.getpid() )

    # Stop scripts
    if mode in ('all', 'stop', 'scripts'):
        run_scripts(mode='stop')

    if mode in ('all', 'stop'):
        # Stop Brutefir
        print(f'(start) STOPPING BRUTEFIR')
        sp.Popen('pkill -KILL -f brutefir >/dev/null 2>&1', shell=True)

        # Stop Jack Loops Daemon
        print(f'(start) STOPPING JACK LOOPS')
        sp.Popen('pkill -KILL -f jloops_daemon.py >/dev/null 2>&1', shell=True)

        # Stop Jack
        print(f'(start) STOPPING JACKD')
        sp.Popen('pkill -KILL -f jackd >/dev/null 2>&1', shell=True)

    if mode in ('all', 'stop', 'server'):
        # Stop the servers:
        manage_server(mode='stop', service='peaudiosys')
        manage_server(mode='stop', service='restart')

    sleep(3)


def run_scripts(mode='start'):
    """ (void)
    """
    for script in CONFIG['scripts']:
        # (i) Some elements on the scripts list from config.yml can be a dict,
        #     e.g the ecasound_peq, so we need to extract the script name.
        if type(script) == dict:
            script = list(script.keys())[0]
        print(f'(start) will {mode} the script \'{script}\' ...')
        # (i) Notice that we are open to run scripts writen in python, bash, etc...
        sp.Popen(f'{MAINFOLDER}/share/scripts/{script} {mode}', shell=True,
                                  stdout=sys.stdout, stderr=sys.stderr)
    if mode == 'stop':
        sleep(.5)  # this is necessary because of asyncronous stopping


def check_state_file():
    """ restores a copy of .state if it was damaged by a sudden power break out
        (void)
    """
    state_file      = STATE_PATH
    state_log_file  = f'{LOG_FOLDER}/state.log'

    def recover_state(reason='damaged'):
        sp.Popen(f'cp {state_file}.BAK {state_file}'.split())
        print(f'{Fmt.BOLD}(start) ERROR \'.state\' file was {reason}, '
              f'it has been restored from \'.state.BAK\'{Fmt.END}')
        now = ctime(time())
        with open(state_log_file, 'a') as f2:
            f2.write(f'{now}: \'.state\' was {reason} and restored.\n')

    try:
        with open(state_file, 'r') as f:
            state = f.read()

            # if last field is ok, let's assume the whole file is ok
            if '"xo_set":' in state:
                sp.Popen(f'cp {state_file} {state_file}.BAK'.split())
                print(f'{Fmt.BLUE}(start) (i) .state copied to .state.BAK{Fmt.END}')

            # file damaged, lets recover from backup, and log to state.log
            else:
                recover_state(reason='damaged')
    except:
                recover_state(reason='missed')


def prepare_drc_graphs():
    """ used by the control web page
        (void)
    """
    print(f'(start) processing drc sets to web/images/{LOUDSPEAKER} in background')
    sp.Popen([ 'python3', f'{MAINFOLDER}/share/www/scripts/drc2png.py', '-q' ])


if __name__ == "__main__":

    # READING OPTIONS FROM COMMAND LINE
    logFlag = False

    if sys.argv[1:]:
        mode = sys.argv[1]
    else:
        print(__doc__)
        sys.exit()

    if sys.argv[2:] and '-l' in sys.argv[2]:
        logFlag = True

    if mode not in ['all', 'stop', 'server', 'scripts']:
        print(__doc__)
        sys.exit()

    if logFlag:
        print('\n' + '-' * 80)
        print(f'start process logged at \'{LOG_FOLDER}/start.log\'')
        print('-' * 80)
        flog = open(f'{LOG_FOLDER}/start.log', 'w')
        original_stdout = sys.stdout
        original_stderr = sys.stderr
        sys.stdout = flog
        sys.stderr = flog

    # CHECKING STATE FILE
    check_state_file()

    # STOPPING:
    stop_processes(mode)

    if mode in ('stop', 'shutdown'):
        print(f'(start) Bye!')
        sys.exit()

    # STARTING:
    if mode in ('all'):
        # If necessary will prepare DRC GRAPHS for use of the web page
        if CONFIG["web_config"]["show_graphs"]:
            prepare_drc_graphs()

        # Starting JACK, EXTERNAL_CARDS and JLOOPS
        jack_stuff = start_jack_stuff()
        if  jack_stuff != 'done':
            print(f'{Fmt.BOLD}(start) Problems starting JACK: {jack_stuff}{Fmt.END}')
            sys.exit()

    # USER SCRIPTS
    if mode in ('all', 'scripts'):
        run_scripts()

    if mode in ('all'):

        # INIT AUDIO by importing 'core' temporally (needs JACK to be running)
        import share.services.preamp_mod.core as core
        print(f'{Fmt.MAGENTA}(start) Managing a temporary \'core\' instance.{Fmt.END}')

        # - BRUTEFIR
        bfstart = start_brutefir()
        if bfstart == 'done':
            print(f'{Fmt.BOLD}{Fmt.BLUE}(start) BRUTEFIR STARTED.{Fmt.END}')
        else:
            print(f'({Fmt.BOLD}start) Problems starting BRUTEFIR: {bfstart}')
            sys.exit()

        # - RESTORE ON_INIT AUDIO settings
        core.init_audio_settings()

        # - PREAMP  -->  MONITORS
        core.connect_monitors()

        del core
        print(f'{Fmt.MAGENTA}(start) Closing the temporary \'core\' instance.{Fmt.END}')


    # RUN THE SERVERS
    manage_server(mode='start', service='restart')
    manage_server(mode='start', service='peaudiosys')
    if not server_is_running(who_asks='start'):
        sys.exit()

    # OPTIONAL USER MACRO AT START
    if mode in ('all'):
        if 'run_macro' in CONFIG:
            mname = CONFIG["run_macro"]
            if mname:
                print( f'{Fmt.BLUE}(start) triyng macro \'{mname}\'{Fmt.END}' )
                sp.Popen( f'{MAINFOLDER}/macros/{mname}'.split() )

    # END
