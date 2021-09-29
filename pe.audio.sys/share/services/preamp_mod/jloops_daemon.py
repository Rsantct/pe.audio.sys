#!/usr/bin/env python3

# Copyright (c) 2019 Rafael Sánchez
# This file is part of 'pe.audio.sys', a PC based personal audio system.
#
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
    A daemon that provides the needed loops
    on Jack to pe.audio.sys to work.
"""
# NOTICE:   This needs JACK to be running.
#           Also, if jackd is interrupted, this will vanish.

import os
import yaml
import jack
import multiprocessing as mp

UHOME = os.path.expanduser("~")


def jack_loop(clientname, nports=2):
    """ Creates a jack loop with given 'clientname'
        NOTICE: this process will keep running until broken,
                so if necessary you'll need to thread this when calling here.
    """
    # CREDITS:  https://jackclient-python.readthedocs.io/en/0.4.5/examples.html

    # The jack module instance for our looping ports
    client = jack.Client(name=clientname, no_start_server=True)

    if client.status.name_not_unique:
        client.close()
        print( f'(jack_loop) \'{clientname}\' already exists in JACK, nothing done.' )
        return

    # Will use the multiprocessing.Event mechanism to keep this alive
    event = mp.Event()

    # This sets the actual loop that copies frames from our capture to our playback ports
    @client.set_process_callback
    def process(frames):
        assert len(client.inports) == len(client.outports)
        assert frames == client.blocksize
        for i, o in zip(client.inports, client.outports):
            o.get_buffer()[:] = i.get_buffer()

    # If jack shutdowns, will trigger on 'event' so that the below 'whith client' will break.
    @client.set_shutdown_callback
    def shutdown(status, reason):
        print('(jack_loop) JACK shutdown!')
        print('(jack_loop) JACK status:', status)
        print('(jack_loop) JACK reason:', reason)
        # This triggers an event so that the below 'with client' will terminate
        event.set()

    # Create the ports
    for n in range( nports ):
        client.inports.register(f'input_{n+1}')
        client.outports.register(f'output_{n+1}')
    # client.activate() not needed, see below

    # This is the keeping trick
    with client:
        # When entering this with-statement, client.activate() is called.
        # This tells the JACK server that we are ready to roll.
        # Our above process() callback will start running now.

        print( f'(jack_loop) running {clientname}' )
        try:
            event.wait()
        except KeyboardInterrupt:
            print('\n(jack_loop) Interrupted by user')
        except:
            print('\n(jack_loop)  Terminated')


def main():
    """ Preparing the loops:
        - a preamp loop
        - as loops as needed from the config.yml sources.
    """
    # 1st: auto spawn the PREAMP loop ports
    jloop = mp.Process( target=jack_loop, args=['pre_in_loop', 2] )
    jloop.start()
    # 2nd: the SOURCE's connection loop ports:
    for source in CONFIG['sources']:
        pname = CONFIG['sources'][source]['jack_pname']
        if 'loop' in pname:
            jloop = mp.Process( target=jack_loop, args=(pname,) )
            jloop.start()


if __name__ == '__main__':

    with open(f'{UHOME}/pe.audio.sys/config.yml', 'r') as f:
        CONFIG = yaml.safe_load(f)

    main()
