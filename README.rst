hwiopy
======

Hardware IO for SOCs in python, starting with Beaglebone Black.

Introduction
----------

First, sorry (seriously sorry) but for the time being, the documentation here is going to be narsty. Not *lacking*, but more of a "brain dump" than an explanation. So it may only be helpful to me. But, uh, better than nothing? Probably? I wish I had time (or the resources to hire someone to document my shit) but at this point I'm just stretched too thinly. Butter over too much bread and all that. Speaking of which, this is being developed on python 3.4, and I don't have time to support python 2. One last apology: my link formatting was largely lost in the .md -> .rst transition. I haven't yet taken the time to update old links, but new ones should be added correctly.

**Everything is currently under development. This is serious danger zone code here, absolutely unstable. But I'm actively using hwiopy, so I wouldn't expect game-breaking changes to happen on a regular basis or anything.**

All that said: the purpose of this library is to develop a universal API for low-level hardware access in python. In other words, I would like to see, if possible, 100% code reuse between, for example, a beaglebone black and a raspberry pi. At the moment I'm developing for beaglebone black, with Raspi in the back of my head as another possible target. At the time being, use looks like this:

    import hwiopy
    bbb = hwiopy.platforms.BBB()
    test_led = bbb.create_pin('8_7', 'gpio', 'test_led')
    test_led.config('out')

    with bbb as beagle:
        for ii in range(1000):
            test_led.methods['output_high_nocheck']()
            test_led.methods['output_low_nocheck']()

