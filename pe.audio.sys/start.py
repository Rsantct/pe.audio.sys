#!/usr/bin/env python3

# Copyright (c) 2019 Rafael Sánchez
# This file is part of 'pe.audio.sys', a PC based personal audio system.

# This is based on 'pre.di.c,' a preamp and digital crossover
# https://github.com/rripio/pre.di.c
# Copyright (C) 2018 Roberto Ripio
# 'pre.di.c' is based on 'FIRtro', a preamp and digital crossover
# https://github.com/AudioHumLab/FIRtro
# Copyright (c) 2006-2011 Roberto Ripio
# Copyright (c) 2011-2016 Alberto Miguélez
# Copyright (c) 2016-2018 Rafael Sánchez
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


"""
    usage:  start.py <mode> [ --log ]

    mode:
        'all'      :    restart all
        'stop'     :    stop all
        'server'   :    restart tcp server
        'scripts'  :    restart user scripts

    --log   messages redirected to 'pe.audio.sys/start.log'

"""

import os
import sys
UHOME = os.path.expanduser("~")
sys.path.append(f'{UHOME}/pe.audio.sys')

from    share.miscel import *
import  subprocess as sp
from    time import sleep, time, ctime
import  yaml
import  jack

ME              = __file__.split('/')[-1]


def prepare_extra_cards(channels=2):
    """ This launch resamplers that connects extra sound cards into Jack
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

        print(f'({ME}) loading resampled extra card: {card}')
        #print(cmd) # DEBUG
        sp.Popen(cmd.split(), stdout=sys.stdout, stderr=sys.stderr)


def run_jloops():
    """ Jack loops launcher
    """
    # Jack loops launcher external daemon
    sp.Popen(f'{MAINFOLDER}/share/services/preamp_mod/jloops_daemon.py', shell=True)


def check_jloops():
    """ Jack loops checking
        returns False if checking fails, otherwise returns True
    """
    # The configured loops
    cfg_loops = []
    loop_names = ['pre_in_loop']
    for source in CONFIG['sources']:
        pname = CONFIG['sources'][source]['capture_port']
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
    jcli = jack.Client(name='loop_check', no_start_server=True)
    tries = 10
    while tries:
        # The running ones
        run_loops = [p.name for p in jcli.get_ports('loop')]
        if sorted(cfg_loops) == sorted(run_loops):
            break
        sleep(1)
        tries -= 1
    jcli.close()
    if tries:
        print(f'{Fmt.BLUE}({ME}) JACK LOOPS STARTED{Fmt.END}')
        return True
    else:
        print(f'{Fmt.BOLD}({ME}) JACK LOOPS FAILED{Fmt.END}')
        return False


def start_jack_stuff():
    """ runs jackd with configured options, jack loops and extrernal cards ports
    """
    warnings = ''

    jack_backend_options = CONFIG["jack_backend_options"] \
                    .replace('$autoCard', CONFIG["system_card"]) \
                    .replace('$autoFS', str(bf_get_sample_rate()))

    cmdlist = ['jackd']

    if logFlag:
        cmdlist += ['--silent']

    cmdlist += f'{CONFIG["jack_options"]}'.split() + \
               f'{jack_backend_options}'.split()

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
            print(f'{Fmt.BOLD}{Fmt.BLUE}({ME}) JACKD STARTED{Fmt.END}')
            break
        print(f'({ME}) waiting for jackd ' + '.' * tries)
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


def manage_server( mode='', address=SRV_HOST, port=SRV_PORT,
                  todevnull=False):

    if mode == 'stop':
        # Stop
        print(f'{Fmt.RED}({ME}) stopping \'server.py peaudiosys\'{Fmt.END}')
        sp.Popen( f'pkill -KILL -f "server.py peaudiosys" \
                   >/dev/null 2>&1', shell=True, stdout=sys.stdout,
                                                 stderr=sys.stderr)

    elif mode == 'start':
        # Start
        print(f'{Fmt.BLUE}({ME}) starting \'server.py peaudiosys\'{Fmt.END}')
        cmd = f'python3 {MAINFOLDER}/share/server.py peaudiosys' \
                                                    f' {address} {port}'
        if todevnull:
            with open('/dev/null', 'w') as fnull:
                sp.Popen( cmd, shell=True, stdout=fnull,
                                           stderr=fnull )
        else:
            sp.Popen( cmd, shell=True, stdout=sys.stdout,
                                       stderr=sys.stderr )

    else:
        raise Exception(f'usage: manage_server(start|stop)')


def stop_processes(mode):

    # Killing any previous instance of start.py
    kill_bill( os.getpid() )

    # Stop scripts
    if mode in ('all', 'stop', 'scripts'):
        run_scripts(mode='stop')

    if mode in ('all', 'stop'):
        # Stop Brutefir
        print(f'({ME}) STOPPING BRUTEFIR')
        sp.Popen('pkill -KILL -f brutefir >/dev/null 2>&1', shell=True)

        # Stop Jack Loops Daemon
        print(f'({ME}) STOPPING JACK LOOPS')
        sp.Popen('pkill -KILL -f jloops_daemon.py >/dev/null 2>&1', shell=True)

        # Stop Jack
        print(f'({ME}) STOPPING JACKD')
        sp.Popen('pkill -KILL -f jackd >/dev/null 2>&1', shell=True)

    if mode in ('all', 'stop', 'server'):
        # Stops the server:
        manage_server(mode='stop')

    sleep(1)


def run_scripts(mode='start'):
    for script in CONFIG['scripts']:
        #(i) Some elements on the scripts list from config.yml can be a dict,
        #    e.g the ecasound_peq, so we need to extract the script name.
        if type(script) == dict:
            script = list(script.keys())[0]
        print(f'({ME}) will {mode} the script \'{script}\' ...')
        sp.Popen(f'{MAINFOLDER}/share/scripts/{script} {mode}', shell=True,
                                  stdout=sys.stdout, stderr=sys.stderr)
    if mode == 'stop':
        sleep(.5)  # this is necessary because of asyncronous stopping


def check_state_file():
    """ a sudden power break out can damage .state.yml  :-/
    """
    state_file      = f'{MAINFOLDER}/.state.yml'
    state_log_file  = f'{MAINFOLDER}/.state.log'

    def recover_state(reason='damaged'):
        sp.Popen(f'cp {state_file}.BAK {state_file}'.split())
        print(f'({ME}) ERROR \'state.yml\' was {reason}, ' +
                'it has been restored from \'.state.yml.BAK\'')
        now = ctime(time())
        with open(state_log_file, 'a') as f2:
            f2.write(f'{now}: \'state.yml\' was {reason} and restored.\n')

    try:
        with open(state_file, 'r') as f:
            state = f.read()

            # if the file is ok, lets backup it
            if 'xo_set:' in state:
                sp.Popen(f'cp {state_file} {state_file}.BAK'.split())
                print(f'({ME}) (i) .state.yml copied to .state.yml.BAK')

            # if it is damaged, lets recover from backup, and log to .state.log
            else:
                recover_state(reason='damaged')
    except:
                recover_state(reason='missed')


def prepare_drc_graphs():

    # find loudspeaker's drc_sets
    pcm_files  = os.listdir(LSPK_FOLDER)
    drc_coeffs  = [ x.replace('.pcm', '') for x in pcm_files
                                          if x[:4] == 'drc.' ]
    drc_sets = []
    for drc_coeff in drc_coeffs:
        drcSetName = drc_coeff[6:]
        if drcSetName not in drc_sets:
            drc_sets.append(drcSetName)
    drc_sets += ['none']

    # find existing drc graph images
    img_folder = f'{MAINFOLDER}/share/www/images'
    png_files = [ x for x in os.listdir(img_folder) if x[:4] == 'drc_' ]
    png_sets =  [ x[4:-4] for x in png_files ]

    # If graphs exist, skip generate them
    if sorted(drc_sets) == sorted(png_sets):
        print(f'({ME}) found drc graphs in web/images folders')
    else:
        print(f'({ME}) processing drc sets to web/images in background')
        sp.Popen([ 'python3', f'{MAINFOLDER}/share/www/scripts/drc2png.py', '-q' ])


def update_bfeq_graph():
    print(f'({ME}) processing Brutefir EQ graph to web/images in background')
    sp.Popen(['python3', f'{MAINFOLDER}/share/services/preamp_mod/bfeq2png.py'])


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
        print(f'start process logged at \'{MAINFOLDER}/start.log\'')
        print('-' * 80)
        flog = open(f'{MAINFOLDER}/start.log', 'w')
        original_stdout = sys.stdout
        original_stderr = sys.stderr
        sys.stdout = flog
        sys.stderr = flog

    # Lets check STATE FILE '.state.yml'
    check_state_file()

    # STOPPING:
    stop_processes(mode)

    if mode in ('stop', 'shutdown'):
        print(f'({ME}) Bye!')
        sys.exit()

    # STARTING:
    if mode in ('all'):
        # If necessary will prepare DRC GRAPHS for the web page
        if CONFIG["web_config"]["show_graphs"]:
            prepare_drc_graphs()

        # Starting JACK, EXTERNAL_CARDS and JLOOPS
        jack_stuff = start_jack_stuff()
        if  jack_stuff != 'done':
            print(f'{Fmt.BOLD}({ME}) Problems starting JACK: {jack_stuff}{Fmt.END}')
            sys.exit()

    if mode in ('all', 'scripts'):
        # Running USER SCRIPTS
        run_scripts()

    if mode in ('all'):

        # INIT AUDIO by importing 'core' temporally (needs JACK to be running)
        import share.services.preamp_mod.core as core
        print(f'{Fmt.MAGENTA}({ME}) Managing a temporary \'core\' instance.{Fmt.END}')

        # - BRUTEFIR
        bfstart = core.restart_and_reconnect_brutefir( ['pre_in_loop:output_1',
                                                        'pre_in_loop:output_2'] )
        if bfstart == 'done':
            print(f'{Fmt.BOLD}{Fmt.BLUE}({ME}) BRUTEFIR STARTED.{Fmt.END}')
        else:
            print(f'({Fmt.BOLD}{ME}) Problems starting BRUTEFIR: {bfstart}')
            sys.exit()

        # - RESTORE ON_INIT AUDIO settings
        core.init_audio_settings()

        # - PREAMP  -->  MONITORS
        core.connect_monitors()

        del core
        print(f'{Fmt.MAGENTA}({ME}) Closing the temporary \'core\' instance.{Fmt.END}')


    if mode in ('all', 'server'):
        # Will update Brutefir EQ graph for the web page
        if CONFIG["web_config"]["show_graphs"]:
            update_bfeq_graph()

    # The 'peaudiosys' SERVER always runs, so that we can do basic operation
    manage_server(mode='start')

    if mode in ('all'):
        # OPTIONAL USER MACRO
        if 'run_macro' in CONFIG:
            # wait a bit for server.py to be ready before running any macro
            sleep(1)
            mname = CONFIG["run_macro"]
            if mname:
                print( f'{Fmt.BLUE}({ME}) triyng macro \'{mname}\'{Fmt.END}' )
                sp.Popen( f'{MAINFOLDER}/macros/{mname}'.split() )

    # END
