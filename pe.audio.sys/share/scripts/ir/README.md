You'll need to learn about your remote.

Try to configure it to 1200 8 N 1 as start point.

Then run **`ir.py`** in learning mode:

    ir.py  -t v+     # v+ is a log file for the remote Vol+ key

and press the key Vol+ for about 10 times

If baudrate is good, you will see blocks of bytes.

If not, try to change the baudrate, some remotes needs weird values as 1500. Try and error.

Once the block bytes seemed to be consistent, you can run the provided tool to analyze them:

    ir_analyze.py v+

The graph will help you to decide about detecting packets by constant lenght or by an end octet (packetLength: or endOfPacket: under ir.config).

Repeat the process for each remote key you want to use, then configure them inside the **`ir.config`** file.

