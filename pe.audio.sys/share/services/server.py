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


"""
    A general purpose TCP server to run processing modules

    Usage:   server.py  <processing_module>  <address>  <port> [-v]

    e.g:     server.py  control localhost 9999
             server.py  aux     localhost 9998

    (use -v for verbose debug info printout)
"""

import socket
import sys
import os


def run_server(host, port, verbose=False):
    """ This is the server itself.
        Inside, it is called the desired processing module
        to perform actions and giving results.
    """
    # https://realpython.com/python-sockets/#echo-client-and-server
    # One thing that’s imperative to understand is that we now have
    # a new socket object from accept(). This is important since
    # it’s the socket that you’ll use to communicate with the client.
    # It’s distinct from the listening socket that the server is using
    # to accept new connections

    # This loop has a blocking stage when calling accept() below
    while True:
        # The server (the 1st listening socket)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as srv:
            srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            srv.bind((host, port))
            srv.listen()
            # The connection (the 2nd socket)
            con, address = srv.accept()  # calling accept() is blocking
            with con:
                # Receiving a command phrase
                cmd = con.recv(1024).decode()
                if verbose:
                    print( f'(server.py-{service}) Rx: {cmd.strip()}' )
                # PROCESSING the command through by the plugged MODULE:
                result = MODULE.do( cmd.strip() )
                # Sending back the command processing result:
                con.sendall( result.encode() )
                if verbose:
                    print( f'(server.py-{service}) Tx: {result}' )


if __name__ == "__main__":

    # Mandatory: address and port from command line
    try:
        service, addr, port  = sys.argv[1:4]
    except:
        print(__doc__)
        sys.exit(-1)

    # Optional -v for verbose printing out (debug)
    if '-v' in sys.argv:
        verbose = True
    else:
        verbose = False

    # Adding the path where to look for importing service modules
    UHOME = os.path.expanduser("~")
    sys.path.append( f'{UHOME}/pe.audio.sys/share/services' )

    # Importing the service module
    # https://python-reference.readthedocs.io/en/latest/docs/functions/__import__.html
    MODULE = __import__(service)
    print( f'(server.py) will run \'{service}\' module at {addr}:{port} ...' )
    # Optional MODULE.init (autostart) function:
    try:
        MODULE.init()
    except:
        pass

    # Runing the server with the MODULE.do() interface
    run_server( host=addr, port=int(port), verbose=verbose )
