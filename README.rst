hwiopy
======

Hardware IO for SOCs in python, starting with Beaglebone Black.

Introduction
----------

Preface to the introduction: oh god don't look at the source code it's dirty and needs to be put out of its misery (like seriously, complete rewrite).

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

You should *not* install as sudo, but the installer *may* prompt you to escalate privileges. This has been done as a compromise between ameliorating potential downstream access risks and automating processes like device tree overlay compiling.

Notes on pinmuxing
---------------

The pip install process currently generates (but does not correctly locate, nor activate) device tree overlays for muxing. Unfortunately this will only apply to kernel 3.8, as it appears that future kernel versions do **not** support runtime modification of the device tree (so pin configuration may require reboot). As such, **pinmuxing is only currently planned for kernel version 3.8. I would like to support muxing in other kernel versions, but unfortunately I don't have the resources at the moment.** Insert some grumbling here (I've spent a lot of time on this problem and made exceptionally little progress).

Table 9-57 has control module information for pinmuxing. Section 9.1 explains what the fuck is going on.

**If you want to disable the HDMI functions to free up the HDMI pins,** you need to manually:

    sudo nano /boot/uEnv.txt

then append the line:

    optargs=capemgr.disable_partno=BB-BONELT-HDMI,BB-BONELT-HDMIN

Ctrl+X to exit, Y to save, Enter to overwrite, then reboot and verify:

    sudo reboot
    (wait and reconnect)
    cat /sys/devices/bone_capemgr.?/slots

You should see "ff:P-O--" in front of anything mentioning HDMI. The lack of an l (for loading) or L (for Loaded) indicates that these capes have not been loaded. Attempting to disable them after boot (at least for me) results in kernel panic and hang.

Features and changelog
========

| function | support level |
| ----- |   ----- |
| gpio | Input supported. Output supported. Interrupts unsupported. |

* 0.1.1 -- Pip installable. No need for user to deal with SysFS. Supports only GPxO (no input yet).
* 0.1.2 -- Added input support. GPIO interrupt generation still unsupported.

Scratchbook
===========

**You will take a significant performance hit if you try to access functions via the pin dictionary. Memoize them, then call that:**

    fastup = test_led.methods['output_high_nocheck']
    fastdown = test_led.methods['output_low_nocheck']

Could probably speed things up a bit more by using lambdas with default arguments and stuff.

Gotchas
-----

If you're used to, for example, the adafruit library: you have no need to run the sysfs export command. Hwiopy does this for you, in a more performant manner.

Memory mapping
------------

The ARM cortex A8 TRM, BBB SRM, and a datasheet or two are in /doc. I realize that it's not necessarily the best practice to include those in the git repo, but the links to them online seem to have been a little less static than would otherwise be desirable, making them difficult to link to. I'd rather unambiguously and conveniently include them here. That said, the json files in the source code are likely to be more helpful.

Planning committee / TODO
-------

+ Whole damn package needs a rewrite. It's very, very messy. I'm waiting until after I have SPI working to do this.
+ Package restructure.
    + The api to a map should be either a single dictionary, or a single wrapper therefore.
    + Should have a single json file for the cortex, single file for the sitara, single file for the beaglebone, etc.
    + Creation of custom devices should be as easy as creating a dictionary to describe them.
+ Use platform autodetection to set a configuration file, which in turn makes the device creation portable between platforms (ex: with platform as myplatform instead of with BBB as myplatform)
+ Similarly, ability to say "I need a gpio", "I need a SPI", etc, and the device responds by creating one and telling you the appropriate pinout.
    + Internal integer description of each pin, to allow code ported from another device to auto-generate a pinout for the new device.
    + Needs to be deterministic, or to have a way to freeze the pinout, so that for any set of requirements on any given device, the same pinout will **always** be generated.
    + A method to save the device description somewhere.
+ Software-defined interfaces (ex software-defined PWM via GPIO).

Preliminary work and performance research
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


Links
=======

General
---------

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
* [libpruio](http://beagleboard.org/project/libpruio/)