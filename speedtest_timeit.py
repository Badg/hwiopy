import hwiopy, time, timeit
bbb = hwiopy.platforms.BBB()
test_led = bbb.create_pin('8_7', 'gpio', 'test_led')
test_led.config('out')
def cycle():
    test_led.methods['output_high_nocheck']()
    test_led.methods['output_low_nocheck']()
with bbb as beagle:
    nn = 100000000
    duration = timeit.timeit(stmt=cycle, number=nn) / nn
hz = 1/duration
print('\n    Average time: ' + str(duration) + '\n    Frequency: ' + str(hz))
