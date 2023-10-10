#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pe.audio.sys'
# 'pe.audio.sys', a PC based personal audio system.

""" Auxiliary service to restart pe.audio.sys remotely
    This module is loaded by 'server.py'
"""
from    subprocess  import Popen
from    time        import  strftime
import  os
import  sys

UHOME = os.path.expanduser("~")
sys.path.append(f'{UHOME}/pe.audio.sys/share/miscel')

from    miscel      import  LOG_FOLDER, manage_amp_switch
from    fmt         import  Fmt


# COMMAND LOG FILE
logFname = f'{LOG_FOLDER}/restart_cmd.log'
if os.path.exists(logFname) and os.path.getsize(logFname) > 10e6:
    print ( f"{Fmt.RED}(restart) log file exceeds ~ 10 MB '{logFname}'{Fmt.END}" )
print ( f"{Fmt.BLUE}(restart) logging commands in '{logFname}'{Fmt.END}" )


def _server_restart():
    print('restarting the server ... .. .')
    Popen(f'{UHOME}/bin/peaudiosys_server_restart.sh', shell=True)
    return '(restart) restarting the server'


def _peaudiosys_restart():
    print('restarting peaudiosys ... .. .')
    Popen(f'{UHOME}/bin/peaudiosys_restart.sh', shell=True)
    return '(restart) restarting peaudiosys'


def _amplifier_restart():
    # This is an alternative when 'peaudiosys' service is down
    print('restarting amplifier ... .. .')
    manage_amp_switch('on')
    return '(restart) restarting amplifier'


# Interface function for this module
def do( cmd ):

    cmd = cmd.strip()

    result = f'(restart) bad command \'{cmd}\''

    cmdmap = {  'server_restart':       _server_restart,
                'peaudiosys_restart':   _peaudiosys_restart,
                'amplifier_restart':   _amplifier_restart
             }


    if cmd in cmdmap:

        result = cmdmap[ cmd ]()

        logline = f'{strftime("%Y/%m/%d %H:%M:%S")}; {cmd}; {result}'

        with open(logFname, 'a') as FLOG:
                FLOG.write(f'{logline}\n')

    return result
