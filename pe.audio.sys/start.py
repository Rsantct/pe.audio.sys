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

    --log   messages redirected to 'pe.audio.sys/log/start.log'

"""

import  subprocess as sp
from    time import sleep, time, ctime, gmtime, strftime
from    json import dumps as json_dumps
from    types import SimpleNamespace
import  os
import  sys

UHOME = os.path.expanduser("~")
sys.path.append(f'{UHOME}/pe.audio.sys/share/miscel')

from config import  CONFIG, STATE_PATH, MAINFOLDER, LOUDSPEAKER, LOG_FOLDER

from miscel import  read_bf_config_fs, server_is_running, process_is_running, \
                    kill_bill, read_state_from_disk, force_to_flush_file, Fmt, \
                    get_remote_sources, remote_zita_restart, local_zita_restart, \
                    send_cmd, get_my_ip

from sound_cards import *


def load_extra_cards(channels=2):
    """ This launch resamplers that connects extra sound cards into Jack
        (void)
    """
    jc = CONFIG["jack"]
    if ('external_cards' not in jc) or (not jc["external_cards"]):
        return

    ext_cards = jc["external_cards"]

    for card, params in ext_cards.items():
        jack_name = card
        device    = params['device']
        resampler = params['resampler']

        if ('resamplingQ' in params) and (params['resamplingQ']):
            quality = params['resamplingQ']
        else:
            quality = ''

        if ('misc_params' in params) and (params['misc_params']):
            misc = params['misc_params']
        else:
            misc = ''

        if (not quality) and ('zita' in resampler):
                quality == 'auto'

        cmd = f'{resampler} -d {device} -j {jack_name} -c {channels}'

        if quality:
            cmd += f' -q {quality}'

        if misc:
            cmd += f' {misc}'

        if 'zita' in resampler:
            cmd = cmd.replace("-q", "-Q")

        print(f'(start) loading resampled extra card: {card}')
        sp.Popen(cmd, shell=True, stdout=sys.stdout, stderr=sys.stderr)


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

    jc = CONFIG['jack']

    # silent (no Xrun messages)
    if ('silent' in jc) and (jc["silent"] == True):
        jOpts = f'-R --silent -d {jc["backend"]}'
    else:
        jOpts = f'-R -d {jc["backend"]}'

    # default period and nperiod
    if ('period' not in jc) or not jc["period"]:
        jc["period"] = 1024
    if ('nperiods' not in jc) or not jc["nperiods"]:
        jc["nperiods"] = 2

    if jc["backend"] != 'dummy':
        jBkndOpts  = f'-d {jc["device"]} -p {jc["period"]} -n {jc["nperiods"]}'
    else:
        jBkndOpts  = f'-p {jc["period"]}'

    # set FS
    jBkndOpts += f' -r {read_bf_config_fs()}'

    # other backend options (config.yml)
    if ('miscel' in jc) and (jc["miscel"]):
        jBkndOpts += f' {jc["miscel"]}'

    # Use 'softmode' for ALSA backend even if not configured under 'miscel:'
    # (i) This does not disable Xrun printouts if any occurs (see man page)
    if ('alsa' in jOpts) and ('-s' not in jBkndOpts):
        jBkndOpts += ' --softmode'

    # Firewire: reset the Firewire Bus and run ffado-dbus-server
    if jc["backend"] == 'firewire':
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
        release_cards_from_pulseaudio()

    # Launch JACKD process
    with open(f'{LOG_FOLDER}/jackd.log', 'w') as jlog:
        sp.Popen(f'jackd {jOpts} {jBkndOpts}', shell=True,
                        stdout=jlog,
                        stderr=jlog)

    # Will check if JACK ports are available
    sleep(1)
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
        load_extra_cards()

        # Emerging JACKLOOPS (external daemon)
        run_jloops()
        if not check_jloops():
            warnings += ' JACKLOOPS FAILED.'

    if warnings:
        return warnings.strip()
    else:
        return 'done'


def start_zita_link():
    """ A LAN audio connection based on zita-njbridge from Fons Adriaensen.

            "similar to having analog audio connections between the
            sound cards of the systems using it"

        Further info at doc/80_Multiroom_pe.audio.sys.md
    """

    try:
        tmp = CONFIG["zita_udp_base"]
        if type(tmp) == int:
            UDP_PORT = tmp
        else:
            raise Exception("BAD VALUE 'zita_udp_base'")
    except Exception as e:
        UDP_PORT = 65000
        print(f'{Fmt.RED}(start) ERROR in config.yml: {str(e)}, using {UDP_PORT} {Fmt.END}')

    try:
        tmp = CONFIG["zita_buffer_ms"]
        if type(tmp) == int:
            ZITA_BUFFER_MS = tmp
        else:
            raise Exception("BAD VALUE 'zita_buffer_ms'")
    except Exception as e:
        ZITA_BUFFER_MS = 20
        print(f'{Fmt.RED}(start) ERROR in config.yml: {str(e)}, using {ZITA_BUFFER_MS} {Fmt.END}')


    zita_link_ports = {}


    for item in REMOTES:

        source_name, raddr, rport = item
        print( f'(start) Running zita-njbridge for: {source_name}' )

        # Trying to RUN THE REMOTE SENDER zita-j2n (*)
        remote_zita_restart(raddr, rport, UDP_PORT)

        # Append the UPD_PORT to zita_link_ports
        zita_link_ports[source_name] = {'addr': raddr, 'udpport': UDP_PORT}

        # RUN LOCAL RECEIVER:
        local_zita_restart(raddr, UDP_PORT, ZITA_BUFFER_MS)

        # (i) zita will use 2 consecutive ports, so let's space by 10
        UDP_PORT += 10

    # (*) Saving the zita's UDP PORTS for future use because
    #     the remote sender could not be online at the moment ...
    with open(f'{MAINFOLDER}/.zita_link_ports', 'w') as f:
        d = json_dumps( zita_link_ports )
        f.write(d)


def stop_zita_link():

    for item in REMOTES:

        _, raddr, rport = item

        # REMOTE
        zargs = json_dumps( (get_my_ip(), None, 'stop') )
        remotecmd = f'aux zita_j2n {zargs}'
        send_cmd(remotecmd, host=raddr, port=rport, timeout=1)

        # LOCAL
        zitajname  = f'zita_n2j_{ raddr.split(".")[-1] }'
        zitapattern  = f'zita-n2j --jname {zitajname}'
        sp.Popen( ['pkill', '-KILL', '-f',  zitapattern] )
        sleep(.2)


def start_brutefir():
    """ runs Brutefir, connects to pream_in_loop and resets
        .state file with extra_delay = 0 ms
        (bool)
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
        # ***NOTICE*** the -f "srtring " MUST have an ending blank in order
        #              to avoid confusion with 'peaudiosys_ctrl'
        sp.Popen( f'pkill -KILL -f "server.py {service} " \
                   >/dev/null 2>&1', shell=True, stdout=sys.stdout,
                                                 stderr=sys.stderr)

    elif mode == 'start':
        # Start
        if service == 'peaudiosys_ctrl':
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
    def wait4jackdkilled():
        tries = 20
        print('(start) waiting for jackd to be killed ')
        while tries:
            try:
                sp.check_output('pgrep -f jackd'.split())
                tries -= 1
                sleep(1)
            except:
                print('(start) jackd was killed')
                sleep(1)
                return
        # This should never happen
        print(f'{Fmt.BOLD}(start) jackd still running, exiting :-/{Fmt.BOLD}')
        sys.exit()

    # Stop the server:
    if mode in ('all', 'stop', 'server'):
        manage_server(mode='stop', service='peaudiosys')

    # Killing any previous instance of start.py
    kill_bill( os.getpid() )

    # Stop plugins
    if mode in ('all', 'stop'):
        run_plugins(mode='stop')

    if mode in ('all', 'stop'):
        # Stop Jack Loops Daemon
        print(f'(start) STOPPING JACK LOOPS')
        sp.Popen('pkill -KILL -f jloops_daemon.py >/dev/null 2>&1', shell=True)
        # Stop Brutefir
        print(f'(start) STOPPING BRUTEFIR')
        sp.Popen('pkill -KILL -f brutefir >/dev/null 2>&1', shell=True)
        # Stop Zita_Link
        if REMOTES:
            print(f'(start) STOPPING ZITA_LINK')
            stop_zita_link()
        # Stop Jack
        print(f'(start) STOPPING JACKD')
        sp.Popen('pkill -KILL -f jackd >/dev/null 2>&1', shell=True)

    # This optimizes instead of a fixed sleep
    wait4jackdkilled()


