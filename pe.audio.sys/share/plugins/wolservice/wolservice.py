#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pe.audio.sys'
# 'pe.audio.sys', a PC based personal audio system.

""" A module to Wake On Lan other machines.
    This module is loaded by 'wolserver.py'
"""

import  os
from    subprocess          import  check_output
from    time                import  strftime
import  yaml
import  json

MY_DIR      = os.path.dirname(__file__)
UHOME       = os.path.expanduser("~")
MAINFOLDER  = f'{UHOME}/pe.audio.sys'


# Things to do first
def init():

    global CONFIG, LOGFNAME

    # Command log file
    LOGFNAME = f'{MAINFOLDER}/log/wolservice.log'
    if os.path.exists(LOGFNAME) and os.path.getsize(LOGFNAME) > 10e6:
        print ( f"(wolservice) log file exceeds ~ 10 MB '{LOGFNAME}'" )
    print ( f"(wolservice) logging commands in '{LOGFNAME}'" )

    # Loading configured machines
    CONFIG = {}
    try:
        with open(f'{MY_DIR}/wolservice.cfg', 'r') as f:
            CONFIG = yaml.safe_load(f)
    except:
        print(f'(wolservice) UNABLE to read wolservice.cfg')


# Processing commands
def process_cmd( cmd_phrase ):
    """ It is expected to receive 'wol someMachineID'
    """
    result = 'nothing done'

    chunks = cmd_phrase.split()

    # wol xxxx
    if chunks[0] == 'wol' and chunks[1:]:

        # Restore space separated values
        machineID   = ' '.join(chunks[1:])

        if machineID in CONFIG["machines"]:
            machineMAC  = CONFIG["machines"][ machineID ]
            try:
                result = check_output(f'wakeonlan {machineMAC}', shell=True) \
                        .decode().strip()
            except:
                result = 'ERROR running wakeonlan'

        else:
            result = f'\'{machineID}\' not configured'

    # get_machines
    elif chunks[0] == 'get_machines':
        result = json.dumps( CONFIG["machines"] )

    # unknown command
    else:
        result = f'unknown command: \'{cmd_phrase}\''

    return result


# Interface function to plug this on server.py
def do( cmd_phrase ):

    result = 'nothing done'
    cmd_phrase = cmd_phrase.strip()

    if cmd_phrase:

        # cmd_phrase log
        with open(LOGFNAME, 'a') as FLOG:
            FLOG.write(f'{strftime("%Y/%m/%d %H:%M:%S")}; {cmd_phrase}; ')

        result = process_cmd(cmd_phrase)

        if type(result) != str:
            result = json.dumps(result)

        # result log
        with open(LOGFNAME, 'a') as FLOG:
            FLOG.write(f'{result}\n')

    return result


# Things to do first
init()
