import hwiopy, time
bbb = hwiopy.platforms.BBB()
test_led = bbb.create_pin('8_7', 'gpio', 'test_led')
test_led.config('out')

nn = 100000000
fastup = test_led.methods['output_high_nocheck']
fastdown = test_led.methods['output_low_nocheck']

with bbb as beagle:
    for ii in range(nn):
        fastup()
        fastdown()
