''' Core / toplevel members of the hwiopy library. Everything here *should* be 
platform-independent.

'''

class device():
    ''' A generic IO device -- not a platform, but an entity

    For example, I could set up arbitrary communications with an LED as a 
    device.
    '''
    def __init__(self, platform):
        pass

class pin():
    ''' A generic single channel for communication. 

    '''
    def __init__(self, mode=None):
        self.mode = mode

class device():
    ''' A base object for a generic hardware-inspecific device. Will probably,
    at some point, provide a graceful fallback to sysfs access.

    Something something sooooomething goes here.
    '''
    def __init__(self, pinmap={}):
        self.pinmap = pinmap

    def __enter__(self):
        pass

    def __exit__(self, type, value, traceback):
        pass

class plug():
    ''' A base object for any multiple-pin interface, for example, SPI.
    '''
    def __init__(self):
        self.pins = {}

class chipset():
    ''' A base object for any chipset.

    Contains a pinout, which is a dict that takes ['<pinname>'] and yields a
    dict with keys ['pin', 'name', 'modes']
    '''
    def __init__(self, pin_modes={}, mem_map={}):
        self.pin_modes = pin_modes
        self.memmap = mem_map