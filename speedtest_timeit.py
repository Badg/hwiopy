import hwiopy, time
bbb = hwiopy.platforms.BBB()
test_led = bbb.create_pin('8_7', 'gpio', 'test_led')
test_led.config('out')

nn = 10000000
fastup = test_led.methods['output_high_nocheck']
fastdown = test_led.methods['output_low_nocheck']

with bbb as beagle:
    _start = time.monotonic()
    for ii in range(nn):
        fastup()
        fastdown()
    _end = time.monotonic()

duration = (_end - _start) / nn
hz = 1/duration
print('\n    Iterations: ' + str(nn) + '\n'
    '    Average time: ' + str(duration) + '\n'
    '    Frequency: ' + str(hz) + '\n')
