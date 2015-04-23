''' Core / toplevel members of the hwiopy library. Everything here 
*should* be platform-independent.

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
    License along with this library; if not, write to the 
    Free Software Foundation, Inc.,
    51 Franklin Street, 
    Fifth Floor, 
    Boston, MA  02110-1301 USA

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

# Global imports
from warnings import warn
from abc import ABCMeta, abstractmethod

# Package dependencies
from platforms import BBB

# class Pin(metaclass=ABCMeta):
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

class System(metaclass=ABCMeta):
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

    @abstractmethod
    def __enter__(self):
        self.on_start()
        return self

    @abstractmethod
    def __exit__(self, type, value, traceback):
        ''' Cleans up and handles errors.
        '''
        self.on_stop()

    @abstractmethod
    def on_start(self, *args, **kwargs):
        ''' Must be called to start the device.
        '''
        self.running = True

    @abstractmethod
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

class SystemBase(Runnable):
    ''' A base object for a system. This isn't the whole computer -- for 
    example, in an SBC this would be just the SoC. I'm not sure what this would
    correspond to on a desktop or an emulator.
    
    In general, this is where the meat for things is at. All memory operations
    should be performed here. HardwareBase is really just configuring the 
    entire computer in a way that reflects the current hardware state of the 
    system.
    '''
    def __init__(self):
        self._running = False
        self.setup()
        
    @abstractmethod
    def setup(self):
        ''' Performs any setup needed during __init__. Should be called only 
        once, and not used again. Cannot be used for manipulation of the system
        while it is running.
        
        Note that this should NOT be used for implementation details. It should
        be for hardware configuration only.
        '''
        pass

    @abstractmethod
    def on_start(self, *args, **kwargs):
        ''' Must be called to start the device.
        '''
        self._running = True

    @abstractmethod
    def on_stop(self, *args, **kwargs):
        ''' Cleans up the started device.
        '''
        self._running = False
        
    @property
    def running(self):
        ''' Read-only property that describes the device state (can be running
        or not running: True/False)
        '''
        return self._running

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
    
class HardwareBase(Runnable):
    ''' Abstract base class for the whole computer (or other hardware 
    configuration). Generally speaking, maps the system definitions (for 
    example, SoC ZCZ balls) to your physical hardware configuration (for 
    example, the Beaglebone Black headers).

    Should this use on_start and on_stop as a way for the device to be used 
    outside of a with: block?
    '''
    def __init__(self, system):
        ''' Handles initialization. Here, will at least store the system in 
        self.
        '''
        # Make sure it is, in fact, a system.
        # "Errors should never pass silently" I think, in this case, trumps
        # "ask forgiveness, not permission"
        if not isinstance(system, SystemBase):
            raise TypeError('System must be a hwiopy system.')
        
        self._system = system
        
    @abstractmethod
    def declare_pin(self, pin, mode):
        ''' Initializes the specified pin to the specified mode.
        
        should pin be a pin object, or a name?
        '''
        pass
        
    @abstractmethod
    def request_pin(self, mode):
        ''' Gets the "best" available pin for that mode, declares it, and 
        returns it.
        '''
        
    @abstractmethod
    def release_pin(self, pin):
        ''' Removes any declaration at the specified pin.
        '''
        pass
        
    @property
    @abstractmethod
    def pins(self):
        ''' Read-only property that describes the current pin declarations.
        '''
        pass
        
    @property
    def system(self):
        ''' Read-only property describing the hardware's system, which is 
        assigned during init.
        '''
        return self._system
        

class _UndetectedHardware():
    ''' Exists for the sole purpose of preventing the use of DetectedHardware
    when the hardware was not autodetected.
    '''
    def __init__(self):
        raise RuntimeError('Hardware was not autodetected during install. If '
                           'you\'re running a system that should have been '
                           'detected, try reinstalling the package.')


# This bit is used for DetectedHardware to know where it inherits from.
_detected_hardware = _UndetectedHardware
if False:
    _detected_hardware = BBB

# DetectedHardware directly and only wraps the class for whatever hardware 
# platform was detected.
class DetectedHardware(_detected_hardware):
    ''' Use the hardware that was autodetected during pip install. If the 
    hardware could not be detected, immediately raises RuntimeError, thanks to
    _UndetectedHardware.
    '''
    pass


class PairedKeyDict():
    ''' Parallel dictionary supporting bi-directional lookup between a device's
    pin naming scheme and an arbitrary hwiopy-internal integer description of 
    its pins.

    pinmapper['name'] -> internal pin number
    pinmapper[internal pin number] - > 'name'
    pinmapper(<either>) -> SoC terminal mapping

    The idea is to very easily generate device new device descriptions for a
    given SoC, as well as provide a super simple way to get the SoC terminal.

    Might add a "user_name" field that supports arbitrary anything, so that
    someone might, for example, call "P8_7" on the beaglebone "test_pin".
    '''
    def __init__(self, pin_names=None, pin_connections=None, mapping=None):
        '''
        pin_names is an ordered list of names.
        pin_connections is also an ordered list.
        mapping is a dict.

        Why the weird construct? Because I can't totally guarantee the 
        consistency of a dictionary's order.

        Integer-based addressing is awkward. I should probably resort to hash
        addressing.
        '''
        # First call super
        super().__init__()

        # Store mapping on the off chance it's useful later
        self._mapping = mapping

        # Now, the internal address.
        # Why the extra list instead of just using the index? Well, because we
        # might decide that this isn't just being ordered by int. Also, because
        # pin addresses should always, always be static, and therefore deleting
        # one shouldn't change the address.
        self._addresses = []
        self._names = []
        self._connections = []

        # Maintain cumulative address number.
        self._address_state = 0

        # Flow control: is this predefined, or are we building a description?
        if (pin_names and pin_connections) and not mapping:
            # Some error traps
            if len(pin_names) != len(pin_connections):
                raise ValueError('Every pin name must have a connection.')
            if len(pin_names) != len(set(pin_names)):
                raise ValueError('Cannot overload pin names.')
            for name in pin_names:
                if not isinstance(name, str):
                    raise TypeError('Pin names must be (or subclass) strings.')
            for conn in pin_connections:
                if not isinstance(conn, str):
                    raise TypeError('Pin connections must be (or subclass) '
                                    'strings.')
            # Generate a list of addresses numbered one to whatever.
            self._addresses = list(range(len(pin_names)))
            self._names = pin_names
            self._connections = pin_connections
            self._address_state += len(pin_names) - 1

        # Improper construction
        elif (pin_names or pin_connections) and not mapping:
            raise ValueError('Cannot declare pin mappings without BOTH names '
                             'and connections.')
        
        # pin_names for ordering, mapping for description
        elif pin_names and mapping:
            if not set(pin_names).issubset(set(mapping)):
                raise ValueError('When using names to specify order and '
                                 'mapping to declare connections, names must '
                                 'be a subset of mapping.')
            # And now, create addresses, names, and connections for the mapping
            for ii in range(len(pin_names)):
                self._addresses.append(ii)
                self._names.append(pin_names[ii])
                self._connections.append(pin_connections[pin_names[ii]])
                self._address_state += 1

        # Just a mapping, thanks
        elif mapping:
            # This... well, it's a bit awkward.
            ii = 0
            for key, value in mapping.items():
                if not isinstance(key, str):
                    raise TypeError('Pin names must be (or subclass) strings.')
                if not isinstance(value, str):
                    raise TypeError('Pin connections must be (or subclass) '
                                    'strings.')
                self._connections.append(value)
                self._names.append(key)
                self._addresses.append(ii)
                self._address_state += 1
                ii += 1
            del ii

        # Improper construction, since only pin_connections
        elif pin_connections:
            raise ValueError('Cannot specify only pin connections.')

        # Empty.
        else:
            # Already handled above.
            pass

    def __call__(self, key):
        index = self._getindex(key)
        return self._connections[index]

    def __getitem__(self, key):
        # Get the index and handle errors.
        index = self._getindex(key)

        # This is a bit weird but whatever (trying to use boilerplate getindex)
        if self._names[index] == key:
            return self._addresses[index]
        else:
            return self._names[index]

    def __setitem__(self, name, connection):
        ''' Creates a new mapping. Sets the name <-> connection, assigns an 
        address.
        '''
        # Gets the new address, then sets it in the lists.
        new_address = self._address_state + 1
        # Onwards
        self._names.append(name)
        self._connections.append(connection)
        self._addresses.append(new_address)
        self._address_state += 1

    def __delitem__(self, key):
        index = self._getindex(key)
        del self._names[index]
        del self._connections[index]
        del self._addresses[index]

    def _getindex(self, key):
        ''' Gets the index of the internal lists for the corresponding name or
        address.
        '''
        if key in self._names:
            return self._names.index(key)
        elif key in self._addresses:
            return self._addresses.index(key)
        else:
            raise KeyError('The key was found in neither names nor addresses.')


class PinBase(Runnable):
    ''' An abstract base class for all pin objects, regardless of function. 
    
    Should always call self.setup.
    '''
    def __init__(self):
        self.setup()
        self._running = False
        
    @abstractmethod
    def setup(self):
        ''' Any actions needed to perform to set up the pin. This method should
        be called once, at initialization. It should **not** be used to 
        configure the pin after a device has started.
        '''
        pass

    @abstractmethod
    def release(self):
        ''' Performs any cleanup needed to un-setup the pin and return the pin
        to its previous state.
        '''
        pass

    @abstractmethod
    def config(self):
        ''' Performs configuration steps for the pin. May be called while 
        device is running.
        '''
        pass
        
    @abstractmethod
    def __call__(self):
        ''' The default pin behavior. For example, PWM might __call__(50%) for
        a 50% duty cycle. GPIO might __call__(1) to output high, or __call__()
        to read. This is a post-configuration "route of least resistance" way
        to interact with the pin.
        '''
        pass
        
        
class Runnable(metaclass=ABCMeta):
    ''' An abstract base class for anything that can be run in the
    hwiopy package. Subclasses must implement on_start, on_stop, and are
    guaranteed to have a read-only self.running property.
    
    As a convenience, the on_start and on_stop methods have been given
    bindings to the context manager as well.
    '''
    def __init__(self):
        self._running = False
       
    @abstractmethod 
    def on_start(self):
        ''' Any actions to perform on the pin when the device starts.
        '''
        self._running = True
        
    @abstractmethod
    def on_stop(self):
        ''' Any actions to perform on the pin when the device stops.
        '''
        self._running = False
        
    @property
    def running(self):
        ''' Read-only property describing whether or not the pin is
        currently running.
        '''
        return self._running
        
    def __enter__(self):
        ''' Call on_start in a with statement.
        '''
        self.on_start()
        return self
        
    def __exit__(self):
        ''' Call on_stop when leaving a with statement.
        '''
        self.on_stop()
        