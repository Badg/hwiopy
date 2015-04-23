''' Core2: atomic update file for core during package restructuring.

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
import collections
import threading
import struct
from warnings import warn
from abc import ABCMeta, abstractmethod
from math import ceil, log2

# Package dependencies
from platforms import BBB


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
        self.setup()
        
    @abstractmethod
    def hardware_setup(self):
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


class PinBase(Runnable):
    ''' An abstract base class for all pin objects, regardless of 
    function. 
    
    Should always call self.setup.
    
    Note that the exclusive use lock currently only applies to external
    accessors that voluntarily use the enter and exit functions, not to
    everyone that accesses. It will probably be transitioned to an RLock
    in order to provide that functionality, though that will incur some
    performance overhead.
    '''
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setup()
        self.__exclusive_use = threading.Lock()
        
    @abstractmethod
    def hardware_setup(self):
        ''' Any actions needed to perform to set up the pin. This method
        should be called once, at initialization. It should **not** be 
        used to configure the pin after a device has started.
        '''
        pass

    @abstractmethod
    def hardware_release(self):
        ''' Performs any cleanup needed to un-setup the pin and return 
        the pin to its previous state.
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
        
    def __enter__(self):
        ''' Overrides the default context manager behavior of runnable,
        since you can't have a pin without a device, and instead creates
        a thread-safe way of locking the pin.
        '''
        self.__exclusive_use.acquire()
        return self
        
    def __exit__(self):
        ''' Overrides the default context manager behavior of runnable,
        since you can't have a pin without a device, and instead creates
        a thread-safe way of locking the pin.
        '''
        self.__exclusive_use.release()
        
      
class Register(ABCMeta):
    ''' Base class for a memory register.
    '''
    def __init__(self, size, register_mmap):
        ''' a;sdkjf;alkjsdf
        '''
        super().__init__()
        
    def write(self):
        ''' Updates the register.
        '''
        pass
        
    def read(self):
        ''' Reads the register status. 
        '''
        pass
     
     
class Packetizer():
    ''' Support operations for bitwise manipulations.
    '''
    def __init__(self, size, endianness):
        ''' Creates a packet generator of bit length "size", with byte 
        order "endianness".
        
        Length must be a multiple of 8.
        
        Acceptable values for endianness: 
            'little'
            'big'
            
        Calling the instance returns its current state as a bytes 
        object.
        
        Packetizer.collapsed returns its current state as an integer.
        '''
        # Fix potential case issues
        endianness = endianness.lower()
        # Error trappage
        if size % 8:
            raise ValueError('Packet size must be a multiple of 8.')
        if endianness not in {'little', 'big'}:
            raise ValueError('Endianness must be "little" or "big".')
        # Handle endianness
        self._order = endianness
        if endianness == 'little':
            fmt = '<'
            self._ordered = lambda: self._order_little(self._words)
        else:
            fmt = '>'
            self._ordered = lambda: self._order_big(self._words)
        byte_len = int(size / 8)
        fmt += 'B' * byte_len
        # Now create the struct.pack object
        self._p = struct.Struct(fmt).pack
        # Need somewhere to store the packet state
        self._words = [0] * byte_len
        # And some things to keep track of size.
        self._size = size
        
    def pack(self, value, offset=0, pad_to_size=None):
        ''' Sets whatever bits are necessary to generate "value" 
        starting at "offset", optionally padded to "pad_to_size" bits.
        
        value must be of type int
        offset must be of type int. It is a BIT offset.
        pad_to_size must be of type int.
        '''
        # Calculate the number of bits required for that value
        bits_required = ceil(log2(value + 1))
        # Error trap for pad_to_size smaller than bits required
        if pad_to_size and pad_to_size < bits_required:
            raise ValueError('Padded size is smaller than the bits required '
                             'for given value.')
        # Figure out how many bits are actually required
        bits_required = pad_to_size or bits_required
        # Error trap for out-of-bounds value
        if bits_required > self.size - offset:
            raise ValueError('Value cannot fit into the packet at that '
                             'offset (or padding exceeds size).')
        # Construct a mask
        mask = 0
        for ii in range(bits_required):
            mask |= 1 << ii
        mask = mask << offset
        # Un-set the bits required for the value (and no more)
        new_state = self.collapsed & ~mask
        # Set the new bits
        new_state |= value << offset
        # Update the packet state
        self._words = self._split(new_state)
        
    def clear(self):
        ''' Clears the current packet.
        '''
        self._words = [0] * len(self._words)
        
    def __call__(self):
        ''' Returns the current packet.
        '''
        return self._p(*self._ordered())
        
    @property
    def size(self):
        ''' Read-only property that gives the packet size.
        '''
        return self._size
        
    @property
    def order(self):
        ''' Read-only property for endianness.
        '''
        return self._order
    
    @property
    def collapsed(self):
        ''' Collapses the internal representation into a single integer.
        This does not respect endianness, and supports python bitwise 
        operations.
        '''
        collapsed = 0
        for ii in range(len(self._words)):
            collapsed |= self._words[ii] << (8 * ii)
        return collapsed
        
    def __repr__(self):
        ''' Calculates a binary representation of the current packet
        state.
        '''
        if self.order == 'little':
            view = '0L'
        else:
            view = '0B'
        ordered = self._ordered()
        # Iterate over each word.
        for word in ordered:
            # Need to go backwards for the individual bits though.
            for ii in range(7, -1, -1):
                # Mask the specific bit, combine it with value, and then truth with
                # 1 to get zero or one
                view += str(word & (1 << ii) and 1)
        return view + ', collapsed: ' + str(self.collapsed)
        
    def _split(self, value):
        ''' Splits the value into each word.
        '''
        split = []
        for ii in range(len(self._words)):
            # Isolate words, one at a time, by shifting them over (truncates 
            # anything out of bounds) and masking with 0b11111111
            word = (value >> (8 * ii)) & 255
            split.append(word)
        return split
        
    @property
    def _collapsed_ordered(self):
        ''' Collapses the internal representation into a single integer.
        THIS IS NOT THE SAME THING YOU WOULD PASS TO STRUCT.PACK! This
        pays attention to bit ordering during the collapse.
        '''
        collapsed = 0
        ordered = self._ordered()
        for ii in range(len(ordered)):
            collapsed |= ordered[ii] << (8 * ii)
        return collapsed
        
    @staticmethod
    def _order_big(itr):
        ''' Returns a properly-ordered iterable for big-endianness.
        '''
        itr = itr.copy()
        itr.reverse()
        return itr
        
    @staticmethod
    def _order_little(itr):
        ''' Returns a properly-ordered iterable for little-endianness.
        '''
        return itr.copy()
      
        