def run_special_plugins():
    """ Special plugins

        - Amplifier switch needs to power on the external DAC in order to
          by accesible from the alsa module

        - Zeroing alsa mixer must be done before restoring
          the saved level if alsa mixer is used for volume management.
    """

    # Using 'call' to wait for the script to finish
    if 'power_amp_control.py' in CONFIG['plugins']:
        cmd = f'{MAINFOLDER}/share/plugins/power_amp_control.py start'
        print(f'(start) starting plugin: power_amp_control.py ...')
        sp.call(cmd, shell=True, stdout=sys.stdout, stderr=sys.stderr)

    if 'sound_cards_prepare.py' in CONFIG['plugins']:
        cmd = f'{MAINFOLDER}/share/plugins/sound_cards_prepare.py start'
        print(f'(start) starting plugin: sound_cards_prepare.py ...')
        sp.Popen(cmd, shell=True, stdout=sys.stdout, stderr=sys.stderr)


def run_plugins(mode='start'):
    """ (void)
    """
    for plugin in CONFIG['plugins']:

        if plugin == 'sound_cards_prepare.py' or plugin == 'power_amp_control.py':
            continue

        # Some plugin command line can have options, for example:
        #   - librespot.py  pulseaudio
        tmp = plugin.split()
        pname = tmp[0]
        if tmp[1:]:
            options = ' '.join(tmp[1:])
        else:
            options = ''

        cmd = f'{MAINFOLDER}/share/plugins/{pname} {mode} {options}'

        if mode == 'start':
            print(f'(start) starting plugin: {plugin} ...')
            # (i) Notice that we are open to run plugins writen in python, bash, etc...
            sp.Popen(cmd, shell=True, stdout=sys.stdout, stderr=sys.stderr)

        elif mode == 'stop':
            try:
                ans = sp.check_output(cmd, shell=True).decode()
            except Exception as e:
                ans = str(e)
            print(f'(start.py) stopping plugin: {plugin}', ans )

        else:
            pass


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
    sp.Popen(f'python3 {MAINFOLDER}/share/www/scripts/drc2png.py -q', shell=True)


