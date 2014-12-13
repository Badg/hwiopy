hwiopy
======

Hardware IO for SOCs in python, starting with Beaglebone Black.

Introduction
----------

First, sorry (seriously sorry) but for the time being, the documentation here is going to be narsty. Not *lacking*, but more of a "brain dump" than an explanation. So it may only be helpful to me. But, uh, better than nothing? Probably? I wish I had time (or the resources to hire someone to document my shit) but at this point I'm just stretched too thinly. Butter over too much bread and all that. Speaking of which, this is being developed on python 3.4 with no intention of supporting python 2.

All that said: the purpose of this library is to develop a standard platform-independent API for platform-dependent hardware access, in the spirit of Kivy and Plyer. At the moment I'm developing for beaglebone black, with Raspi in the back of my head as another possible target. Ideally I'd like to make the library as simple to use as "write [value] to [pin]". All in due time.

Special thanks to [Tabula](http://tabula.technology/) for help with datasheet table processing.

Installation
===========

    git clone https://github.com/Badg/hwiopy.git

For now, there is no stable release, so you must:

    git branch -b develop origin/develop
    git checkout develop

Gotchas and other things that are likely to screw you up or otherwise don't work yet
============

Hwiopy currently only supports gpio output.

Before being used, the pin must be manually exported for use. I've been doing this by using sysFS to export pins. To enable gpio, first figure out what terminal of the Sitara SoC the BBB is connected to:

    bbb = hwiopy.platforms.BBB()
    test_pin = bbb.create_pin('8_7', 'gpio', 'test_pin')
    sitara_terminal = test_pin.terminal

then figure out what GPIO number we have:

    gpio_desc = bbb.system._resolve_mode.describe(test_pin.terminal, 'gpio')
    gpio_num = gpio_dec['mode_name']

it should look like "gpio2_2", "gpio1_22", etc. Now take the first number (this is the register number; there's gpio0, gpio1, gpio2, etc, each with 32 bits/channels total). Multiply that by 32, and add the second number. So gpio2_2 becomes (2*32) + 2, gpio1_22 becomes (1*32) + 22, etc. That's the number you use when you use the sysFS mappings to configure the pin, for example:

    echo 66 > /sys/class/gpio/export 

will set up the gpio2_2 channel, which corresponds to pin 8_7 on the BBB header.

As of this writing, you do not need to set the output/input configuration in sysFS; hwiopy will do that for you.


Preliminary work
=============

SysFS access for reference speeds:
--------------

    sudo ~/.virtualenvs/python34/bin/python
    import timeit
    timeit.timeit("io.open('/sys/class/leds/beaglebone:green:usr0/brightness', 'rb')", setup='import io', number=10000)/10000

(timeit.timeit for 10000x testing) yielded an average access time of:

* .000370 seconds, corresponding to 2.7 khz
* .000202 seconds, corresponding to 4.95 khz
* .000219 seconds, corresponding to 4.57 khz

and for 1000000x testing yielded an average access time of:

* .000183 seconds, corresponding to 5.46 khz
* .000183 seconds, corresponding to 5.46 khz
* .000182 seconds, corresponding to 5.49 khz

Turning off buffering:

    timeit.timeit("io.open('/sys/class/leds/beaglebone:green:usr0/brightness', 'rb', buffering=0)", setup='import io', number=10000)/10000

resulted, for 10000x:

* .000178 seconds, corresponding to 5.62 khz
* .000172 seconds, corresponding to 5.81 khz
* .000181 seconds, corresponding to 5.52 khz

and for 1000000x testing yielded an average access time of:

* .000154 seconds, corresponding to 6.49 khz
* .000153 seconds, corresponding to 6.54 khz
* .000153 seconds, corresponding to 6.54 khz

[Scope testing](http://i.imgur.com/ReNK9gz.png) the adafruit library resulted in a 6.826kHz max switching speed.

Accessing one pin explicitly using python in /dev/mem for a maximum expectable performance baseline
-----------------

Using a direct, explicitly-hardcoded memory access approach, I was able to reach average switching speeds (one cycle being turn the pin on, turn the pin off) of 350-450 kHz over a test duration of 2-15 minutes. This was likely approaching the limits of timer overhead; it would be better to verify this with a scope. At any rate I would expect around 500 kHz to be an approximate maximum switching speed for python gpio access. The file used for this test is vollgas_test.py, and the timing mechanism is pretty basic.

This script is also a good place to test optimizations; for example, what happens if you decrease the size of the mmap, or decrease the number of bits you're setting? You don't *actually* need to pull the entire 32-bit register to update a GPIO pin; how much faster is it if you don't?

Scratchbook
===========

All (period?) "prior art" packages do io through writing to sysfs. Adafruit library, for example, uses this through a... rather convoluted c++ wrapper. This package, on the other hand, 

Can also map pins to /dev/mem using mmap? This would be a possible route for improvement. Not 100% sure how to deal with pinmuxing -- perhaps mux with the /sys/ mappings -- but theoretically possible within /dev/mem as well. [Check this out.](http://chiragnagpal.com/examples.html)

I compared IO for the simple /sys/ mappings was between numpy and the stock io libraries. Stock io was significantly faster, roughly 3x.

**You will take a significant performance hit if you try to access functions via the pin dictionary. Give them a new name first, then call that:**

    fastup = test_led.methods['output_high_nocheck']
    fastdown = test_led.methods['output_low_nocheck']

Could probably speed things up a bit more by using lambdas with default arguments and stuff.


Memory mapping
------------

The ARM cortex A8 TRM, BBB SRM, and a datasheet or two are in /doc. I realize that it's not necessarily the best practice to include those in the git repo, but the links to them online seem to have been a little less static than would otherwise be desirable, making them difficult to link to. I'd rather unambiguously and conveniently include them here. That said, the json files in the source code are likely to be more helpful.

By far the most tedious part about this has been bringing in the bitwise/bytewise description of the /dev/mem mapping. All of the information I've gathered has been put into json files: check them out if you're looking to do any other kind of access to the memory register, as it will save an enormous amount of time compared to the reference material. For any register that contains the string "_intchannel", the corresponding part of the register uses 1 bit per GPIO. So for example, on the gpio1 register, when you set output, bit 1 is gpio1-1, bit 2 is gpio1-2, bit 3 is gpio1-3, etc.

Planning committee
-------

+ **Need to compare the speed of the library with the speed of explicitly calling out the bits to change**

+ capability to declare a pin for a purpose
+ resolve pin on header to memory mapping
    + serialize arm cortex a8 memory mappings
    + serialize bbb pinout mappings
+ specify "plug" and have pins automatically declared 
    + ex: create SPI0 plug
    + include any possible onboard conflicts, like USB or HDMI
+ subclass plugs (ex add more chip selects to SPI0)
+ check for overlap on "plugs" (ex: accidentally using SPI1 and HDMI)
+ print pinout method


Some links
-------

* [Python mmap for control on 3.2](http://www.alexanderhiam.com/tutorials/beaglebone-io-using-python-mmap/)
* [C mmap for control on 3.8](http://chiragnagpal.com/examples.html)
* [PyRUSS: Existing PRU library](http://hipstercircuits.com/pypruss-a-simple-pru-python-binding-for-beaglebone/)
* [PuBBIO: similar, for older kernel](https://github.com/alexanderhiam/PyBBIO)
* [Enable PWM on BeagleBone with Device Tree overlays](http://hipstercircuits.com/enable-pwm-on-beaglebone-with-device-tree-overlays/)
* [SysFS use reference](http://www.armhf.com/using-beaglebone-black-gpios/)
* [Muxing reference on stackoverflow](http://stackoverflow.com/questions/16872763/configuring-pins-mode-beaglebone)
* [Interrupts thru gpio](http://www.linux.com/learn/tutorials/765810-beaglebone-black-how-to-get-interrupts-through-linux-gpio)
* [Interesting C++ library](http://mkaczanowski.com/beaglebone-black-cpp-gpio-library-for-beginners/)

SPI links
------

* [Some quick SPI notes](https://github.com/notro/fbtft/wiki/BeagleBone-Black)
* [Getting SPI1 working with multiple CS (watch out for pin 42)](http://stackoverflow.com/questions/24078938/bbb-trouble-getting-second-spi-chip-select-with-device-tree)
* [Basic rundown on doing it with overlays](http://hipstercircuits.com/enable-spi-1-0-and-1-1-with-device-tre-overlays-on-beaglebone/)
* [Another howto](http://www.linux.com/learn/tutorials/746860-how-to-access-chips-over-the-spi-on-beaglebone-black)
* [On using GPIO as extra chip selects](https://groups.google.com/forum/#!topic/beagleboard/mMr0C5GNhRk)
* [Olimex post on multiple chipselects](https://www.olimex.com/forum/index.php?topic=2279.0)

PRU links
--------

* [beagleboard.org on PRUs](http://beagleboard.org/pru)