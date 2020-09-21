#!/usr/bin/env python3

# Copyright (c) 2019 Rafael Sánchez
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

import socket
import os
import yaml
import jack
from json import loads as json_loads
from time import sleep

UHOME = os.path.expanduser("~")

# Some nice ANSI formats for printouts
class Fmt:
    """
    # CREDITS: https://github.com/adoxa/ansicon/blob/master/sequences.txt

    0         all attributes off
    1         bold (foreground is intense)
    4         underline (background is intense)
    5         blink (background is intense)
    7         reverse video
    8         concealed (foreground becomes background)
    22        bold off (foreground is not intense)
    24        underline off (background is not intense)
    25        blink off (background is not intense)
    27        normal video
    28        concealed off
    30        foreground black
    31        foreground red
    32        foreground green
    33        foreground yellow
    34        foreground blue
    35        foreground magenta
    36        foreground cyan
    37        foreground white
    38;2;#        foreground based on index (0-255)
    38;5;#;#;#    foreground based on RGB
    39        default foreground (using current intensity)
    40        background black
    41        background red
    42        background green
    43        background yellow
    44        background blue
    45        background magenta
    46        background cyan
    47        background white
    48;2;#        background based on index (0-255)
    48;5;#;#;#    background based on RGB
    49        default background (using current intensity)
    90        foreground bright black
    91        foreground bright red
    92        foreground bright green
    93        foreground bright yellow
    94        foreground bright blue
    95        foreground bright magenta
    96        foreground bright cyan
    97        foreground bright white
    100       background bright black
    101       background bright red
    102       background bright green
    103       background bright yellow
    104       background bright blue
    105       background bright magenta
    106       background bright cyan
    107       background bright white
    """

    BLACK           = '\033[30m'
    RED             = '\033[31m'
    GREEN           = '\033[32m'
    YELLOW          = '\033[33m'
    BLUE            = '\033[34m'
    MAGENTA         = '\033[35m'
    CYAN            = '\033[36m'
    WHITE           = '\033[37m'

    BRIGHTBLACK     = '\033[90m'
    BRIGHTRED       = '\033[91m'
    BRIGHTGREEN     = '\033[92m'
    BRIGHTYELLOW    = '\033[93m'
    BRIGHTBLUE      = '\033[94m'
    BRIGHTMAGENTA   = '\033[95m'
    BRIGHTCYAN      = '\033[96m'
    BRIGHTWHITE     = '\033[97m'

    BOLD        = '\033[1m'
    UNDERLINE   = '\033[4m'
    BLINK       = '\033[5m'
    END         = '\033[0m'


# Sets a peaudiosys parameter as per a given pattern, useful for user macros.
def set_as_pattern(param, pattern, sender='miscel', verbose=False):
    """ Sets a peaudiosys parameter as per a given pattern.
        This applies only for 'xo', 'drc' and 'target'
    """
    result = ''

    if param not in ('xo', 'drc', 'target'):
        return "parameter mus be 'xo', 'drc' or 'target'"

    for setName in json_loads( send_cmd(f'get_{param}_sets') ):

        if pattern in setName:
            result = send_cmd( f'set_{param} {setName}',
                               sender=sender, verbose=verbose )
            break

    return result


# Waiting for jack ports to be available
def wait4ports(pattern):
    """ Waits for jack ports to be available
    """
    JC = jack.Client('miscel', no_start_server=True)
    n = 20  # 10 sec
    while n:
        if len( JC.get_ports( pattern ) ) >= 2:
            break
        n -= 1
        sleep(0.5)
    JC.close()
    if n:
        return True
    else:
        return False


# Send a command to a peaudiosys server
def send_cmd(cmd, sender='', verbose=False, service='peaudiosys'):
    """ send commands to a peaudiosys server
    """
    # (i) start.py will assign 'preamp' port number this way:
    port = {'peaudiosys':   CPORT,
            'preamp':       CPORT + 1,
            'players':      CPORT + 2
            }[service]

    if not sender:
        sender = 'share.miscel'


    ans = None
    with socket.socket() as s:
        try:
            s.connect( (CHOST, port) )
            s.send( cmd.encode() )
            if verbose:
                print( f'{Fmt.BLUE}({sender}) Tx: to   {service}: \'{cmd}\'{Fmt.END}' )
            ans = ''
            while True:
                tmp = s.recv(1024).decode()
                if not tmp:
                    break
                ans += tmp
            if verbose:
                print( f'{Fmt.BLUE}({sender}) Rx: from {service}: \'{ans}\'{Fmt.END}' )
            s.close()
        except:
            if verbose:
                print( f'{Fmt.RED}({sender}) socket error on {CHOST}:{port}{Fmt.END}' )

    return ans


# pe.audio.sys control service addressing
try:
    with open(f'{UHOME}/pe.audio.sys/config.yml', 'r') as f:
        CFG = yaml.safe_load(f)
        CHOST, CPORT = CFG['peaudiosys_address'], CFG['peaudiosys_port']
except:
    print(f'{Fmt.RED}(share.miscel) ERROR reading address/port in \'config.yml\'{Fmt.END}')
    exit()
