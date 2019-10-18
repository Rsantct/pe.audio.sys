#!/usr/bin/env python3

# Copyright (c) 2019 Rafael Sánchez
# This file is part of 'pe.audio.sys', a PC based personal audio system.

# This is based on 'pre.di.c,' a preamp and digital crossover
# https://github.com/rripio/pre.di.c
# Copyright (C) 2018 Roberto Ripio
# 'pre.di.c' is based on 'FIRtro', a preamp and digital crossover
# https://github.com/AudioHumLab/FIRtro
# Copyright (c) 2006-2011 Roberto Ripio
# Copyright (c) 2011-2016 Alberto Miguélez
# Copyright (c) 2016-2018 Rafael Sánchez
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

    Use:     server.py  <processing_module>  <address>  <port>

    e.g:     server.py  control localhost 9999
             server.py  aux     localhost 9998
"""

# The 'verbose' option can be useful when debugging:
verbose = False

import socket
import sys
import os
import yaml

def run_server(host, port, verbose=False):
    """ This is the server itself.
        Inside, it is called the desired processing module
        to perform actions and giving results.
    """

    def server_socket(host, port):
        """ Returns a socket 's' that listen to clients """

        # We use socket.SO_REUSEADDR to avoid this error:
        # socket.error: [Errno 98] Address already in use
        # that can happen if we reinit this script.
        # This is because the previous execution has left the socket in a
        # TIME_WAIT state, and cannot be immediately reused.
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # the tcp socket
        try:
            s.bind((host, port))
        except:
            print( f'(server.py [{service}]) Error binding {host}:{port}' )
            s.close()
            sys.exit(-1)

        # returns the socket object
        return s

    # Creates the socket
    mysocket = server_socket(host, port)

    # MAIN LOOP to proccess connections
    maxconns = 10
    while True:
        # Listen for a queue of connections
        mysocket.listen(maxconns)
        if verbose:
            print( f'(server.py [{service}]) listening on \'localhost\':{port}' )

        # Waits for a client to be connected:
        sc, remote = mysocket.accept()
        if verbose:
            print( f'(server.py [{service}]) connected to client {remote[0]}' )

        # A buffer loop to proccess received data
        while True:
            # Reception
            data = sc.recv(4096).decode()

            if not data:
                # Nothing in buffer, then will close because the client has disconnected too soon.
                if verbose:
                    print (f'(server.py [{service}]) Client disconnected. \
                             Closing connection...' )
                sc.close()
                break

            # Reserved words for controling the communication ('quit' or 'shutdown')
            elif data.rstrip('\r\n') == 'quit':
                sc.send(b'OK\n')
                if verbose:
                    print( f'(server.py [{service}]) closing connection...' )
                sc.close()
                break

            elif data.rstrip('\r\n') == 'shutdown':
                sc.send(b'OK\n')
                if verbose:
                    print( f'(server.py [{service}]) Shutting down the server...' )
                sc.close()
                mysocket.close()
                sys.exit(1)

            # If not a reserved word, then process the received data as a command:
            else:
                if verbose:
                    print  ('>>> ' + data )
                
                #######################################################################
                # PROCESSING by using the IMPORTED MODULE when starting up this server,
                # always must use the the module do() function.
                result = MODULE.do(data)
                #######################################################################

                # And sending back the result
                # NOTICE: it is expected to receive a result as a bytes-like object
                if result:
                    sc.send( result )
                else:
                    sc.send( b'' )

                if verbose:
                    print( f'(server.py [{service}]) connected to client {remote[0]}' )


if __name__ == "__main__":
    
    # Mandatory: address and port from command line
    try:
        service, addr, port  = sys.argv[1:4]
    except:
        print(__doc__)
        sys.exit(-1)
        
    
    # Read paths where to look for processing plugins
    UHOME = os.path.expanduser("~")
    THISPATH = os.path.dirname(os.path.abspath(__file__))
    with open(f'{THISPATH}/server.yml', 'r') as f:
        config = yaml.load(f)
    for path in config['paths']:
        sys.path.append( f'{UHOME}/{path}' )

    # MAIN
    try:
        # https://python-reference.readthedocs.io/en/latest/docs/functions/__import__.html
        MODULE = __import__(service)
        print( f'(server.py) will run \'{service}\' module ...' )
        run_server( host=addr, port=int(port), verbose=verbose )

    except:
        print( f'(server.py) stopped after \'{service}\' module has broken. Bye' )
