#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pe.audio.sys'
# 'pe.audio.sys', a PC based personal audio system.

"""
    Command line tool for the pe.audio.sys Ecasound PEQ plugin.

    Usage:             peq_control.py  cmd  arg1  arg2 ....

    Available commands and arguments:

    - PEQ_dump2peq                  Prints running parametric filters,
                                    also dumps them to LSPK_FOLDER/eca_dump.peq

    - PEQ_dump2ecs                  Prints running .ecs structure
                                    also dumps it to LSPK_FOLDER/eca_dump.ecs

    - PEQ_load_peq  peqID           Loads a LSPK_FOLDER/peqID.peq file
                                    of parameters in Ecasound

    - PEQ_bypass  on|off|toggle     Bypass the EQ

    - PEQ_gain  XX                  Sets EQ gain

    - ECA_cmd  cmd1 ... cmdN        Native ecasound-iam commands.
                                    (See man ecasound-iam)


    NOTE: .peq files are HUMAN READABLE PEQ settings,
          .ecs files are standard Ecasound chainsetup files.

"""

import  sys
import  os

UHOME       = os.path.expanduser("~")
MAINFOLDER  = f'{UHOME}/pe.audio.sys'
sys.path.append(f'{MAINFOLDER}/share/miscel')

import  peq_mod as pm
from    miscel  import send_cmd

if __name__ == '__main__':

    # is ecasound listening?
    if not pm.ecanet(''):
        print("(!) no answer from Ecasound server")
        sys.exit()

    # we can pass more than one command from command line to ecasound
    if sys.argv[1:]:

        cmd  = sys.argv[1]
        args = sys.argv[2:]

        if   cmd == "ECA_cmd":
            for ecaCmd in args:
                print( pm.ecanet(ecaCmd) )

        elif cmd == "PEQ_dump2peq":
            pm.eca_dump2peq(verbose=True)

        elif cmd == "PEQ_dump2ecs":
            pm.eca_dump2ecs(verbose=True)

        elif cmd == "PEQ_load_peq" and args:
            peqfname = args[0]
            if not peqfname.endswith('.peq'):
                peqfname += '.peq'
            peqpath = f'{pm.LSPK_FOLDER}/{peqfname}'
            # aux will update .aux_info status file
            res = send_cmd( f'aux peq_load {peqpath}' )
            print(res)

        elif cmd == "PEQ_bypass" and args:
            # aux will update .aux_info status file
            res = send_cmd( f'aux peq_bypass {args[0]}' )
            print(res)

        elif cmd == "PEQ_gain" and args:
            pm.eca_gain(args[0])

        else:
            print(f'(!) Bad command')
            print(__doc__)

    else:
        print(__doc__)
