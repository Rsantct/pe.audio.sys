#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pe.audio.sys'
# 'pe.audio.sys', a PC based personal audio system.
"""
    Communicates with an LCDd driver
"""

# https://manpages.debian.org/testing/lcdproc/LCDd.8.en.html
# http://lcdproc.sourceforge.net/docs/current-dev.html

import socket


class Client(object):
    """ A LCDd client
    """

    def __init__(self, cname='lcd_cli', host="localhost", port=13666, verbose=False):
        self.cname          = cname
        self.host           = host
        self.port           = port
        self.verbose        = verbose
        self.error          = False
        self.LCDd_timeout   = .2

        if self.verbose:
            print('(lcd_client) VERBOSE MODE')


    def connect(self):

        self.cli = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        try:
            # if not timeout s.recv will hang :-/
            self.cli.settimeout(self.LCDd_timeout)
            self.cli.connect( (self.host, self.port) )
            if self.verbose:
                print(f'(lcd_client) Connected to the LCDd driver.')
            return True

        except Exception as e:
            print(f'(lcd_client) Error connecting to the LCDd driver: {str(e)}')
            self.cli.close()
            del (self.cli)
            self.error = True
            return False


    def send( self, msg ):
        """ sends a message to LCDd andn returns the received answer
        """

        def send( msg ):

            if self.verbose:
                print(f'(lcd_client) send: {msg}')

            try:
                self.cli.send( f'{msg}\n'.encode() )
                return True

            except Exception as e:
                print(f'(lcd_client) send ERROR: {str(e)}')
                self.error = True
                return False


        def received():

            ans = b''
            while True:
                try:
                    ans += self.cli.recv(1024)
                except:
                    break

            if self.verbose:
                print(f'(lcd_client) received: {ans}')

            return ans.decode().strip()


        if send(msg):
            return received()

        else:
            return ''


    def register( self ):
        """ Try to register a client into the LCDd server
        """
        ans = self.send('hello')
        if "huh?" not in ans:
            if 'success' in self.send( f'client_set name {self.cname}' ):
                print( f'(lcd_client) LCDd client \'{self.cname}\' registered' )
                return True
            else:
                print( f'(lcd_client) LCDd client \'{self.cname}\' ERROR registering' )
                self.error = True
                return False


    def get_size( self ):
        """ gets the LCD size
        """
        w = 0
        h = 0
        ans = self.send('hello').split()
        try:
            w = int( ans[ ans.index('wid') + 1 ] )
            h = int( ans[ ans.index('hgt') + 1 ] )
        except:
            pass
        return {'columns': w, 'rows': h}


    def delete_screen( self, sname ):
        self.query( f'screen_del {sname}' )


    def create_screen( self, sname, priority="info", duration=3, timeout=0 ):
        # duration: A screen will be visible for this amount of time every rotation (1/8 sec)
        # timeout:  After the screen has been visible for a total of this amount of time,
        #           it will be deleted (1/8 sec)
        self.query( f'screen_add {sname}' )
        duration *= 8
        timeout = str(timeout  * 8)
        self.query( f'screen_set {sname} -cursor no' )
        self.query( f'screen_set {sname} priority {priority}' )
        if duration != "0":
            self.query( f'screen_set {sname} duration {duration}' )
        if timeout != "0":
            self.query( f'screen_set {sname} timeout {timeout}' )


if __name__ == "__main__":

    # This is only for command line test purpose
    c = Client(cname='test', host='localhost', port=13666)
    if c.connect():
        c.register()
        print( '(lcd_client)', c.send('hello') )
        print( '(lcd_client)', c.get_size() )
