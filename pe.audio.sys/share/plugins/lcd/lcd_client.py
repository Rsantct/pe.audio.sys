#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pe.audio.sys'
# 'pe.audio.sys', a PC based personal audio system.

"""
    Communicates with an LCDd server daemon
"""
# https://manpages.debian.org/testing/lcdproc/LCDd.8.en.html
# http://lcdproc.sourceforge.net/docs/current-dev.html

import socket


class Client(object):
    """ A LCDd client
    """

    def __init__(self, cname, host="localhost", port=13666):
        self.cname   = cname
        self.host    = host
        self.port    = port
        self.cli     = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.verbose = False

    def set_verbose(self, mode):
        self.verbose = mode

    def connect(self):
        try:
            self.cli.connect( (self.host, self.port) )
            self.cli.settimeout(.1)  # if not timeout s.recv will hang :-/
            print(f'(lcd_client) Connected to the LCDd server.')
            return True

        except:
            print(f'(lcd_client) Error connecting to the LCDd server.')
            self.cli.close()
            return False

    def query( self, phrase ):
        """sends a command phrase to LCDd then returns the received answer"""
        self.cli.send( f'{phrase}\n'.encode() )
        ans = b''
        while True:
            try:
                ans += self.cli.recv(1024)
            except:
                break
        return ans.decode().strip()

    def send( self, phrase ):
        """sends a command phrase to LCDd"""
        # This is faster than query to get an answer
        self.cli.send( f'{phrase}\n'.encode() )
        if self.verbose:
            print(phrase)

    def register( self ):
        """Try to register a client into the LCDd server"""
        ans = self.query('hello' )
        if "huh?" not in ans:
            if 'success' in self.query( f'client_set name {self.cname}' ):
                print( f'(lcd_client) LCDd client \'{self.cname}\' registered' )
            else:
                print( f'(lcd_client) LCDd client \'{self.cname}\' ERROR registering' )

    def get_size( self ):
        """gets the LCD size"""
        w = 0
        h = 0
        ans = self.query('hello').split()
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
        dur = str(duration * 8)
        tou = str(timeout  * 8)
        self.query( f'screen_set {sname} -cursor no' )
        self.query( f'screen_set {sname} priority {priority}' )
        if dur != "0":
            self.query( f'screen_set {sname} duration {dur}' )
        if tou != "0":
            self.query( f'screen_set {sname} timeout {tou}' )


if __name__ == "__main__":

    # This is only for command line test purpose
    c = Client('test', host='localhost', port=13666)
    if c.connect():
        c.register()
        print( '(lcd_client)', c.query('hello') )
        print( '(lcd_client)', c.get_size() )
