#!/usr/bin/env python3

'''
    A helper macro to listen to a remote pe.audio.sys machine.

    For further details see

        doc/80_Multiroom_pe.audio.sys.md

        share/scripts/zita_link.py
'''
### USER CONFIG HERE:
REM_SRC_NAME = "remoteXXXXXX"
REM_ADD_DELAY = 100
LOC_ADD_DELAY = 0
###


from json import loads as json_loads
import sys
import os

UHOME = os.path.expanduser("~")
sys.path.append(f'{UHOME}/pe.audio.sys/share/miscel')

from miscel import send_cmd, get_my_ip, get_remote_sources_info


# Getting remote source parameters
remote_sources = get_remote_sources_info()
if not remote_sources:
    print(f'(remote_source) ERROR remote sources not available')
    sys.exit()

found = False
for item in remote_sources:
    sname, remote_addr, remote_port  = item
    if sname == REM_SRC_NAME:
        found = True
        break
if not found:
    print(f'(remote_source) ERROR remote source {REM_SRC_NAME} not found')
    sys.exit()


# Restarting zita process on sender side (sender will do only if needed)
my_ip = get_my_ip()
send_cmd(f'aux zita_client {my_ip} start', host=remote_addr, port=remote_port)


# -------- CUSTOM SETUP ----------
# Balancing delays and  filtering:
print(f'Balancing delays for listening along with the remote loudspeaker')
# OPTIONAL LOCAL  SETTINGS (example)
#send_cmd( 'set_xo mp')
#send_cmd(f'add_delay {LOC_ADD_DELAY}')
# OPTIONAL REMOTE SETTINGS (example)
#send_cmd( 'set_xo mp',                  host=remote_addr, port=remote_port)
#send_cmd(f'add_delay {REM_ADD_DELAY}',  host=remote_addr, port=remote_port)
# --------------------------------


# Switching local source
send_cmd( 'player pause')
send_cmd(f'input {REM_SRC_NAME}')

# -------- OPTIONAL --------
# Linking the relative changes in volume from the remote sender,
# by announcing that we are listening to it.
# (The remote script 'remote_volume.py' will listen at remote_port + 5)
send_cmd('hello', host=remote_addr, port=remote_port + 5)

print('End.')
