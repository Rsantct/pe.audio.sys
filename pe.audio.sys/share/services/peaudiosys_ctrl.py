#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pe.audio.sys'
# 'pe.audio.sys', a PC based personal audio system.

""" An auxiliary service to remotely restart pe.audio.sys,
    and switch on/off the system.

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
logFname = f'{LOG_FOLDER}/peaudiosys_ctrl.log'
if os.path.exists(logFname) and os.path.getsize(logFname) > 10e6:
    print ( f"{Fmt.RED}(peaudiosys_ctrl) log file exceeds ~ 10 MB '{logFname}'{Fmt.END}" )
print ( f"{Fmt.BLUE}(peaudiosys_ctrl) logging commands in '{logFname}'{Fmt.END}" )


def restart_server():
    print('restarting the server ... .. .')
    Popen(f'{UHOME}/bin/peaudiosys_server_restart.sh', shell=True)
    return '(peaudiosys_ctrl) restarting the server'


def restart_peaudiosys():
    print('restarting peaudiosys ... .. .')
    Popen(f'{UHOME}/bin/peaudiosys_restart.sh', shell=True)
    return '(peaudiosys_ctrl) restarting peaudiosys'


# Interface function for this module
def do( cmdphrase):

    result = 'bad command'

    try:
        cmd = cmdphrase.split()[0]
        arg = cmdphrase.split()[-1]
    except:
        cmd = arg = ''
        return result


    if   cmd == 'restart_server':
        result = restart_server()

    elif cmd == 'restart_peaudiosys':
        result = restart_peaudiosys()

    elif cmd == 'amp_switch':
       result = manage_amp_switch( arg )


    logline = f'{strftime("%Y/%m/%d %H:%M:%S")}; {cmd}; {result}'

    with open(logFname, 'a') as FLOG:
            FLOG.write(f'{logline}\n')

    return result