Special thanks to [Tabula](http://tabula.technology/) for help with datasheet table processing.

Installation
===========

    pip install hwiopy

I'm working on adding automatic device tree overlay compilation during the install process. For now, this is just an sdist.

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

Using a direct, explicitly-hardcoded memory access approach, I was able to reach average switching speeds (one cycle being turn the pin on, turn the pin off) of 350-450 kHz over a test duration of 2-15 minutes. This was likely approaching the limits of timer overhead; it would be better to verify this with a scope. At any rate I would expect around 500 kHz to be an approximate maximum switching speed for python gpio access. The file used for this test is vollgas_stats.py, and the timing mechanism is pretty basic.

This script is also a good place to test optimizations; for example, what happens if you decrease the number of bits you're setting? You don't *actually* need to pull the entire 32-bit register to update a GPIO pin; how much faster is it if you don't?

Note that I've actually run this test. First, it's worth noting that the minimum mmap size for the BBB is 4096 bytes, or 0:4095, and that any mmap must be a multiple of that. So the 4KB gpio register is already the minimum mmap-able size. I've not seen an appreciable difference between setting single bytes and setting the entire four-byte "setdataout" or "cleardataout" "line" of the register; both appear to max out at 350-450 kHz with results averaged across test times ranging from 1.5 to 15 minutes.

Tests as of 15 Dec 2014, on commit ddd34a0, running "stock" ubuntu 14.04:

**Process time, setting 1-byte words:**

+ Total iterations:         | 300000000
+ Batch size:               | 100
+ Total average frequency:  | 425.49753103800003 kHz
+ Median batch frequency:   | 428.954 kHz
+ Best batch frequency:     | 431.188 kHz
+ Worst batch frequency:    | 215.053 kHz
+ 50th percentile batch:    | 429.0548687006123 kHz

**Process time, setting 4-byte words:**

+ Total iterations:         | 300000000
+ Batch size:               | 100
+ Total average frequency:  | 422.53790626833336 kHz
+ Median batch frequency:   | 426.288 kHz
+ Best batch frequency:     | 427.503 kHz
+ Worst batch frequency:    | 245.198 kHz
+ 50th percentile batch:    | 426.0616522026246 kHz

**Performance time, setting 1-byte words:**

+ Total iterations:         | 300000000
+ Batch size:               | 100
+ Total average frequency:  | 427.95563750233333 kHz
+ Median batch frequency:   | 431.732 kHz
+ Best batch frequency:     | 433.918 kHz
+ Worst batch frequency:    | 12.063 kHz
+ 50th percentile batch:    | 431.5824456327986 kHz

**Performance time, setting 4-byte words:**

+ Total iterations:         | 300000000
+ Batch size:               | 100
+ Total average frequency:  | 425.1705433643333 kHz
+ Median batch frequency:   | 429.184 kHz
+ Best batch frequency:     | 430.263 kHz
+ Worst batch frequency:    | 102.722 kHz
+ 50th percentile batch:    | 429.12251310922545 kHz

**Monotonic time, setting 1-byte words:**

+ Total iterations:         | 300000000
+ Batch size:               | 100
+ Total average frequency:  | 427.99319446199996 kHz
+ Median batch frequency:   | 431.733 kHz
+ Best batch frequency:     | 433.839 kHz
+ Worst batch frequency:    | 7.158 kHz
+ 50th percentile batch:    | 431.423574404455 kHz

**Monotonic time, setting 4-byte words:**

+ Total iterations:         | 300000000
+ Batch size:               | 100
+ Total average frequency:  | 424.9962927153333 kHz
+ Median batch frequency:   | 428.954 kHz
+ Best batch frequency:     | 430.185 kHz
+ Worst batch frequency:    | 23.066 kHz
+ 50th percentile batch:    | 429.0035250076771 kHz

It's very clear from these results that there are some serious limitations associated with the non-RT nature of the system, with some batches having almost millisecond-order latencies. These indicate that a preempt-RT patch might be worth considering, and that bit banging protocols may have some serious difficulties running directly (without assistance from PRUs).

Also, as a note, I'm seeing roughly 4x slower than other reported speeds. Part of me wonders if it's possible for this to have something to do with data structure alignment in the register?

Pinmuxing and pin setup process
==================

From the pyBBIO developer, [here](http://graycat.io/tutorials/beaglebone-io-using-python-mmap/):

> All this pinmuxing is handled by the AM335x control module. Of course there’s a catch, which is hiding in section 9.1:

>> Note: For writing to the control module registers, the Cortex A8 MPU will need to be in privileged mode of operation and writes will not work from user mode.

> Luckily, thanks to the friendly BeableBone developers, there is a user-level workaround. There is a file for each external pin found in /sys/kernel/debug/omap_mux/. Writing to these files tells a driver to configure the pin multiplexers as desired. To find the proper file names is a bit of a pain, and requires one more document; the AM3359 datasheet, found here.

Unfortunately this solution has been eliminated in the 3.8 kernel, neceessitating the use of device tree overlays. It's also worth mentioning that PRUSS access requires modification of the device tree itself, not just an overlay.

--------------------

Overlay generation:

Need to set up pip install, then generate overlays for every function and stuff.

Autoconfiguring library with metaclass? "lshw # gets quite a bit of information on everything about your CPU"

Should definitely reconfigure library with metaclasses. DeviceMeta would be particularly useful:

+ Register any user-defined devices in a dict
+ Provide singular API to hwiopy.Device instead of platform-specific device calls like hwiopy.platforms.BBB
+ Facilitate automagic detection of platform, thereby enabling singular API ^
+ Basically, distill the various platforms into a single Device class, so that code can be ported unmodified to different platforms.
+ Reduce platform-specific boilerplate

though (some caveat that I forgot was going to be here)

---------------------

From a [helpful stackoverflow page](http://stackoverflow.com/questions/13124271/driving-beaglebone-gpio-through-dev-mem), whose author [also has a small library with some good reference](https://github.com/facine/easyBlack/blob/master/src/memGPIO.cpp), see some C code:

    enableClockModules () {
        // Enable disabled GPIO module clocks.
        if (mapAddress[(CM_WKUP_GPIO0_CLKCTRL - MMAP_OFFSET) / GPIO_REGISTER_SIZE] & IDLEST_MASK) {
          mapAddress[(CM_WKUP_GPIO0_CLKCTRL - MMAP_OFFSET) / GPIO_REGISTER_SIZE] |= MODULEMODE_ENABLE;
          // Wait for the enable complete.
          while (mapAddress[(CM_WKUP_GPIO0_CLKCTRL - MMAP_OFFSET) / GPIO_REGISTER_SIZE] & IDLEST_MASK);
        }
        if (mapAddress[(CM_PER_GPIO1_CLKCTRL - MMAP_OFFSET) / GPIO_REGISTER_SIZE] & IDLEST_MASK) {
          mapAddress[(CM_PER_GPIO1_CLKCTRL - MMAP_OFFSET) / GPIO_REGISTER_SIZE] |= MODULEMODE_ENABLE;
          // Wait for the enable complete.
          while (mapAddress[(CM_PER_GPIO1_CLKCTRL - MMAP_OFFSET) / GPIO_REGISTER_SIZE] & IDLEST_MASK);
        }
        if (mapAddress[(CM_PER_GPIO2_CLKCTRL - MMAP_OFFSET) / GPIO_REGISTER_SIZE] & IDLEST_MASK) {
          mapAddress[(CM_PER_GPIO2_CLKCTRL - MMAP_OFFSET) / GPIO_REGISTER_SIZE] |= MODULEMODE_ENABLE;
          // Wait for the enable complete.
          while (mapAddress[(CM_PER_GPIO2_CLKCTRL - MMAP_OFFSET) / GPIO_REGISTER_SIZE] & IDLEST_MASK);
        }
        if (mapAddress[(CM_PER_GPIO3_CLKCTRL - MMAP_OFFSET) / GPIO_REGISTER_SIZE] & IDLEST_MASK) {
          mapAddress[(CM_PER_GPIO3_CLKCTRL - MMAP_OFFSET) / GPIO_REGISTER_SIZE] |= MODULEMODE_ENABLE;
          // Wait for the enable complete.
          while (mapAddress[(CM_PER_GPIO3_CLKCTRL - MMAP_OFFSET) / GPIO_REGISTER_SIZE] & IDLEST_MASK);
        }
    }

where

    MMAP_OFFSET = 0x44C00000
    MMAP_SIZE = 0x481AEFFF - MMAP_OFFSET
    GPIO_REGISTER_SIZE = 4
    MODULEMODE_ENABLE = 0x02
    IDLEST_MASK = (0x03 << 16)
    CM_WKUP = 0x44E00400
    CM_PER = 0x44E00000
    CM_WKUP_GPIO0_CLKCTRL = (CM_WKUP + 0x8)
    CM_PER_GPIO1_CLKCTRL = (CM_PER + 0xAC)
    CM_PER_GPIO2_CLKCTRL = (CM_PER + 0xB0)
    CM_PER_GPIO3_CLKCTRL = (CM_PER + 0xB4)

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

Planning committee / TODO
-------

+ **Need to compare the speed of the library with the speed of explicitly calling out the bits to change**

+ Restructure mapping systems:
    + Need to move maps into maps folder
    + Need to create a maps.py in maps folder
    + Need to restructure maps using ABCs so that arbitrary, non-included maps can be generated by users wishing to implement custom hardware
+ Automatic configuration and overlay creation during install
    + Is there a way to autodetect the hardware platform?
    + It would be nice to be able to say "with platform" instead of "with <platform>"
+ specify "plug" and have pins automatically declared 
    + ex: create SPI0 plug
    + include any possible onboard conflicts, like USB or HDMI
    + Should probably be implemented as a pinout generator class, that would also be useful as a way to generate layouts. If you're doing this with runtime code (instead of as a write-time code aid) it absolutely must be deterministic, or the configuration would be non-static and users would have to change their pinouts. Should there be a way to freeze the pinout?
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
* [Derek Molloy youtube channel](https://www.youtube.com/user/DerekMolloyDCU/videos)

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
* [TI wiki of PRU projects](http://processors.wiki.ti.com/index.php/PRU_Projects)
* [Element14 blog on PRU use](http://www.element14.com/community/community/designcenter/single-board-computers/next-gen_beaglebone/blog/2013/05/22/bbb--working-with-the-pru-icssprussv2)
* [PyPRUSS](http://hipstercircuits.com/pypruss-one-library-to-rule-them-all/)
* [Generic HAL PRU stuff](https://github.com/cdsteinkuehler/linuxcnc/blob/MachineKit-ubc/src/hal/drivers/hal_pru_generic/pru_generic.p#L135)

Changelog
=======

Don't even consider looking here until this hits at least alpha. There are too many changes much too quickly at this point; when I change the status to alpha that will signifiy that I'm moving the project to a point where it's not quite so dangerous to use.