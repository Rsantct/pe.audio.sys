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
        'services' :    restart tcp services
        'scripts'  :    restart user scripts

    --log   messages redirected to 'pe.audio.sys/start.log'

"""

import os
import sys
import subprocess as sp
from time import sleep
import yaml
import jack

ME    = __file__.split('/')[-1]
UHOME = os.path.expanduser("~")
MAINFOLDER  = f'{UHOME}/pe.audio.sys'

with open(f'{MAINFOLDER}/config.yml', 'r') as f:
    CONFIG = yaml.safe_load(f)
LOUDSPEAKER     = CONFIG['loudspeaker']
LSPK_FOLDER     = f'{MAINFOLDER}/loudspeakers/{LOUDSPEAKER}'
TCP_BASE_PORT   = CONFIG['peaudiosys_port']


def get_Bfir_sample_rate():
    """ retrieve loudspeaker's filters FS from its Brutefir configuration
    """
    FS = 0

    for fname in (f'{LSPK_FOLDER}/brutefir_config',
                  f'{UHOME}/.brutefir_defaults'):
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

    if 'defaults' in fname:
        print(f'({ME}) *** using .brutefir_defaults SAMPLE RATE ***')

    return FS


def jack_is_running():
    try:
        sp.check_output('jack_lsp >/dev/null 2>&1'.split())
        return True
    except sp.CalledProcessError:
        return False


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
    sp.Popen(f'{MAINFOLDER}/share/services/preamp_mod/jloops_daemon.py')


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
        print(f'({ME}) JACK LOOPS STARTED')
        return True
    else:
        print(f'({ME}) JACK LOOPS FAILED')
        return False


def start_jackd():
    """ runs jack with configured options
    """
    jack_backend_options = CONFIG["jack_backend_options"] \
                    .replace('$autoCard', CONFIG["system_card"]) \
                    .replace('$autoFS', str(get_Bfir_sample_rate()))

    cmdlist = ['jackd'] + f'{CONFIG["jack_options"]}'.split() + \
              f'{jack_backend_options}'.split()

    #print(' '.join(cmdlist)) ; sys.exit() # DEBUG

    if 'pulseaudio' in sp.check_output("pgrep -fl pulseaudio",
                                       shell=True).decode():
        cmdlist = ['pasuspender', '--'] + cmdlist

    # Launch jackd process
    sp.Popen(cmdlist, stdout=sys.stdout, stderr=sys.stderr)
    sleep(1)

    # Will check if JACK ports are available
    tries = 10
    while tries:
        if jack_is_running():
            print(f'({ME}) JACKD STARTED')
            break
        print(f'({ME}) waiting for jackd ' + '.' * tries)
        sleep(.5)
        tries -= 1

    if tries:

        # ADDIGN EXTRA SOUND CARDS RESAMPLED INTO JACK ('external_cards:')
        prepare_extra_cards()

        # Emerging jack_loops (external daemon)
        run_jloops()
        if check_jloops():
            return True
        else:
            return False
    else:
        # JACK FAILED
        return False


def manage_service(service, address='localhost', port=TCP_BASE_PORT,
                    mode='restart', todevnull=False):

    if mode in ('stop', 'restart'):
        # Stop
        print(f'({ME}) stopping SERVICE: \'{service}\'')
        sp.Popen(f'pkill -KILL -f "server.py {service}" \
                   >/dev/null 2>&1', shell=True, stdout=sys.stdout,
                                                 stderr=sys.stderr)

    sleep(.25)  # this is necessary because of asyncronous stopping

    if mode in ('stop'):
        return

    if mode in ('start', 'restart'):
        # Start
        print(f'({ME}) starting SERVICE: \'{service}\'')
        cmd = f'python3 {MAINFOLDER}/share/services/server.py {service}' \
                                                    f' {address} {port}'
        if todevnull:
            with open('/dev/null', 'w') as fnull:
                sp.Popen(cmd, shell=True, stdout=fnull, stderr=fnull)
        else:
            sp.Popen(cmd, shell=True, stdout=sys.stdout, stderr=sys.stderr)


def stop_processes(mode):

    # Killing any previous instance of start.py
    kill_bill()

    # Stop scripts
    if mode in ('all', 'stop', 'scripts'):
        run_scripts(mode='stop')

    # Stop services:
    if mode in ('all', 'stop', 'services'):
        manage_service('preamp',  TCP_BASE_PORT+1, mode='stop')
        manage_service('players', TCP_BASE_PORT+2, mode='stop')

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


def kill_bill():
    """ killing any previous instance of this, becasue
        some residual try can be alive accidentaly.
    """

    # List processes like this one
    processString = f'pe.audio.sys/start.py all'
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
    own_pid = str(os.getpid())
    for rawpid in rawpids:
        if rawpid.split()[1] == own_pid:
            rawpids.remove(rawpid)

    # Just display the processes to be killed, if any.
    print('-' * 21 + f' ({ME}) killing running before me ' + '-' * 21)
    for rawpid in rawpids:
        print(rawpid)
    print('-' * 80)

    if not rawpids:
        return

    # Extracting just the 'pid' at 2ndfield [1]:
    pids = [ x.split()[1] for x in rawpids ]

    # Killing the remaining pids, if any:
    for pid in pids:
        print(f'({ME}) killing old \'start.py\' processes:', pid)
        sp.Popen(f'kill -KILL {pid}'.split())
        sleep(.1)
    sleep(.5)


def check_state_file():
    state_file = f'{MAINFOLDER}/.state.yml'
    with open(state_file, 'r') as f:
        state = f.read()
        # if the file is ok, lets backup it
        if 'xo_set:' in state:
            sp.Popen(f'cp {state_file} {state_file}.BAK'.split())
            print(f'({ME}) (i) .state.yml copied to .state.yml.BAK')
        # if it is damaged:
        else:
            print(f'({ME}) ERROR \'state.yml\' is damaged, ' +
                    'you can restore it from \'.state.yml.BAK\'')
            sys.exit()


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
    if mode not in ['all', 'stop', 'services', 'scripts']:
        print(__doc__)
        sys.exit()
    if logFlag:
        flog = open(f'{MAINFOLDER}/start.log', 'w')
        original_stdout = sys.stdout
        original_stderr = sys.stderr
        sys.stdout = flog
        sys.stderr = flog

    # Lets backup .state.yml to help us if it get damaged.
    check_state_file()

    # STOPPING
    stop_processes(mode)

    # The 'peaudiosys' service always runs, so that we can do basic operation
    manage_service('peaudiosys', address=CONFIG['peaudiosys_address'],
                    mode='restart', todevnull=True)

    if mode in ('stop', 'shutdown'):
        sys.exit()

    if mode in ('all'):
        # If necessary will prepare drc graphs for the web page
        if CONFIG["web_config"]["show_graphs"]:
            prepare_drc_graphs()

        # START JACK
        if not start_jackd():
            print(f'({ME}) Problems starting JACK ')
            sys.exit()

        # (i) Importing core.py needs JACK to be running
        import share.services.preamp_mod.core as core

    if mode in ('all', 'scripts'):
        # Running USER SCRIPTS
        run_scripts()

    if mode in ('all'):
        # BRUTEFIR
        core.restart_and_reconnect_brutefir( ['pre_in_loop:output_1',
                                              'pre_in_loop:output_2'] )
        # RESTORE settings
        core.init_audio_settings()
        # PREAMP  --> MONITORS
        core.connect_monitors()
        # RESTORE source
        core.init_source()

    if mode in ('all', 'services'):
        # Will update Brutefir EQ graph for the web page
        if CONFIG["web_config"]["show_graphs"]:
            update_bfeq_graph()

        # SERVICES (TCP SERVERS):
        manage_service('preamp',  port=(TCP_BASE_PORT + 1), mode='start')
        manage_service('players', port=(TCP_BASE_PORT + 2), mode='start')


    # END
    if logFlag:
        sys.stdout = original_stdout
        sys.stderr = original_stderr
        print(f'start process logged at \'{MAINFOLDER}/start.log\'')
