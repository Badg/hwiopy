''' This is a sorta janky way to try and get a reasonable estimation of the 
absolute fastest speeds that could be reached using python on ubuntu 14.04 for
gpio access on the BBB.

With nn = 300000000, this should take about 15 minutes to run.
'''

import struct, time, mmap

# How many times to loop? Note that for loops are faster than while loops
nn = 300000000

# Memory addresses and stuff for the 8_7 pin. Must be preconfigured.
gpio2_base = 0x481AC000
gpio2_size = 4095
set_dataout = slice(0x194, 0x194 + 4)
clear_dataout = slice(0x190, 0x190 + 4)
my_channel = struct.pack('<L', 1<<2)

with open('/dev/mem', 'r+b') as f:
    with mmap.mmap(f.fileno(), gpio2_size, offset=gpio2_base) as mem:
        _start = time.process_time()
        for ii in range(nn):
            mem[set_dataout] = my_channel
            mem[clear_dataout] = my_channel
        _end = time.process_time()
        duration = (_end - _start) / nn
hz = 1/duration
print('\n    Average time: ' + str(duration) + '\n    Frequency: ' + str(hz))
