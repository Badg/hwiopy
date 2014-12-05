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

class Pin():
    ''' A generic single channel for communication on a device. Pins connect
    to the 'outside world'.

    '''
    def __init__(self, terminal, mode, name=None, pin_num=None):
        # An optional, nice, human-readable name.
        self.name = name
        # What number does the datasheet assign the pin on the device header?
        self.num = pin_num
        # What mode the pin has been configured to. All Pin objects will have
        # a mode, since that's how the Pin is created.
        self.mode = mode
        # This may need to be removed and replaced with a function
        self.value = None
        # Which SoC terminal?
        self.terminal = terminal
        # For the purpose of fast updating, store the location?
        # It might be worthwhile to verify that this is in fact faster than
        # using locate(). Or I suppose both could be made available.
        self.location = None

    def locate(self):
        ''' Returns the filesystem/mmap/etc representation of the pin.
        '''
        pass

    def update(self):
        ''' Update output for output pin, or input for input pin.
        '''
        pass

    def status(self):
        ''' Check output for output pin. Does (same as update?) for input pin.
        '''
        pass

    def setup(self):
        ''' Things to do to set up the pin when a core.Device is __enter__ed.
        '''
        pass

class Plug():
    ''' A base object for any multiple-pin interface, for example, SPI.
    '''
    def __init__(self):
        self.pins = {}

class System():
    ''' A base object for any computer system, be it SoC, desktop, whatever.
    '''
    def __init__(self, terminal_modes):
        self.terminal_modes = terminal_modes
        self.running = False

        # Set the conventions for memory reference dicts, which might not be
        # used for every SoC (but probably will?)
        # mem_filename is the file system location of the memory map
        self._mem_filename = None
        # callable that turns a register name into a (start, end) tuple:
        self._resolve_map = None
        # callable that turns a register type into an (offset, bitsize) tuple:
        self._resolve_register_bits = None

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

class Device():
    ''' A base object for a generic hardware-inspecific device. Will probably,
    at some point, provide a graceful fallback to sysfs access.

    __init()__
    =========================================================================
    
    **kwargs
    ----------------------------------------------------------------

    resolve_header: callable    takes str pin_num and returns str term_num
    system          object      core.system, subclass, etc

    local namespace (self.XXXX; use for subclassing)
    ----------------------------------------------------------------

    pinout          dict        [pin name] = core.pin object, subclass, etc
    system          object      core.system, subclass, etc
    _resolve_header callable    resolves a pin into a header   
    create_pin      callable    connects a header pin to a specific term mode

    create_pin()
    =========================================================================

    Connects a header pin to the specified mode on the corresponding system 
    terminal. Likely overridden in each platform definition. 

    *args
    ----------------------------------------------------------------

    pin_num         str         'pin number'
    mode            str         'mode of SoC terminal'

    **kwargs
    ----------------------------------------------------------------

    name=None       str         'friendly name for the pin'
    '''
    def __init__(self, system, resolve_header):

        self._resolve_header = resolve_header
        self.system = system
        self.pinout = {}
        self.pins_available = self._resolve_header.list_system_headers()

    def __enter__(self):
        pass

    def __exit__(self, type, value, traceback):
        pass

    def create_pin(self, pin_num, mode, name=None, **kwargs):
        # Need lots of error traps first
        terminal = self._resolve_header(pin_num)
        pin = self.system.declare_linked_pin(terminal, mode, name=name)
        pin.num = pin_num

        # Check for a given 'pretty' name. If it has one, add both the pin
        # number and the pin name as keys in the pinout dict. Note that as
        # pin is a mutable object, as long as pin itself isn't re-declared,
        # pinout[name] is pinout[number] will always -> True.
        if name:
            self.pinout[pin.name] = pin
        self.pinout[pin_num] = pin

    def release_pin(self, pin):
        ''' Releases the called pin. Can be called by friendly name or pin
        number.
        '''

        # Get relevant information from the pin before deleting it
        pin = self.pinout[pin]
        name = pin.name
        num = pin.num
        terminal = pin.terminal

        # Remove all associated keys in the pinout
        if name:
            try:
                del self.pinout[name]
            except KeyError:
                pass
        if num:
            try:
                del self.pinout[num]
            except KeyError:
                pass

        # Finally, call the system's function to release the terminal
        self.system.release_terminal(terminal)