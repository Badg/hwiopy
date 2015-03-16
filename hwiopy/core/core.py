''' Core / toplevel members of the hwiopy library. Everything here *should* be 
platform-independent.

LICENSING
-------------------------------------------------

hwiopy: A common API for hardware input/output access.
    Copyright (C) 2014-2015 Nicholas Badger
    badg@nickbadger.com
    nickbadger.com

    This library is free software; you can redistribute it and/or
    modify it under the terms of the GNU Lesser General Public
    License as published by the Free Software Foundation; either
    version 2.1 of the License, or (at your option) any later version.

    This library is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
    Lesser General Public License for more details.

    You should have received a copy of the GNU Lesser General Public
    License along with this library; if not, write to the Free Software
    Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301
    USA

------------------------------------------------------

A note on nomenclature: for clarity, I'm referring to anything on an SoC as 
a terminal, and everything on a device as a pin. I'm going to try to keep this
division as strict as possible, because I'm confused as balls over here 
already.

Will probably need to add a virtual terminal at some point? Or maybe the 
generic SoC defines terminals available in the fallback sysFS mappings? 
Or summat.

WILL NEED TO BE MADE THREADSAFE AT SOME POINT. THIS IS EXTREMELY DANGEROUS TO
RUN THREADED AT THE MOMENT.
'''

class Pin():
    ''' A generic single channel for communication on a device. Pins connect
    to the 'outside world'.

    '''
    def __init__(self, terminal, mode, methods=None, name=None, pin_num=None):
        # An optional, nice, human-readable name.
        self.name = name
        # What number does the datasheet assign the pin on the device header?
        self.num = pin_num
        # What mode the pin has been configured to. All Pin objects will have
        # a mode, since that's how the Pin is created.
        self.mode = mode
        # This may need to be removed and replaced with a function
        self.value = None
        # Which System terminal?
        self.terminal = terminal
        # Which system register? Note that not all systems will use this
        # Oh, and it's just a name, not the actual location.
        self.register_name = None

        # Dict for holding the pin's methods:
        if methods:
            # Need to always have on_start, on_stop, and config methods.
            # Pop them from the methods dict, or if they don't exist, create
            # them as empty lambdas.
            if 'on_start' not in methods:
                self.on_start = lambda: None
            else:
                self.on_start = methods.pop('on_start')
            if 'on_stop' not in methods:
                self.on_stop = lambda: None
            else:
                self.on_stop = methods.pop('on_stop')
            if 'config' not in methods:
                self.config = lambda: None
            else:
                self.config = methods.pop('config')
        else:
            methods = {}
        self.methods = methods

        # It might be nice to be able to use 
        #   with pin as pin:
        # You'd need to reference the system, because you'd have to start it
        # or else you'd lack any access to the memory. That would be tough 
        # for anything that modifies pin. Would just need to check against 
        # system.running and if not, then set self.standalone = True and call
        # system.on_start and then, in self.__exit__() call system.on_stop 
        # if self.standalone == True


        # For the purpose of fast updating, store the location?
        # It might be worthwhile to verify that this is in fact faster than
        # using locate(). Or I suppose both could be made available.
        # Deprecate?
        self.location = None

class Plug():
    ''' A base object for any multiple-pin interface, for example, SPI.
    '''
    def __init__(self):
        self.pins = {}

class System():
    ''' A base object for any computer system, be it SoC, desktop, whatever.

    Might want to subclass to mmapped system, then to cortex?
    '''
    def __init__(self, resolve_mode):
        self._resolve_mode = resolve_mode
        self.running = False

        # Set the conventions for memory reference dicts, which might not be
        # used for every SoC (but probably will?)
        # mem_filename is the file system location of the memory map
        self._mem_filename = None
        # callable that turns a register name into a (start, end) tuple:
        self._resolve_map = None
        # callable that turns a register type into an (offset, bitsize) tuple:
        self._resolve_register_bits = None

        # Where are mapped registers? Not all systems will use this
        self._register_mmaps = {}

        # Every terminal must be defined in terminal_modes
        # The keys in terminal_modes therefore provide the definition for
        # the terminals
        self.terminals = list(self._resolve_mode.list())

        # No keys have been declared to start. This dict is used to actually
        # set up the terminals with on_start and clean up with on_stop
        self.terminals_declared = {}

        # Add any declarable terminals to terminals_available
        self.terminals_available = \
            self._resolve_mode.list(only_assignable=True)

    def __enter__(self):
        self.on_start()
        return self

    def on_start(self, *args, **kwargs):
        ''' Must be called to start the device.
        '''
        self.running = True

    def __exit__(self, type, value, traceback):
        ''' Cleans up and handles errors.
        '''
        self.on_stop()

    def on_stop(self, *args, **kwargs):
        ''' Cleans up the started device.
        '''
        self.running = False

    def declare_linked_pin(self, terminal, mode):
        ''' Sets up the terminal for on_start initialization and returns a 
        pin object.
        '''
        # Error traps
        # --------------

        # Check to make sure that the terminal hasn't already been used
        if terminal in self.terminals_declared:
            raise AttributeError('Terminal has already been declared as a '
                'pin. Cannot re-declare a terminal after its initialization.')

        # Pin declaration
        # ---------------

        # Update declared terminals
        self.terminals_declared[terminal] = mode

        # Return the declared pin. If a system uses a mmap, it'll be handled 
        # in the child declare_linked_pin method
        return Pin(terminal, mode, 
            methods=self._resolve_mode(self, terminal, mode)())

    def release_terminal(self, terminal):
        ''' Releases a terminal, allowing re-declaration. Note: the device 
        must independently release its pin; if it calls the terminal once it's
        been released, an error will result. This is NOT for repurposing a
        terminal while the device is running.
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
        # I don't think the terminals_available bit was ever modified?
        # self.terminals_available[terminal] = True

    def mutate_terminal(self, *args, **kwargs):
        ''' Changes a terminal's function while the device it's attached to is 
        running. May or may not be overridden for each individual SoC. Only 
        use if you know what you're doing. Shouldn't be necessary for normal 
        operations.
        '''
        raise NotImplementedError('mutate_terminal must be defined for each '
            'individual SoC.')

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
        self.running = False

    def __enter__(self):
        self.on_start()
        return self

    def on_start(self):
        # This is separated out so that there is a start method that doesn't
        # return, which is useful for subclassing

        self.running = True

        # MUST call system on_start before pin on_start
        self.system.on_start()

        # Now start every pin
        for pin in self.pinout.values():
            pin.on_start()

    def __exit__(self, type, value, traceback):
        self.on_stop()

    def on_stop(self):
        # This is separated out so that there is a stop method that doesn't
        # return, which is useful for subclassing

        # MUST call pin on_stop before system on_stop
        for pin in self.pinout.values():
            pin.on_stop()

        self.system.on_stop()

        self.running = False

    def create_pin(self, pin_num, mode, name=None, **kwargs):
        # Need lots of error traps first
        # Check for existing pin at pin_num (note that this is a little 
        # redundant, since declare_linked_pin already checks for repeated 
        # terminal choice)
        if pin_num in self.pinout:
            raise ValueError('Pin ' + pin_num + ' has already been assigned.') 
        # Ensure a unique pin_name
        if name and name in self.pinout:
            raise ValueError('Choose a unique pin name.')

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