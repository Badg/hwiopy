''' This is a sorta janky way to try and get a reasonable estimation of the 
absolute fastest speeds that could be reached using python on ubuntu 14.04 for
gpio access on the BBB.

This is unpythonic, largely for performance reasons, but also slightly because
I'm being lazy and I really don't expect to use this much beyond the current 
evaluation.
'''

import struct, time, mmap, statistics

# How many times to loop? Note that for loops are faster than while loops
nn = 300000000
batch = 100
nn_range = range(0, nn, batch)
batch_range = range(batch)


# Memory addresses and stuff for the 8_7 pin. Must be preconfigured.
gpio2_base = 0x481AC000
# Note that the minumum size for mmap is 4095 and the size must be a multiple
# of 4096.
gpio2_size = 4095

print('\n### Process time:')

set_dataout_2_2 = slice(0x194, 0x194 + 1)
clear_dataout_2_2 = slice(0x190, 0x190 + 1)
# Construct 1 byte, little-endian, 0th channel on the right: 00000100
my_channel = struct.pack('<b', 1<<2)

# Create a list for times
times = []

with open('/dev/mem', 'r+b') as f:
    with mmap.mmap(f.fileno(), gpio2_size, offset=gpio2_base) as mem:
        for ii in nn_range:
            _start = time.process_time()
            for jj in batch_range:
                mem[set_dataout_2_2] = my_channel
                mem[clear_dataout_2_2] = my_channel
            _end = time.process_time()
            times.append((_end - _start) / batch)
hz = [1/tt for tt in times]
khz = [int(HZ)/1000 for HZ in hz]

tot_avg = statistics.mean(khz)
tot_med = statistics.median(khz)
med_50 = statistics.median_grouped(khz)

print('\nSetting 1-byte lines: \n'
    '    Total iterations: ' + str(nn) + '\n'
    '    Batch size: ' + str(batch) + '\n'
    '    Total average frequency: ' + str(tot_avg) + 'kHz\n'
    '    Median batch frequency: ' + str(tot_med) + 'kHz\n'
    '    Best batch frequency: ' + str(max(khz)) + 'kHz\n'
    '    Worst batch frequency: ' + str(min(khz)) + 'kHz\n'
    '    50th percentile batch: ' + str(med_50) + 'kHz\n')

set_dataout = slice(0x194, 0x194 + 4)
clear_dataout = slice(0x190, 0x190 + 4)
# Construct 4 bytes, little-endian, 0th channel on the right: ...00000100
my_channel = struct.pack('<L', 1<<2)

# Create a list for times
times = []

with open('/dev/mem', 'r+b') as f:
    with mmap.mmap(f.fileno(), gpio2_size, offset=gpio2_base) as mem:
        for ii in nn_range:
            _start = time.process_time()
            for jj in batch_range:
                mem[set_dataout] = my_channel
                mem[clear_dataout] = my_channel
            _end = time.process_time()
            times.append((_end - _start) / batch)
hz = [1/tt for tt in times]
khz = [int(HZ)/1000 for HZ in hz]

tot_avg = statistics.mean(khz)
tot_med = statistics.median(khz)
med_50 = statistics.median_grouped(khz)

print('\nSetting 4-byte lines: \n'
    '    Total iterations: ' + str(nn) + '\n'
    '    Batch size: ' + str(batch) + '\n'
    '    Total average frequency: ' + str(tot_avg) + 'kHz\n'
    '    Median batch frequency: ' + str(tot_med) + 'kHz\n'
    '    Best batch frequency: ' + str(max(khz)) + 'kHz\n'
    '    Worst batch frequency: ' + str(min(khz)) + 'kHz\n'
    '    50th percentile batch: ' + str(med_50) + 'kHz\n')

print('\n### Performance time:')

set_dataout_2_2 = slice(0x194, 0x194 + 1)
clear_dataout_2_2 = slice(0x190, 0x190 + 1)
# Construct 1 byte, little-endian, 0th channel on the right: 00000100
my_channel = struct.pack('<b', 1<<2)

# Create a list for times
times = []

with open('/dev/mem', 'r+b') as f:
    with mmap.mmap(f.fileno(), gpio2_size, offset=gpio2_base) as mem:
        for ii in nn_range:
            _start = time.perf_counter()
            for jj in batch_range:
                mem[set_dataout_2_2] = my_channel
                mem[clear_dataout_2_2] = my_channel
            _end = time.perf_counter()
            times.append((_end - _start) / batch)
hz = [1/tt for tt in times]
khz = [int(HZ)/1000 for HZ in hz]

tot_avg = statistics.mean(khz)
tot_med = statistics.median(khz)
med_50 = statistics.median_grouped(khz)

