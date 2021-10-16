#!/usr/bin/env python3

# Copyright (c) 2021 Rafael Sánchez
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

"""
    An auxiliary server for Wake On Lan other machines

    Usage:   wolserver.py [-v]

    (use -v for verbose debug info printout)
"""

import socket
import sys
import os
import yaml
from subprocess import Popen

MY_DIR = os.path.dirname(__file__)

# You can use this propertie when importing this module,
# in order to retrieve que connected client address.
CLIADDR = ('', 0)

def run_server(host, port, verbose=False):
    """ Inside this simple server, it is called the desired PROCESSING MODULE to
        request the actual service action then will return back the action result.
    """
    # UNDERSTANDING A SERVER:
    # https://realpython.com/python-sockets/#echo-client-and-server
    # One thing that’s imperative to understand is that we now have
    # a new socket object from accept(). This is important since
    # it’s the socket that you’ll use to communicate with the client.
    # It’s distinct from the listening socket that the server is using
    # to accept new connections

    # (i) In a future, Python 3.8 will provide a higher level function
    #     'create_server()' that can replace the below 4 commands for
    #     srv creation. In the meanwhile, lets use the well known procedure:

    # Prepare the server (the 1st listening socket)
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((host, port))
    # The backlog option allows to limit the number of future connections
    srv.listen(10)

    global CLIADDR
    # Main loop to accept, process and close connections.
    # This loop has a blocking stage when calling accept() below
    while True:
        # The connection (the 2nd socket)
        # NOTICE: calling accept() is blocking
        con, CLIADDR = srv.accept()
        # The 'with' context will close 'con' on exiting from 'with'
        with con:
            # Receiving a command phrase
            cmd = con.recv(1024).decode()
            if verbose:
                print( f'(wolserver) Rx: {cmd.strip()}' )
            # PROCESSING the command through by the plugged MODULE:
            result = MODULE.do( cmd.strip() )
            # Sending back the command processing result:
            con.sendall( result.encode() )
            if verbose:
                print( f'(wolserver) Tx: {result}' )


if __name__ == "__main__":

    # command line
    for opc in sys.argv[1:]:
        if opc == 'stop':
            Popen( 'pkill -f -KILL wolserver.py'.split() )
            sys.exit()

    # Loading configured machines
    try:
        with open(f'{MY_DIR}/wolservice/wolservice.cfg', 'r') as f:
            CONFIG = yaml.safe_load(f)
            addr = CONFIG["server_addr"]
            port = CONFIG["server_port"]
    except:
        print(f'(wolservice) UNABLE to read wolservice.cfg')
        sys.exit()

    # Optional -v for verbose printing out (debug)
    if '-v' in sys.argv:
        verbose = True
    else:
        verbose = False

    # Adding the path where to look for importing the service module
    sys.path.append( f'{MY_DIR}/wolservice' )

    # Importing the service module
    # https://python-reference.readthedocs.io/en/latest/docs/functions/__import__.html
    MODULE = __import__('wolservice')
    print( f'(wolserver) will run \'wolservice\' module at {addr}:{port} ...' )

    # Runing the server with the MODULE.do() interface
    run_server( host=addr, port=int(port), verbose=verbose )