class MmapPinBase(PinBase, Register):
    ''' Abstract base class for any memory-mapped pin.
    
    Subclass register or just have one?
    '''
    @abstractmethod
    def __init__(self, system_name, hardware_name=None):
        ''' 
        hardware_name: what the hardware calls this pin, ex '8_7'
        system_name: what the system calls this pin, ex 'r7'
        
        No need for the names to be different. If no hardware_name is 
        provided, uses the system_name as the hardware_name.
        '''
        super().__init__()
        # Explicitly check for None as hardware name to preserve things that
        # evaluate to False:
        if hardware_name == None:
            hardware_name = system_name
        # And set them into self.
        self._hardware_name = hardware_name
        self._system_name = system_name
    
    @property
    def register_name(self):
        ''' Returns the name of the memory register that controls the 
        behavior of this pin.
        '''
        return self._register_name
    
        
class Runnable(metaclass=ABCMeta):
    ''' An abstract base class for anything that can be run in the
    hwiopy package. Subclasses must implement on_start, on_stop, and are
    guaranteed to have a read-only self.running property.
    
    As a convenience, the on_start and on_stop methods have been given
    bindings to the context manager as well.
    '''
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
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
        
    
class _LockingPersistentMMap(mmap.mmap):
    ''' Wraps mmap, replacing the default context manager behavior with
    a locking mechanism. Intended to allow systems to handle their mmap
    opening and closing within THEIR respective context manager methods,
    whilst making the mmaps they use thread-safe.
    
    Inits with an open file object and a python slice of the zeroth, 
    '''
    def __init__(self, f, length, offset):
        # Insert a lock into self and call super.
        self.__lock = threading.Lock()
        super().__init__(f.fileno(), length, offset=offset)
        
    def __enter__(self):
        # Get the lock and then return self.
        self.__lock.acquire()
        return self
        
    def __exit__(self):
        # Release the lock.
        self.__lock.release()


class _UndetectedHardware():
    ''' Exists for the sole purpose of preventing the use of DetectedHardware
    when the hardware was not autodetected.
    '''
    def __init__(self):
        raise RuntimeError('Hardware was not autodetected during install. If '
                           'you\'re running a system that should have been '
                           'detected, try reinstalling the package.')
# This bit is used for DetectedHardware to know where it inherits from.
_DetectedHardware = _UndetectedHardware
if False:
    _DetectedHardware = BBB
