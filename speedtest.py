import hwiopy, time
bbb = hwiopy.platforms.BBB()
test_led = bbb.create_pin('8_7', 'gpio', 'test_led')
test_led.config('out')
with bbb as beagle:
    while True:
        test_led.methods['output_high_nocheck']()
        test_led.methods['output_low_nocheck']()