print('\nSetting 1-byte lines: \n'
    '    Total iterations: ' + str(nn) + '\n'
    '    Batch size: ' + str(batch) + '\n'
    '    Total average frequency: ' + str(tot_avg) + 'kHz\n'
    '    Median batch frequency: ' + str(tot_med) + 'kHz\n'
    '    Best batch frequency: ' + str(max(khz)) + 'kHz\n'
    '    Worst batch frequency: ' + str(min(khz)) + 'kHz\n'
    '    50th percentile batch: ' + str(med_50) + 'kHz\n')

set_dataout = slice(0x194, 0x194 + 4)
clear_dataout = slice(0x190, 0x190 + 4)
# Construct 4 bytes, little-endian, 0th channel on the right: ...00000100
my_channel = struct.pack('<L', 1<<2)

# Create a list for times
times = []

with open('/dev/mem', 'r+b') as f:
    with mmap.mmap(f.fileno(), gpio2_size, offset=gpio2_base) as mem:
        for ii in nn_range:
            _start = time.perf_counter()
            for jj in batch_range:
                mem[set_dataout] = my_channel
                mem[clear_dataout] = my_channel
            _end = time.perf_counter()
            times.append((_end - _start) / batch)
hz = [1/tt for tt in times]
khz = [int(HZ)/1000 for HZ in hz]

tot_avg = statistics.mean(khz)
tot_med = statistics.median(khz)
med_50 = statistics.median_grouped(khz)

print('\nSetting 4-byte lines: \n'
    '    Total iterations: ' + str(nn) + '\n'
    '    Batch size: ' + str(batch) + '\n'
    '    Total average frequency: ' + str(tot_avg) + 'kHz\n'
    '    Median batch frequency: ' + str(tot_med) + 'kHz\n'
    '    Best batch frequency: ' + str(max(khz)) + 'kHz\n'
    '    Worst batch frequency: ' + str(min(khz)) + 'kHz\n'
    '    50th percentile batch: ' + str(med_50) + 'kHz\n')

print('\n### Monotonic time:')

set_dataout_2_2 = slice(0x194, 0x194 + 1)
clear_dataout_2_2 = slice(0x190, 0x190 + 1)
# Construct 1 byte, little-endian, 0th channel on the right: 00000100
my_channel = struct.pack('<b', 1<<2)

# Create a list for times
times = []

with open('/dev/mem', 'r+b') as f:
    with mmap.mmap(f.fileno(), gpio2_size, offset=gpio2_base) as mem:
        for ii in nn_range:
            _start = time.monotonic()
            for jj in batch_range:
                mem[set_dataout_2_2] = my_channel
                mem[clear_dataout_2_2] = my_channel
            _end = time.monotonic()
            times.append((_end - _start) / batch)
hz = [1/tt for tt in times]
khz = [int(HZ)/1000 for HZ in hz]

tot_avg = statistics.mean(khz)
tot_med = statistics.median(khz)
med_50 = statistics.median_grouped(khz)

print('\nSetting 1-byte lines: \n'
    '    Total iterations: ' + str(nn) + '\n'
    '    Batch size: ' + str(batch) + '\n'
    '    Total average frequency: ' + str(tot_avg) + 'kHz\n'
    '    Median batch frequency: ' + str(tot_med) + 'kHz\n'
    '    Best batch frequency: ' + str(max(khz)) + 'kHz\n'
    '    Worst batch frequency: ' + str(min(khz)) + 'kHz\n'
    '    50th percentile batch: ' + str(med_50) + 'kHz\n')

set_dataout = slice(0x194, 0x194 + 4)
clear_dataout = slice(0x190, 0x190 + 4)
# Construct 4 bytes, little-endian, 0th channel on the right: ...00000100
my_channel = struct.pack('<L', 1<<2)

# Create a list for times
times = []

with open('/dev/mem', 'r+b') as f:
    with mmap.mmap(f.fileno(), gpio2_size, offset=gpio2_base) as mem:
        for ii in nn_range:
            _start = time.monotonic()
            for jj in batch_range:
                mem[set_dataout] = my_channel
                mem[clear_dataout] = my_channel
            _end = time.monotonic()
            times.append((_end - _start) / batch)
hz = [1/tt for tt in times]
khz = [int(HZ)/1000 for HZ in hz]

tot_avg = statistics.mean(khz)
tot_med = statistics.median(khz)
med_50 = statistics.median_grouped(khz)

print('\nSetting 4-byte lines: \n'
    '    Total iterations: ' + str(nn) + '\n'
    '    Batch size: ' + str(batch) + '\n'
    '    Total average frequency: ' + str(tot_avg) + 'kHz\n'
    '    Median batch frequency: ' + str(tot_med) + 'kHz\n'
    '    Best batch frequency: ' + str(max(khz)) + 'kHz\n'
    '    Worst batch frequency: ' + str(min(khz)) + 'kHz\n'
    '    50th percentile batch: ' + str(med_50) + 'kHz\n')