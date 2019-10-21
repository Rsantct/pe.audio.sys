## Mixing sources

If you are interested on running a mixer for your jack sources, here we provide a **[jackminimix](https://www.aelius.com/njh/jackminimix/)** scripts for pre.di.c to work with.

    pre.di.c/init/jackminimix                   # Init the mixer when starting pre.di.c
    pre.di.c/clients/bin/jackminimix_start.sh   # Starts the mixer and connects configured sources
    pre.di.c/clients/bin/jackminimix_ctrl.py    # Controls mixer inputs gains on the fly

The `jackminimix` program can by hosted under `~/bin`. The running program can be controlled on the fly via OSC protocol.

Unfortunately direct udp messages via netcat does not work for me, neither I was able to use the pure Python OSC implementation [python-osc](https://pypi.org/project/python-osc) because not available under Berryconda (Python Anaconda distro for Raspberry Pi)... So here we use `oscchief`, a nice OSC command line tool.

**[oscchief](https://github.com/hypebeast/oscchief)**

It is needed that you compile both `jackminimix` and `oscchief` tools. Not needs `make install`, just copy the compiled binaries under your ~/bin folder.

**Notice**: when compiling `oscchief` under Raspbian, it was necessary to edit the `Makefile` to use `LDLIBS` this way:

    LDLIBS=`pkg-config --static --libs liblo`


Here we provide armhf compiled binaries under this doc folder for your convenience.
