#!/usr/bin/env python3

# Copyright (c) 2022 Rafael Sánchez
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

""" Auxiliary service to restart pe.audio.sys remotely
    This module is loaded by 'server.py'
"""
from    subprocess  import Popen
from    time        import  strftime
import  os
import  sys

UHOME = os.path.expanduser("~")
sys.path.append(f'{UHOME}/pe.audio.sys/share/miscel')

from    config      import  LOG_FOLDER
from    fmt         import  Fmt


# COMMAND LOG FILE
logFname = f'{LOG_FOLDER}/restart_cmd.log'
if os.path.exists(logFname) and os.path.getsize(logFname) > 10e6:
    print ( f"{Fmt.RED}(restart) log file exceeds ~ 10 MB '{logFname}'{Fmt.END}" )
print ( f"{Fmt.BLUE}(restart) logging commands in '{logFname}'{Fmt.END}" )


# Interface function for this module
def do( cmd ):

    def server_restart():
        print('restarting the server ... .. .')
        Popen(f'{UHOME}/bin/peaudiosys_server_restart.sh', shell=True)
        return '(restart) restarting the server'


    def peaudiosys_restart():
        print('restarting peaudiosys ... .. .')
        Popen(f'{UHOME}/bin/peaudiosys_restart.sh', shell=True)
        return '(restart) restarting peaudiosys'


    cmd = cmd.strip()
    result = f'(restart) bad command \'{cmd}\''

    cmdmap = {  'server_restart':       server_restart,
                'peaudiosys_restart':   peaudiosys_restart
              }


    if cmd in cmdmap:

        result = cmdmap[ cmd ]()

        logline = f'{strftime("%Y/%m/%d %H:%M:%S")}; {cmd}; {result}'

        with open(logFname, 'a') as FLOG:
                FLOG.write(f'{logline}\n')

    return result
