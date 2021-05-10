#!/usr/bin/env python3

'''
    A helper macro to listen to a remote pe.audio.sys machine.

    For further details see

        doc/80_Remote_pe.audio.sys.md

        share/scripts/zita_link.py
'''


from json import loads as json_loads
import sys
import os

UHOME = os.path.expanduser("~")
sys.path.append(f'{UHOME}/pe.audio.sys/share')

from miscel import send_cmd, get_my_ip, get_remote_source_info


# Getting remote source parameters
source, remote_addr, remote_port  = get_remote_source_info()


# Restarting zita process on sender side (sender will do only if needed)
my_ip = get_my_ip()
send_cmd(f'aux zita_client {my_ip} start', host=remote_addr, port=remote_port)


# -------- CUSTOM SETUP ----------
# Balancing delays and  filtering:
print(f'Balancing delays for listening along with the remote loudspeaker')
# OPTIONAL LOCAL  SETTINGS (sample)
#send_cmd('preamp set_xo mp')
#send_cmd('aux add_delay 150')
# OPTIONAL REMOTE SETTINGS (sample)
#send_cmd('preamp set_xo mp',   host=remote_addr, port=remote_port)
#send_cmd('aux add_delay 150',  host=remote_addr, port=remote_port)
# --------------------------------


# Switching local source
send_cmd(  'player pause' )
send_cmd( f'preamp input {source}' )

# -------- OPTIONAL --------
# Linking the relative changes in volume from the remote sender,
# by announcing that we are listening to it.
# (The remote script 'remote_volume.py' will listen at remote_port + 5)
send_cmd('hello', host=remote_addr, port=remote_port + 5)

print('End.')
