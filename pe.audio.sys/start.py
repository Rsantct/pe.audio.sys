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
    options:
        'all ':                 restart all
        'stop' or 'shutdown':   stop all
        'core':                 restart core except Jackd
"""

import os
import sys
import subprocess as sp
from time import sleep
import yaml

UHOME = os.path.expanduser("~")
with open( f'{UHOME}/pe.audio.sys/config.yml' ) as f:
    CONFIG = yaml.load(f)
LOUDSPEAKER     = CONFIG['loudspeaker']
LSPK_FOLDER     = f'{UHOME}/pe.audio.sys/loudspeakers/{LOUDSPEAKER}'

def is_jack_running():
    try:
        sp.check_output( 'jack_lsp' )
        return True
    except:
        return False

def start_jackd():

    jack_backend_options = CONFIG["jack_backend_options"].replace(
                            'system_card', CONFIG["system_card"] )

    tmplist = ['jackd'] + f'{CONFIG["jack_options"]}'.split() + \
              f'{jack_backend_options}'.split() + \
              '>/dev/null 2>&1'.split()
    #print( ' '.join(tmplist) ) ; sys.exit() # DEBUG
    
    if 'pulseaudio' in sp.check_output("pgrep -fl pulseaudio", shell=True).decode():
        tmplist = ['pasuspender', '--'] + tmplist

    sp.Popen( tmplist )
    sleep(1)

    # will check if JACK ports are available
    c = 6
    while c:
        print( '(start.py) waiting for jackd ' + '.'*c )
        try:
            sp.check_output( 'jack_lsp >/dev/null 2>&1'.split() )
            sleep(1)
            print( '(start.py) JACKD STARTED' )
            return True
        except:
            c -= 1
            sleep(.5)
    return False
            
def start_brutefir():
    os.chdir( LSPK_FOLDER )
    #os.system('pwd') # debug
    sp.Popen( 'brutefir brutefir_config'.split() )
    os.chdir ( UHOME )
    print( '(start.py) STARTING BRUTEFIR' )
    sleep(1) # wait a while for Brutefir to start ...

def get_services():
    services = []
    for item in CONFIG["services_addressing"]:
        service = item.split('_')[0]
        if not service in services:
            services.append(service)
    return services

def start_service( service ):
    try:
        address = CONFIG["services_addressing"][f"{service}_address"]
        port =    CONFIG["services_addressing"][f"{service}_port"]
        # use shell=True to release python process if you want to
        # restart any service in runtime.
        sp.Popen( f'python3 {UHOME}/pe.audio.sys/share/server.py {service}'
                  f' {address} {port}', shell=True)
        print( f'(start.py) starting SERVICE: \'{service}\'' )

    except:
        print( f'(start.py) ERROR starting service: \'{service}\'' )

def stop_processes(jackd=False):

    if run_level == 'all':
        run_scripts( mode = 'stop' )

    print( '(start.py) STOPPING CORE' )
    # Any service:
    sp.Popen( 'pkill -KILL -f "pe.audio.sys/share/server.py" \
               >/dev/null 2>&1', shell=True )
    # Brutefir
    sp.Popen( 'pkill -KILL -f brutefir >/dev/null 2>&1', shell=True )

    # Jack
    if jackd:
        print( '(start.py) STOPPING JACKD' )
        sp.Popen( 'pkill -KILL -f jackd >/dev/null 2>&1', shell=True )

    sleep(1)

def prepare_extra_cards( channels = 2 ):

    if not CONFIG['external_cards']:
        return

    for card, params in CONFIG['external_cards'].items():
        jack_name = card
        alsacard =  params['alsacard']
        resampler = params['resampler']
        quality =   str( params['resamplingQ'] )
        try:
            misc = params['misc_params']
        except:
            misc = ''
        
        cmd = f'{resampler} -d{alsacard} -j{jack_name} -c{channels} -q{quality} {misc}'
        if 'zita' in resampler:
            cmd = cmd.replace("-q", "-Q")

        print( f'(start.py) loading resampled extra card: {card}' )
        #print(cmd) # DEBUG
        sp.Popen( cmd.split() ) 

def run_scripts(mode='start'):
    for script in CONFIG['scripts']:
        #(i) Some elements on the scripts list from config.yml can be a dict, 
        #    e.g the ecasound_peq, so we need to extract the script name.
        if type(script) == dict:
            script = list(script.keys())[0]
        print( f'(start.py) will {mode} the script \'{script}\' ...' )
        sp.Popen( f'{UHOME}/pe.audio.sys/share/scripts/{script} {mode}', shell=True)
    if mode == 'stop':
        sleep(.5) # this is necessary because of asyncronous stopping

def kill_bill():
    """ killing any previous instance of this, becasue
        some residual try can be alive accidentaly.
    """

    # List processes like this one
    processString = f'python3 {UHOME}/pe.audio.sys/start.py'
    rawpids = []
    cmd = ( f'ps -eo etimes,pid,cmd' +
            f' | grep "{processString}"' +
            f' | grep -v grep'  )
    try:
        rawpids = sp.check_output( cmd, shell=True ).decode().split('\n')
    except:
        pass
    # Discard blanks and strip spaces:
    rawpids = [ x.strip().replace('\n','')  for x in rawpids if x]
    # A 'rawpid' element has 3 fields 1st:etimes 2nd:pid 2th:comand_string
    # Sorting by 1st_field:etimes (elapsed time seconds, see 'man ps'):
    rawpids.sort( key=lambda x: int(x.split()[0]) )
    # Now we have the 'rawpids' ordered the oldest the last.
    #print(rawpids) #debug

    # Discard the last one because it is **the own pid**
    if rawpids:
        rawpids.pop()

    # Extracting just the 'pid' at 2ndfield [1]:
    pids = [ x.split()[1] for x in rawpids ]

    # Killing the remaining pids, if any:
    for pid in pids:
        sp.Popen( f'kill -KILL {pid}'.split() )
        sleep(.1)

def check_state_file():
    
    STATEFILE = f'{UHOME}/pe.audio.sys/.state.yml' 
    with open( STATEFILE, 'r') as f:
        state = f.read()
        # if th file is ok
        if 'xo_set:' in state:
            sp.Popen( f'cp {STATEFILE} {STATEFILE}.BAK'.split() )
            print( f'(start.py) (i) .state.yml copied to .state.yml.BAK' )
        # if it is damaged:
        else:
            print( f'(start.py) ERROR \'state.yml\' is damaged, ' + 
                    'you can restore it from \'.state.yml.BAK\'' )
            sys.exit()

if __name__ == "__main__":
    
    # Lets backup .state.yml to help us if it get damaged.
    check_state_file()
    
    # KILLING ANY PREVIOUS INSTANCE OF THIS
    kill_bill() 

    # READING OPTIONS FROM COMMAND LINE
    run_level = ''
    if sys.argv[1:]:

        if sys.argv[1] in ['stop', 'shutdown']:
            run_level = 'all'
            stop_processes(jackd=True)
            sys.exit()

        elif sys.argv[1] == 'core':
            run_level = 'core'
            stop_processes(jackd=False)
            
        elif sys.argv[1] == 'all':
            run_level = 'all'
            stop_processes(jackd=True)
            # Trying to start JACKD
            if not start_jackd():
                print('(start.py) Problems starting JACK ')
                sys.exit()
            
        else:
            print(__doc__)
            sys.exit()

    else:
        print(__doc__)
        sys.exit()

    if is_jack_running():
       
        # (i) Importing core.py needs JACK to be running
        from share.core import  jack_loops_prepare,     \
                                init_audio_settings,    \
                                init_source,            \
                                jack_connect_bypattern, \
                                save_yaml, STATE_PATH

        # BRUTEFIR
        start_brutefir()

        # ADDIGN EXTRA SOUND CARDS RESAMPLED INTO JACK
        prepare_extra_cards()

        # PREAMP INPUTS (JACK LOOPS)
        if run_level == 'all':
            jack_loops_prepare()
            sleep(1) # this is necessary, or checking for ports to be activated

        # RESTORE: audio settings
        state = init_audio_settings()
        save_yaml(state, STATE_PATH)
        
        # RESTORE source as set under config.yml
        state = init_source()
        save_yaml(state, STATE_PATH)

        # THE TCP SERVERS:
        # (i) - The system control service 'pasysctl.py' needs jack to be running.
        #     - From now on, 'pasysctl.py' MUST BE the ONLY OWNER of STATE_PATH.
        for service in get_services():
            start_service(service)

        # Running USER SCRIPTS
        run_scripts()

        # (i) Leaving this for last: it depends on Brutefir ports to become active
        # pre_in    -->   brutefir
        jack_connect_bypattern('pre_in',   'brutefir', wait=60)
        

    else:
        print( '(start.py) JACK not detected')