# DetectedHardware directly and only wraps the class for whatever hardware 
# platform was detected.
class DetectedHardware(_DetectedHardware):
    ''' Use the hardware that was autodetected during pip install. If the 
    hardware could not be detected, immediately raises RuntimeError, thanks to
    _UndetectedHardware.
    '''
    pass










'''
The idea is to very easily generate device new device descriptions for a
given SoC, as well as provide a super simple way to get the SoC terminal.

Might add a "user_name" field that supports arbitrary anything, so that
someone might, for example, call "P8_7" on the beaglebone "test_pin".
'''
class ParallelKeyMap():
    ''' Parallel dictionary supporting bi-directional lookup between a device's
    pin naming scheme and an arbitrary hwiopy-internal integer description of 
    its pins.

    Getting an item:
    >>> ParallelKeyDict[<any valid key>]
    value
    
    Setting a new value:
    >>> ParallelKeyDict[Key1A, Key1B, Key1C...] = value
    (sets the value to all of the keys for a new value)
    
    Setting an existing value:
    >>> ParallelKeyDict[<any valid key>] = newvalue
    
    Linking keys:
    >>> ParallelKeyDict.link(old key, [new keys])
    
    Seeing linked keys:
    >>> ParallelKeyDict(<any valid key>)
    [All associated parallel keys]
    
    Removing a parallel key:
    >>> ParallelKeyDict.unlink(reference key, [keys to remove])
    
    Remove an entire item (also, all keys):
    >>> del ParallelKeyDict[<any valid key>]
    
    Does not (yet) support initialization of keys in a single shot.
    '''
    
    def __init__(self):
        ''' errrrrrr...
        '''
        # First call super
        super().__init__()

        # Give it a namespace. This is where we'll record every name.
        self._namespace = set()

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
         

