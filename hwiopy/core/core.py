''' Core / toplevel members of the hwiopy library. Everything here *should* be 
platform-independent.

A note on nomenclature: for clarity, I'm referring to anything on an SoC as 
a terminal, and everything on a device as a pin. I'm going to try to keep this
division as strict as possible, because I'm confused as balls over here 
already.

Will probably need to add a virtual terminal at some point? Or maybe the 
generic SoC defines terminals available in the fallback sysFS mappings? 
Or summat.
'''

class device():
    ''' A base object for a generic hardware-inspecific device. Will probably,
    at some point, provide a graceful fallback to sysfs access.

    ### kwargs:

    pinmap:         dict        [pin name] = core.pin object, subclass, etc

    ### Conventional subclass kwargs:

    chipset:        object      core.soc, subclass, etc
    '''
    def __init__(self, pinmap):

        self.pinmap = pinmap
        self.chipset = None

    def __enter__(self):
        pass

    def __exit__(self, type, value, traceback):
        pass

class pin():
    ''' A generic single channel for communication on a *device*.

    '''
    def __init__(self, terminal, mode, name=None):
        self.name = name
        self.mode = mode
        self.value = None
        # Connection describes the processor pin
        self.terminal = terminal

    def update(self):
        ''' Update output for output pin, or input for input pin.
        '''
        pass

    def status(self):
        ''' Check output for output pin. Does (same as update?) for input pin.
        '''
        pass

class plug():
    ''' A base object for any multiple-pin interface, for example, SPI.
    '''
    def __init__(self):
        self.pins = {}

class soc():
    ''' A base object for any system-on-a-chip.
    '''
    def __init__(self, terminal_modes):
        self.terminal_modes = terminal_modes
        self.running = False

        # Set the conventions for memory reference dicts, which might not be
        # used for every SoC (but probably will?)
        # mem_filename is the file system location of the memory map
        self.mem_filename = None
        # mem_mapping describes which registers are where, ex the 4KB GPIO1 
        # register is at 0x??????
        self.mem_mapping = None
        # The register_bits describe which bits correspond to what within each
        # type of register, ex the gpio config is offset 0x154 and to set the
        # idle mode you change bits 3-4
        self.register_bits = None

        # Every terminal must be defined in terminal_modes
        # The keys in terminal_modes therefore provide the definition for
        # the terminals
        self.terminals = list(terminal_modes)

        # No keys have been declared to start. This dict is used to actually
        # set up the terminals with on_start and clean up with on_stop
        self.terminals_declared = {}

        # Add any declarable terminals to terminals_available
        self.terminals_available = {}
        # Inspect each terminal_mode to make sure it's declarable
        for sys_name, sys_term in self.terminal_modes.items():
            # Predeclare a lookup flag
            terminal_available = False
            # Look into the sys_term dict at each mode defined in 'modes'
            for mode in sys_term['modes'].values():
                # If the 'mode_num' is defined, we can declare it as a mode
                if mode['mode_num']:
                    terminal_available = True
            # If the terminal is available, declare it as such.
            self.terminals_available[sys_name] = terminal_available

    def declare_linked_pin(self, terminal, mode):
        ''' Sets up the terminal for on_start initialization and returns a 
        pin object.
        '''
        # Error traps
        # --------------

        # First make sure terminal_modes exists and has content.
        if not self.terminal_modes:
            raise AttributeError('Available terminal modes must be specified '
                'prior to declaring a pin.')

        # Now make sure the terminal name is valid:
        if terminal not in self.terminal_modes:
            raise AttributeError('Invalid terminal name.')

        # Now check to make sure the mode is valid:
        if mode not in self.terminal_modes[terminal]['modes']:
            possible_modes = list(
                self.terminal_modes[terminal]['modes'].values())
            raise KeyError('Invalid mode type. Current terminal may have the '
                'following modes: \n' + possible_modes)

        # Now check to make sure that the terminal hasn't already been used
        if terminal in self.terminals_declared:
            raise AttributeError('Terminal has already been declared as a '
                'pin. Cannot re-declare a terminal after its initialization.')

        # Pin declaration
        # ---------------

        self.terminals_declared[terminal] = mode
        return pin(terminal, mode)
        # Note that now the chipset must create update, status, etc methods

    def release_terminal(self, terminal):
        ''' Releases a terminal, allowing re-declaration. Note: the device 
        must independently release its pin; if it calls the terminal once it's
        been released, an error will result.
        '''
        # Error traps
        # --------

        # Cannot release a pin connected to an SoC that is currently running
        if self.running == True:
            raise RuntimeError('Cannot release a terminal while running.')
        # Can't release a terminal that hasn't been declared
        if terminal not in self.terminals_declared:
            raise KeyError('Cannot release an undeclared terminal.')

        # Meat and bones
        # ------------

        del self.terminals_declared[terminal]
        self.terminals_available[terminal] = True

    def mutate_terminal(self, *args, **kwargs):
        ''' Changes a terminal's function while the device it's attached to is 
        running. May or may not be overridden for each individual SoC. Only 
        use if you know what you're doing. Shouldn't be necessary for normal 
        operations.
        '''
        raise NotImplementedError('mutate_terminal must be defined for each '
            'individual SoC.')

    def __enter__(self):
        self.on_start()

    def __exit__(self, type, value, traceback):
        self.on_stop()

    def on_start(self, *args, **kwargs):
        ''' Must be called to start the device.
        '''
        self.running = True
        for term, mode in self.terminals_declared.items():
            self._setup_term(term, mode)

    def on_stop(self, *args, **kwargs):
        ''' Cleans up the started device.
        '''
        for term, mode in self.terminals_declared.items():
            self._unsetup_term(term, mode)
        self.running = False

    def _setup_term(self, *args, **kwargs):
        ''' Gets the terminal ready for use. Handles muxing, mode select, etc. 

        MUST be overridden for each individual SoC that needs to be set up.
        '''
        pass

    def _unsetup_term(self, *args, **kwargs):
        ''' If anything needs to be released before a new call to _setup_term,
        this is the place to do it.

        MUST be overridden for each individual SoC that needs its terminals to 
        be released after use.
        '''
        pass