def prepare_log_header():
    """ Writes down the parents processes from which
        start.py has been called, for debugging purposes.
        (void)
    """
    # parent
    ppid = str(os.getppid())
    try:
        ppname = sp.check_output(f'ps -o cmd= {ppid}'.split()).decode().strip()
    except:
        ppname  = '?'

    # grandparent
    try:
        gpid = sp.check_output(f'ps -o ppid= -p {ppid}'.split()).decode().strip()
        if int(ppid) > 1:
            gpname = sp.check_output(f'ps -o cmd= {gpid}'.split()).decode().strip()
        else:
            gpname = '(kernel)'
    except:
        gpid    = '?'
        gpname  = '?'

    # great-grandparent
    try:
        ggpid = sp.check_output(f'ps -o ppid= -p {gpid}'.split()).decode().strip()
        if int(gpid) > 1:
            ggpname = sp.check_output(f'ps -o cmd= {ggpid}'.split()).decode().strip()
        else:
            ggpname = '(kernel)'
    except:
        ggpid   = '?'
        ggpname = '?'

    try:
        timestamp = strftime('%Y-%m-%d', gmtime()) + ' ' + \
                    sp.check_output('uptime').decode().strip()
    except:
        timestamp = ctime()

    with open(logPath, 'w') as f:
        f.write(f'{Fmt.BLUE}')
        f.write(f'(i) \'{logPath}\'\n')
        f.write(f'    {timestamp}\n')
        f.write(f'    great-grandpa pid is: {ggpid} {ggpname}\n')
        f.write(f'    grandpa       pid is: {gpid} {gpname}\n')
        f.write(f'    parent        pid is: {ppid} {ppname}\n')
        f.write(f'    start.py      pid is: {os.getpid()}\n')
        f.write(f'{Fmt.BOLD}')
        f.write(f'    NOTICE THAT MESSAGE LOGGING IS ASYNCHRONOUS\n\n')
        f.write(f'{Fmt.END}')


