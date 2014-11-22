hwiopy
======

Hardware IO for SOCs in python, starting with Beaglebone Black.

Introduction
----------

First, sorry (seriously sorry) but for the time being, the documentation here is going to be narsty. Not *lacking*, but more of a "brain dump" than an explanation. So it may only be helpful to me. But, uh, better than nothing? Probably? I wish I had time (or the resources to hire someone to document my shit) but at this point I'm just stretched too thinly. Butter over too much bread and all that. Speaking of which, this is being developed on python 3.4 with no intention of supporting python 2.

All that said: the purpose of this library is to develop a standard platform-independent API for platform-dependent hardware access, in the spirit of Kivy and Plyer. At the moment I'm developing for beaglebone black, with Raspi in the back of my head as another possible target. Ideally I'd like to make the library as simple to use as "write [value] to [pin]". All in due time.

Special thanks to [Tabula](http://tabula.technology/) for help with datasheet table processing.

Scratchbook
===========

All (period?) io is being done through writing to sysfs. Need to sudo (or chmod) /sys/class. Adafruit library uses this through c++ wrapper. Could entirely circumvent with own python library, which would probably be best case. Have verified file writing works with sudo echo 1 > /sys/class/leds/beaglebone:green:usr0/brightness (may need to sudo su). 

Can also map pins to /dev/mem using mmap? This would be a possible route for improvement. Not 100% sure how to deal with pinmuxing -- perhaps mux with the /sys/ mappings -- but theoretically possible within /dev/mem as well. [Check this out.](http://chiragnagpal.com/examples.html)

I compared IO for the simple /sys/ mappings was between numpy and the stock io libraries. Stock io was significantly faster, roughly 3x. Timing using:

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

Memory mapping
------------

This comes from the ARM cortex A8 TRM, starting around page 175.

Map:

* DMTIMER0 0x44E0_5000 0x44E0_5FFF 4KB DMTimer0 Registers
* GPIO0 0x44E0_7000 0x44E0_7FFF 4KB GPIO Registers
* UART0 0x44E0_9000 0x44E0_9FFF 4KB UART Registers
* I2C0 0x44E0_B000 0x44E0_BFFF 4KB I2C Registers
* ADC_TSC 0x44E0_D000 0x44E0_EFFF 8KB ADC_TSC Registers
* DMTIMER1_1MS 0x44E3_1000 0x44E3_1FFF 4KB DMTimer1 1ms Registers
* RTCSS 0x44E3_E000 0x44E3_EFFF 4KB RTC Registers
* UART1 0x4802_2000 0x4802_2FFF 4KB UART1 Registers
* UART2 0x4802_4000 0x4802_4FFF 4KB UART2 Registers
* I2C1 0x4802_A000 0x4802_AFFF 4KB I2C1 Registers
* McSPI0 0x4803_0000 0x4803_0FFF 4KB McSPI0 Registers
* DMTIMER2 0x4804_0000 0x4804_0FFF 4KB DMTimer2 Registers
* DMTIMER3 0x4804_2000 0x4804_2FFF 4KB DMTimer3 Registers
* DMTIMER4 0x4804_4000 0x4804_4FFF 4KB DMTimer4 Registers
* DMTIMER5 0x4804_6000 0x4804_6FFF 4KB DMTimer5 Registers
* DMTIMER6 0x4804_8000 0x4804_8FFF 4KB DMTimer6 Registers
* DMTIMER7 0x4804_A000 0x4804_AFFF 4KB DMTimer7 Registers
* GPIO1 0x4804_C000 0x4804_CFFF 4KB GPIO1 Registers
* MMCHS0 0x4806_0000 0x4806_0FFF 4KB MMCHS0 Registers
* I2C2 0x4819_C000 0x4819_CFFF 4KB I2C2 Registers
* McSPI1 0x481A_0000 0x481A_0FFF 4KB McSPI1 Registers
* UART3 0x481A_6000 0x481A_6FFF 4KB UART3 Registers
* UART4 0x481A_8000 0x481A_8FFF 4KB UART4 Registers
* UART5 0x481A_A000 0x481A_AFFF 4KB UART5 Registers
* GPIO2 0x481A_C000 0x481A_CFFF 4KB GPIO2 Registers
* GPIO3 0x481A_E000 0x481A_EFFF 4KB GPIO3 Registers
* DCAN0 0x481C_C000 0x481C_DFFF 8KB DCAN0 Registers
* DCAN1 0x481D_0000 0x481D_1FFF 8KB DCAN1 Registers
* INTCPS 0x4820_0000 0x4820_0FFF 4KB Interrupt Controller Registers
* PRU_ICSS 0x4A30_0000 0x4A37_FFFF 512KB PRU-ICSS Instruction/Data/Control Space
* LCD Controller 0x4830_E000 0x4830_EFFF 4KB LCD Registers
* 

PWM (each 4KB total):

* PWM Subsystem 0 0x4830_0000 0x4830_00FF PWMSS0 Configuration Registers
    * eCAP0 0x4830_0100 0x4830_017F PWMSS eCAP0 Registers
    * eQEP0 0x4830_0180 0x4830_01FF PWMSS eQEP0 Registers
    * ePWM0 0x4830_0200 0x4830_025F PWMSS ePWM0 Registers
* PWM Subsystem 1 0x4830_2000 0x4830_20FF PWMSS1 Configuration Registers
    * eCAP1 0x4830_2100 0x4830_217F PWMSS eCAP1 Registers
    * eQEP1 0x4830_2180 0x4830_21FF PWMSS eQEP1 Registers
    * ePWM1 0x4830_2200 0x4830_225F PWMSS ePWM1 Registers
* PWM Subsystem 2 0x4830_4000 0x4830_40FF PWMSS2 Configuration Registers
    * eCAP2 0x4830_4100 0x4830_417F PWMSS eCAP2 Registers
    * eQEP2 0x4830_4180 0x4830_41FF PWMSS eQEP2 Registers
    * ePWM2 0x4830_4200 0x4830_425F PWMSS ePWM2 Registers

GPIO registers: page 4871

When setting the datain / dataout bits, remember that each GPIO register has one bit per GPIO. So in other words, if you wanted to set the 1 bit for gpioX_5, you'd need to set

    0000100000...

BBB Pinout
---------

See the .json

Planning committee
-------

+ Need to reorganize .json files
    + modes_available
+ Need to add chipset class

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

Installation
===========

Cannibalize the Adafruit library. Seriously. After a little finagling (one of my other repos, look for a fork of the Adafruit library with a python3 branch) I installed it into a py=3.4 virtualenv using 

```
sudo /path/to/clone setup.py install
```
  
then stole the compiled .so libraries:

```
sudo mkdir /usr/local/lib/hwio
sudo cp /path/to/dir/ADC.cpython.34.so /usr/local/lib/hwio/adc_py34.so
```

(etc), and don't forget to verify path:

'''
echo $LD_LIBRARY_PATH
'''

and then, if missing, 

'''
export LD_LIBRARY_PATH=/usr/local/lib:/usr/lib:$LD_LIBRARY_PATH
'''

and finally to allow access to the libraries (don't actually do it this way):

'''
sudo chmod 777 /usr/local/lib/hwio/*
'''

then cloned this repo:

```
git clone https://github.com/Badg/hwiopy.git ~/hwiopy
cd ~/hwiopy
```

More when I actually get it working and shit.
