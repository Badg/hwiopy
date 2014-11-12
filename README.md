hwiopy
======

Hardware IO for SOCs in python, starting with Beaglebone Black.

Introduction
--------

First, sorry (seriously sorry) but for the time being, the documentation here is going to be narsty. Not *lacking*, but more of a "brain dump" than an explanation. So it may only be helpful to me. But, uh, better than nothing? Probably? I wish I had time (or the resources to hire someone to document my shit) but at this point I'm just stretched too thinly. Butter over too much bread and all that.

Installation
--------

Cannibalize the Adafruit library. Seriously. I installed it into a py=2.7 virtualenv using 

```
sudo ~/.virtualenvs/python27/bin/pip install Adafruit_BBIO
```
  
then stole the compiled .so libraries:

```
sudo mkdir /usr/local/lib/hwio
sudo cp ~/.virtualenvs/python27/lib/python2.7/site-packages/Adafruit_BBIO/ADC.so /usr/local/lib/hwio/adc.so
sudo cp ~/.virtualenvs/python27/lib/python2.7/site-packages/Adafruit_BBIO/GPIO.so /usr/local/lib/hwio/gpio.so
sudo cp ~/.virtualenvs/python27/lib/python2.7/site-packages/Adafruit_BBIO/PWM.so /usr/local/lib/hwio/pwm.so
sudo cp ~/.virtualenvs/python27/lib/python2.7/site-packages/Adafruit_BBIO/SPI.so /usr/local/lib/hwio/spi.so
sudo cp ~/.virtualenvs/python27/lib/python2.7/site-packages/Adafruit_BBIO/UART.so /usr/local/lib/hwio/uwart.so'''
```

then cloned this repo:

```
git clone https://github.com/Badg/hwiopy.git ~/hwiopy
cd ~/hwiopy
```

More when I actually get it working and shit.