class SplitHashMap(collections.MutableMapping):
    ''' Creates a key: value store from a hash map using a specified 
    hash algorithm. 
    
    This seems a bit redundant, I suppose, given that python dicts *are*
    hash maps. However, the point of this class is to support more 
    complex use cases, for examples:
    1. Chain maps with reused content but different key structures
    2. Parallel key dictionaries
    3. Hash maps using secure hash functions (useful for content-based
       addressing)
    (that is actually everything I can think of at this moment).
    I'd be happy to hear of cleverer ways of doing this!
    '''
    def __init__(self, d=None, hasher=hash):
        ''' Creates a SecureHashMap, optionally from an existing dict d.
        Uses hash algorithm "hasher", which must be a callable, and 
        should take one positional argument (the object to hash) and 
        return the finalized hash. The type compatibility of the hasher
        will determine the type compatibility of the split hash map. 
        Also worth noting: there is no built-in handling of hash 
        collisions, so plan accordingly. If the splitting method 
        encounters a collision, it will raise a ValueError.
        
        This DOES support nested containers, but they must be either
        dict-like or list-like.
        
        The output of hasher *must* be usable as a dictionary key. In
        general, int is most efficient?
        '''
        # First, some error traps.
        # Ensure hasher is callable.
        if not callable(hasher):
            raise TypeError('hasher must be callable.')
        # Turn d into a dictionary so we have items()
        try:
            d = dict(d or {})
        except TypeError:
            raise TypeError('d must be dict-like.')
            
        # Initialize the content dict
        self._split_values = {}
        # Split the input dictionary accordingly.
        self._split_keys = self._recursive_split(d, self._split_values, hasher)
        # Add in the hasher
        self._hasher = hasher

    def __getitem__(self, key):
        ''' Returns the chained byte value, instead of simply the 
        content's hash address.
        '''
        # Get the address (or the mapping) from the key.
        address = self._split_keys[key]
        # Recombine it (note we need to use recursive join because otherwise
        # nested mappings are unsupported)
        return self._recursive_join(address, self._split_values)

    def __setitem__(self, key, value):
        ''' Overrides default chainmap behavior, separating the key: value into
        a key: hash, hash: value dictionary, to allow for more robust internal
        manifest manipulation (and robust inheritance / anteheritance).
        '''
        # Do a recursive split of any content from the value, in case it's 
        # a container.
        stripped_mapping = self._recursive_split(value, self._split_values, 
                                                 self._hasher)
        
        # That will automagically mutate the self._split_values to include the
        # stripped value.
        self._split_keys[key] = stripped_mapping

    def __delitem__(self, key):
        ''' Smarter delete mechanism that garbage collects the self.content
        dictionary in addition to deleting the key from the mapping.

        todo: consider adding a method to delete content based on the content,
        thereby removing all the keys that point to it as well.
        
        todo: this is going to have a weird effect if you delete keys 
        from nested mappings. That should probably be figured out, but
        it can't be handled here. Well, I guess the only side effect 
        would be persistence in the content dictionary. Other than that,
        it should work just fine. But it would be orphaned content.
        '''
        # Actually, uh, this is pretty easy. Delete the key or mapping from the
        # keys dict
        del self._split_keys[key]
        # And garbage collect. Note that deleting a toplevel key might delete
        # lower-level mappings, so we can't just abandon if orphan.
        self.garbage_collect()

    def __len__(self):
        ''' Returns the length of the keys.
        '''
        return len(self._split_keys)
        
    def __iter__(self):
        ''' Returns the split keys iter.
        '''
        return self._split_keys.__iter__()

    def garbage_collect(self):
        ''' Checks every address in _split_values, removing it if not 
        found.
        '''
        # Note that we need to create a separate set of keys for this to avoid
        # "dictionary changed size during iteration"
        for address in set(self._split_values):
            self._abandon_if_orphan(address)

    def clear(self):
        ''' Ensures content is also cleared when the SHM is.
        '''
        self._split_values.clear()
        self._split_keys.clear()

    def _abandon_if_orphan(self, address):
        ''' Recursively checks the mapping for the address, removing it
        from values if not found.
        '''
        # Look at every mapping in _split_keys
        if not self._recursive_check(self._split_keys, address):
            del self._split_values[address]
        
    @classmethod
    def _recursive_join(cls, mapping, content):
        ''' Inspects every key: value pair in mapping, and then replaces
        any hash with its content. If the value is a container, 
        recurses.
        '''
        # Create a new instance of the mapping to copy things to.
        if isinstance(mapping, collections.Mapping):
            joined = mapping.__class__()
            for key, value in mapping.items():
                joined[key] = cls._recursive_join(value, content)
        elif isinstance(mapping, collections.MutableSequence):
            joined = mapping.__class__()
            for value in mapping:
                joined.append(cls._recursive_join(value, content))
        # Not a container. Process the value.
        else:
            # In this case, mapping is actually an address.
            joined = content[mapping]
            
        return joined

    @classmethod
    def _recursive_split(cls, mapping, content, hasher):
        ''' Inspects every key: value pair in mapping, and then replaces
        any content with its hash. If the value is a container, 
        recurses.
        
        Returns the stripped mapping.
        '''
        # Create a new instance of the mapping to copy things to.
        if isinstance(mapping, collections.Mapping):
            stripped = mapping.__class__()
            for key, value in mapping.items():
                stripped[key] = cls._recursive_split(value, content, hasher)
        elif isinstance(mapping, collections.MutableSequence):
            stripped = mapping.__class__()
            for value in mapping:
                stripped.append(cls._recursive_split(value, content, hasher))
        # Not a container. Process the value.
        else:
            # Let's split this shit. Get the has/address
            stripped = hasher(mapping)
            # Add it to external (outside of recursion) content if needed.
            if stripped not in content:
                content[stripped] = mapping
            # Ensure non-collision, and if collision, error.
            elif content[stripped] != mapping:
                raise ValueError('Hash collision. Sorry, not currently '
                                 'handled. Choose a different hash function, '
                                 'a different value, or implement a custom '
                                 'subclass with proper collision handling.')
                
        # And return whatever we did.
        return stripped
        
    @classmethod
    def _recursive_check(cls, mapping, address):
        ''' Inspects every key: value pair in mapping, and looks to see
        if any of the mappings point to the address. If the mapping is
        a container, recurses.
        
        A note on design decisions:
        Significant issues were encountered trying to implement this 
        class in a properly duck-typed way. The problem is that non-
        container iterable types like bytes and strings present huge
        challenges. In order to accomodate as many container types
        as possible, whilst simultaneously allowing for arbitrary
        content, I decided to limit the container types to those that
        are detected as either collections.Mapping or
        collections.MutableSequence. That means tuples will be ignored.
        
        Also, readability counts.
        '''
        found = False
        # In for a penny, in for a pound.
        if isinstance(mapping, collections.Mapping):
            for value in mapping.values():
                found |= cls._recursive_check(value, address)
        elif isinstance(mapping, collections.MutableSequence):
            for value in mapping:
                found |= cls._recursive_check(value, address)
        else:
            found |= (mapping == address)
        # Return.
        return found