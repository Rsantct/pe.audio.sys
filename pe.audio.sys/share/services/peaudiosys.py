#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pe.audio.sys'
# 'pe.audio.sys', a PC based personal audio system.

""" MAIN SERVICE MODULE that controls the whole system:
        preamp, players and auxiliary functions.
    This module is loaded by 'server.py'
"""

import  json
from    time                import  strftime
import  os
import  sys

UHOME = os.path.expanduser("~")
sys.path.append(f'{UHOME}/pe.audio.sys/share')
sys.path.append(f'{UHOME}/pe.audio.sys/share/miscel')

from    services    import  preamp
from    services    import  players
from    services    import  aux

from    config      import  LOG_FOLDER
from    fmt         import  Fmt


# COMMAND LOG FILE
logFname = f'{LOG_FOLDER}/peaudiosys_cmd.log'
if os.path.exists(logFname) and os.path.getsize(logFname) > 10e6:
    print ( f"{Fmt.RED}(peaudiosys) log file exceeds ~ 10 MB '{logFname}'{Fmt.END}" )
print ( f"{Fmt.BLUE}(peaudiosys) logging commands in '{logFname}'{Fmt.END}" )


# Interface function for this module
def do( cmd_phrase ):

    def read_cmd_phrase(cmd_phrase):

        # (i) command phrase SYNTAX must start with an appropriate prefix:
        #           preamp  command  arg1 ...
        #           players command  arg1 ...
        #           aux     command  arg1 ...
        #     The 'preamp' prefix can be omited

        pfx, cmd, argstring = '', '', ''

        # This is to avoid empty values when there are more
        # than on space as delimiter inside the cmd_phrase:
        chunks = [x for x in cmd_phrase.split(' ') if x]

        # If not prefix, will treat as a preamp command kind of
        if not chunks[0] in ('preamp', 'player', 'aux'):
            chunks.insert(0, 'preamp')
        pfx = chunks[0]

        if chunks[1:]:
            cmd = chunks[1]
        if chunks[2:]:
            # <argstring> can be compound
            argstring = ' '.join( chunks[2:] )

        return pfx, cmd, argstring


    result = f'(peaudiosys) nothing done'
    cmd_phrase = cmd_phrase.strip()

    if cmd_phrase:

        pfx, cmd, args = read_cmd_phrase( cmd_phrase )
        #print('pfx:', pfx, '| cmd:', cmd, '| args:', args) # DEBUG

        result = {  'preamp':   preamp.do,
                    'player':   players.do,
                    'aux':      aux.do
                  }[ pfx ]( cmd, args )

        if type(result) != str:
            result = json.dumps(result)

        # Avoids logging non-relevant commands
        if  ('state'        not in cmd)  and \
            ('state'        not in args) and \
            ('get_'         not in cmd)  and \
            ('warning'      not in cmd)  and \
            ('info'         not in cmd):

            logline = f'{strftime("%Y/%m/%d %H:%M:%S")}; {cmd_phrase}; {result}'

            with open(logFname, 'a') as FLOG:
                    FLOG.write(f'{logline}\n')

    return result
