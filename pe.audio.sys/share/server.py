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

    # https://realpython.com/python-sockets/#tcp-sockets

    def server_socket(host, port):
        """ Returns a TCP socket object, binded to host:port """

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

    # Instance a binded socket object
    s = server_socket(host, port)

    # MAIN LOOP to proccess connections
    while True:
        # initiate the socket in listen (server) mode
        s.listen()
        #if verbose:
        #    print( f'(server.py [{service}]) listening on \'localhost\':{port}' )

        # Waits for a client to be connected:
        # 'conn' is a socket itself
        conn, address = s.accept()
        if verbose:
            print( f'(server.py [{service}]) connected to client {address[0]}:{address[1]}' )

        # A buffer loop to proccess received data
        while True:

            try:
                # Reception of 1024
                data = conn.recv(1024).decode()
                if verbose:
                    print( f'(server.py [{service}]) Rx: {data.strip()}' )
            except:
                if verbose:
                    print( f'(server.py [{service}]) ERROR receiving from client, closing.' )
                conn.close()
                break

            if not data:
                # Nothing in buffer, then will close
                if verbose:
                    print( f'(server.py [{service}]) Rx empty, '
                             'closing connection...' )
                conn.close()
                break

            # Reserved words for controling the communication ('quit' or 'shutdown')
            if data.rstrip() == 'quit':
                if verbose:
                    print( f'(server.py [{service}]) \'quit\', closing connection...' )
                conn.close()
                break

            elif data.rstrip() == 'shutdown':
                if verbose:
                    print( f'(server.py [{service}]) shutting down the server...' )
                conn.close()
                s.close()
                sys.exit(1)

            # If not a reserved word, then process the received data as a command:
            else:
                # PROCESSING THE COMMAND through by MODULE.do()
                result = MODULE.do(data)
                if verbose and result:
                    print( f'(server.py [{service}]) Tx: {result}' )
                # And sending back the result
                if result:
                    conn.send( result.encode() )
                else:
                    # sending CRLF instead of empty to avoid hanging the receiver.
                    conn.send( '\r\n'.encode() )


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