def usb_dac_watchdog(mode='stop'):

    if mode == 'stop':
        sp.Popen(f'pkill -KILL -f "usb_dac_watchdog.py"', shell=True)

    elif mode=='start':

        if 'usb_dac_watchdog' in CONFIG and CONFIG["usb_dac_watchdog"]==True:
            if not process_is_running('usb_dac_watchdog.py'):
                sp.Popen(f'{MAINFOLDER}/share/plugins/usb_dac_watchdog.py start', shell=True)


def peaudiosys_ctrl_on():
    if not process_is_running('server.py peaudiosys_ctrl'):
        manage_server(mode='start', service='peaudiosys_ctrl')


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

    if mode not in ['all', 'stop', 'server']:
        print(__doc__)
        sys.exit()

    if logFlag:
        logPath = f'{LOG_FOLDER}/start.log'
        print('\n' + '-' * 80)
        print(f'start process logged at \'{logPath}\'')
        print('-' * 80)
        prepare_log_header()
        # We prefer this custom log instead of standard logging module
        flog = open(logPath, 'a')
        sys.stdout = flog
        sys.stderr = flog


    # CHECKING STATE FILE
    check_state_file()

    # Optional REMOTE SOURCES
    REMOTES = get_remote_sources()

    # USB_DAC_WATCHDOG (must not interfere with this)
    usb_dac_watchdog('stop')

    # THE 'peaudiosys_ctrl' SERVER must be always ON
    peaudiosys_ctrl_on()

    # STOPPING ALL THE STAFF
    stop_processes(mode)
    if mode in ('stop', 'shutdown'):
        # RESTORING USB_DAC_WATCHDOG
        usb_dac_watchdog('start')
        print(f'(start) Bye!')
        sys.exit()

    # SPECIAL PLUGINS.
    run_special_plugins()

    # STARTING:
    if mode in ('all'):

        # Starting JACK, EXTERNAL_CARDS and JLOOPS
        jack_stuff = start_jack_stuff()
        if  jack_stuff != 'done':
            print(f'{Fmt.BOLD}(start) Problems starting JACK: {jack_stuff}{Fmt.END}')
            sys.exit()

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

        # Optional REMOTE SOURCES
        if REMOTES:
            start_zita_link()

        # - RESTORE ON_INIT AUDIO settings
        core.init_audio_settings()

        # - PREAMP  -->  MONITORS
        core.connect_monitors()

        # If necessary will prepare DRC GRAPHS for use of the web page
        if CONFIG["web_config"]["show_graphs"]:
            prepare_drc_graphs()

        del core
        print(f'{Fmt.MAGENTA}(start) Closing the temporary \'core\' instance.{Fmt.END}')


    # PLUGINS
    if mode in ('all'):
        run_plugins()

    # RUN THE 'peaudiosys' SERVER
    manage_server(mode='start', service='peaudiosys')
    if not server_is_running(who_asks='start'):
        print(f'{Fmt.BOLD}(start) PANIC: \'peaudiosys\' service is down. Bye.{Fmt.END}')
        sys.exit()

    # OPTIONAL USER MACRO AT START
    if mode in ('all'):
        if 'run_macro' in CONFIG:
            mname = CONFIG["run_macro"]
            if mname:
                print( f'{Fmt.BLUE}(start) triyng macro \'{mname}\'{Fmt.END}' )
                sp.Popen( f'{MAINFOLDER}/macros/{mname}', shell=True )

    # RESTORING USB_DAC_WATCHDOG
    usb_dac_watchdog('start')

    # END
    print(f'{Fmt.BOLD}{Fmt.BLUE}(start) END.{Fmt.END}')

    sys.exit()

