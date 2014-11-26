''' Core / toplevel members of the hwiopy library. Everything here *should* be 
platform-independent.

'''

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

class device_pin():
    ''' A generic single channel for communication. 

    '''
    def __init__(self, name=None, mode=None):
        self.name = name
        self.mode = mode

class device_plug():
    ''' A base object for any multiple-pin interface, for example, SPI.
    '''
    def __init__(self):
        self.pins = {}

class soc():
    ''' A base object for any system-on-a-chip.

    Contains a pinout, which is a dict that takes ['<pinname>'] and yields a
    dict with keys ['pin', 'name', 'modes']
    '''
    def __init__(self, pin_modes_all, mem_map={}, registers={}, 
            mem_filename=None):
        self.pin_modes_all = pin_modes_all
        self.mem_map = mem_map
        self.mem_filename = mem_filename
        self.registers = registers

        # Every pin must be defined in pin_modes_available; use keys as pins.
        self.pins = list(pin_modes_all)
        # No keys have been declared to start.
        self.pins_declared = {}

        # Add any declarable pins to pins_available
        self.pins_available = {}
        # Inspect each pin_mode_available to make sure it's declarable
        for sys_name, sys_pin in self.pin_modes_all.items():
            # Predeclare a lookup flag
            pin_available = False
            # Look into the sys_pin dict at each mode defined in 'modes'
            for mode in sys_pin['modes'].values():
                # If the 'mode_num' is defined, we can declare it as a mode
                if mode['mode_num']:
                    pin_available = True
            # If the pin is available, declare it as such.
            if pin_available:
                self.pins_available[sys_name]

    def declare_pin(self, pin_name, pin_to_declare):
        ''' Creates a pin object in the chipset, checking it for validity.

        pin_to_declare must be of type soc_pin, and the soc_pin device must be
        the same object as the pin being declared.
        '''
        # Error traps
        # --------------

        # First make sure pin_modes_available exists and has content.
        if not pin_modes_all:
            raise AttributeError('Available pin modes must be specified '
                'prior to declaring a pin.')

        # Now make sure the pin name is valid:
        if pin_name not in self.pin_modes_all:
            raise AttributeError('Invalid pin name.')

        # Now check to make sure the mode is valid:
        if pin.mode not in self.pin_modes_all[pin_name]['modes']:
            possible_modes = list(
                self.pin_modes_all[pin_name]['modes'].values())
            raise KeyError('Invalid mode type. Current pin may have the '
                'following modes: \n' + possible_modes)

        # Now check to make sure that pin hasn't already been declared
        if pin_name in self.pins_declared:
            raise AttributeError('Pin has already been declared. Cannot '
                're-declare pins after pin initialization.')

        # Pin declaration
        # ---------------

        self.pins_declared[pin_name] = pin_to_declare

    def __enter__(self):
        self.on_start()

    def __exit__(self, type, value, traceback):
        self.on_stop()

    def on_start():
        ''' Must be called to start the device.
        '''
        pass

    def on_stop():
        ''' Cleans up the started device.
        '''
        pass

class soc_pin():
    ''' A generic single pin on a SoC. Meant to be used programmatically and 
    may not be renamed to something user-friendly.

    '''
    def __init__(self, sys_name, soc, mode=None):
        self._mode = None
        self.soc = soc
        self.sys_name = sys_name

        if mode:
            self.set_mode(mode)

    def set_mode(mode):
