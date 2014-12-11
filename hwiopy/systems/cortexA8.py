''' Beaglebone Black hardware-specific operations.

Something something sooooomething goes here.

Missing a great many error traps.

This should all be made threadsafe. It is currently HIGHLY un-threadsafe.
'''
# Global dependencies
import io
import json
import struct
import mmap

# Intrapackage dependencies
from . import __path__
from .. import core
# from .. import platforms

# This dict gets updated each time a new mode generator is implemented.
_mode_generators = {}

# Convert dicts into functions for memory maps and registers
class _memory_map():
    ''' Callable class that resolves the memory mapping for registers into a 
    [start, end] tuple. Also provides utility functions to list available 
    registers, etc.

    _memory_map():
    ======================================================

    *args
    ------------------------------------------------------

    register:           str             'name of register'

    return
    -------------------------------------------------------

    tuple               (start address, end address)


    _memory_map.list():
    ========================================================

    return
    --------------------------------------------------------

    tuple               ('register0', 'register1', 'register2'...)

    _memory_map.describe():
    =========================================================

    *args
    ---------------------------------------------------------

    register:           str             'name of register'

    return
    -------------------------------------------------------

    str                 'description of register'
    '''
    def __init__(self):
        # Simply load the corresponding json file and create a map dict
        with open(__path__[0] + '/cortexA8_memmap.json', 'r', newline='') \
                as json_mem_map:
            self._map_dict = json.load(json_mem_map)
        self._registers = tuple(self._map_dict.keys())
        
    def __call__(self, register):
        # Grab the start and convert it to int (aka long)
        start = int(self._map_dict[register]['start'], base=16)
        # Grab the end and same
        end = int(self._map_dict[register]['end'], base=16)
        # Return the tuple
        return (start, end)

    # Very simply return the available registers
    def list(self):
        return self._registers

    # Very simply return a description of the queried register
    def describe(self, register):
        return self._map_dict[register]['description']

class _register_map():
    ''' Callable class that resolves the bit mapping for registers into an 
    [offset, size] tuple. Also provides utility functions to list available 
    registers, etc.

    _register_map():
    ======================================================

    *args
    ------------------------------------------------------

    register_type:      str             'ex: gpio, pwm, etc'
    register_function=None: str             'ex: dataout, cleardataout, etc'
    bit_command=None:   str             'ex: autoidle, enawakeup, etc'

    return
    -------------------------------------------------------

    register_function=None: dict            {'function': (offset, bitsize)...}
    register_function=str:
        bit_command=None:   tuple           (offset, bitsize)
        bit_command=str:    tuple           (offset, bitsize, bitrange)


    _register_map.list():
    ========================================================

    *args
    --------------------------------------------------------

    register_type=None: str             'ex: gpio, pwm, etc'

    return
    --------------------------------------------------------

    register_type=None: tuple           ['gpio', 'pwm'...]
    register_type=str:  tuple           ['autoidle', 'enawakeup'...]
    
    _register_map.describe():
    =========================================================

    *args
    ---------------------------------------------------------

    register_type:      str             'ex: gpio, pwm, etc'

    return
    -------------------------------------------------------

    dict                {'function': ['bit op 1', 'bit op 2'...]}
    '''
    # What string defines the command for "each bit is a channel"?
    _channelwise = '_intchannel'

    def __init__(self):
        # Simply load the corresponding json file and create a map dict
        with open(__path__[0] + '/cortexA8_registers.json', 'r', newline='') \
                as json_reg_map:
            self._register_dict = json.load(json_reg_map)
        self._register_types = tuple(self._register_dict.keys())
        self._register_functions = {}
        for reg, reg_dict in self._register_dict.items():
            self._register_functions[reg] = tuple(reg_dict.keys())

    def __call__(self, register_type, register_function=None, 
            bit_command=None):
        # Error trap bit_command without register_function
        if bit_command and not register_function:
            raise ValueError('Must select function to resolve bit command.')

        if not register_function:
            reg_fns = self.list(register_type)
        else:
            reg_fns = [register_function]

        tmp_dict = {}
        for reg_fn in reg_fns:
            # Grab the function's definition
            # Then resolve the offset and size for the register function
            function_dict = \
                self._register_dict[register_type][reg_fn]
            # Return a tuple of (offset, bitsize)
            resolved = [int(function_dict['address'], base=16), 
                function_dict['bitsize']]

            # If we're trying to call a specific bit command, resolve which 
            # bits correspond to that setting. Note that due to error trap, 
            # this will only be true if we're focusing on a specific function
            if bit_command:
                # Grab the dictionary of possible bits for this function
                bit_range_dict = self.\
                    _register_dict[register_type][reg_fn]['bits']
                # Extract the bits as a list and return it
                bit_range = list(range(
                    bit_range_dict[bit_command][0], 
                    bit_range_dict[bit_command][1] + 1
                    ))
                resolved.append(bit_range)

            tmp_dict[reg_fn] = tuple(resolved)

        # If we are, in fact, only concerned with a single function, strip the
        # dict down to the tuple
        if not register_function:
            return tmp_dict
        else: 
            return tmp_dict[register_function]

    # Return the available register types, or if a type is specified, the 
    # functions available within that register.
    def list(self, register_type=None):
        if register_type:
            return self._register_functions[register_type]
        else: 
            return self._register_types

    # Describes a register type's functions and bit settings
    def describe(self, register_type):
        reg_dict = self._register_dict[register_type]
        desc = {}
        for fn, fn_dict in reg_dict.items():
            desc[fn] = list(fn_dict['bits'].keys())
        return desc

class _mode_map():
    ''' Callable class that resolves a sitara terminal into its 
    available modes, which are callable to initialize that mode.

    _mode_map():
    ======================================================

    *args
    ------------------------------------------------------

    terminal:           str             'name of terminal'
    mode=None           str             'mode for terminal'

    return
    -------------------------------------------------------

    mode=None           dict            {'mode': callable, 'gpio': gpio}
    mode=str            callable class  

    _mode_map.list():
    ========================================================

    *args
    --------------------------------------------------------

    terminal=None       str             'name of terminal'
    only_assignable=False   bool        Only list assignable modes

    return
    --------------------------------------------------------

    terminal=None       dict            {'term': ['mode', ...], ...}
    terminal=str        list            ['mode', 'mode', ...]

    _mode_map.describe():
    ========================================================

    *args
    --------------------------------------------------------

    terminal            str             'name of terminal'
    mode=None           str             'name of mode to describe'

    return
    --------------------------------------------------------

    mode=None           list            ['mode description, mode descr...]
    mode=str            str             'description of mode'

    _mode_map.get_register():
    ========================================================

    *args
    --------------------------------------------------------

    terminal            str             'name of terminal'
    mode                str             'name of mode'

    return
    --------------------------------------------------------

    str                 'name of register'
    '''
    def __init__(self, modes_file):
        # First grab the termmodes file, which describes which terminals
        # are capable of which modes, what mem map to look up, etc
        with open(modes_file, 'r', 
                newline='') as json_termmodes:
            self._mode_dict = json.load(json_termmodes)

        # Now construct a reference dict with all of the terminals: modes
        self._terminals = {}
        for term, term_dict in self._mode_dict.items():
            self._terminals[term] = list(term_dict['modes'].keys())

        # Construct a second reference dict with each terminal's 
        # mode: callables
        self._terminal_callables = {}
        for term, mode_list in self._terminals.items():
            # Initialize the dict for the terminal
            self._terminal_callables[term] = {}
            # Check modes for implementation; if none, add generic oops
            for mode in mode_list:
                try:
                    self._terminal_callables[term][mode] = \
                        _mode_generators[mode]
                except KeyError:
                    self._terminal_callables[term][mode] = \
                        _mode_not_implemented

        # Generate a reference dict of only assignable modes
        self._assignable = {}
        for term, term_dict in self._mode_dict.items():
            self._assignable[term] = []
            for mode, mode_dict in term_dict['modes'].items():
                # Validate that the mode has a number
                if mode_dict['mode_num']:
                    # Therefore make it assignable
                    self._assignable[term].append(mode)
        
    def __call__(self, system, terminal, mode):
        # Note that the system bit is needed due to inner/outer class 
        # namespaces. It would be nice to have a bound inner class, but
        # That can maybe be hammered out another time.
        # Error trap for the terminal name:

        # Call up the description; currently just for error trapping
        desc = self.describe(terminal, mode)
        return self._terminal_callables[terminal][mode](system, terminal)

    # List the available modes
    def list(self, terminal=None, only_assignable=False):
        if terminal:
            # Error trap out a bad terminal name
            desc = self.describe(terminal)
            if only_assignable:
                return self._assignable[terminal]
            else:
                return self._terminals[terminal]
        else: 
            if only_assignable:
                return self._assignable
            else:
                return self._terminals

    # Describe the available modes. Also used to check mode validity.
    # Yeah, I could probably devote a separate return True method to that,
    # but why bother?
    def describe(self, terminal, mode=None):
        # Error trap on bad terminal name 
        if terminal not in self._terminals:
            raise ValueError('Terminal ' + terminal + ' not found.')

        if mode:
            # Error trap on bad mode name
            if mode not in self._terminals[terminal]:
                raise ValueError(mode + 'mode is unavailable for ' + 
                    terminal.upper() + ' terminal.')
            else:
                return \
                    self._mode_dict[terminal]['modes'][mode]
        else: 
            return self._mode_dict[terminal]['modes'].values()

    def get_register(self, terminal, mode):
        return self.describe(terminal, mode)['register']

class Sitara335(core.System):
    ''' The sitara 335 SoC. Used in the Beaglebone Black.
    '''
    def __init__(self, mem_filename):
        # Call the super(), creating and passing the callable resolve_mode
        super().__init__(_mode_map(__path__[0] + '/sitara_termmodes.json'))

        # Grab the filename for the memory mapping
        self._mem_filename = mem_filename
        # Memfile will only exist when the memfile is open.
        self._memfile = None

        # Now create the _memory_map object for callable use
        self._resolve_map = _memory_map()
        # Now create the _resolve_register_bits for calling
        self._resolve_register_bits = _register_map()

    def __enter__(self):
        ''' Overrides the generic chipset entry method.
        '''
        self.on_start()
        return self

    def on_start(self, *args, **kwargs):
        ''' Must be called to start the device.
        '''
        super().on_start()
        # Need to parse over all pin modes and open mmaps for each

        # Open the memfile
        self._memfile = open(self._mem_filename, "r+b")

        for term, mode in self.terminals_declared.items():
            # Get the register name from the terminals_declared dict.
            # Should the register name be folded into the terminals_declared
            # dict? It's being accessed more than once.
            register = self._resolve_mode.get_register(term, mode)
            # Create the mmaps.
            self._get_register_mmap(register)

    def __exit__(self, type, value, traceback):
        ''' Overrides the generic chipset exit method.
        '''
        self.on_stop()

    def on_stop(self, *args, **kwargs):
        ''' Cleans up the started device.
        '''
        super().on_stop()

        registers = list(self._register_mmaps)
        # Close all mmaps and remove them from self._register_maps
        for register in registers:
            self._register_mmaps[register].close()
            del self._register_mmaps[register]

        # Cleanup the memfile
        self._memfile.close()
        self._memfile = None

    def declare_linked_pin(self, terminal, mode, *args, **kwargs):
        ''' Sets up a pin as something, checks for available modes, etc.
        '''
        # Don't forget to assign the result of the pin declaration
        pin = super().declare_linked_pin(terminal, mode)

        # Add the register name to the pin
        pin.register_name = self._resolve_mode.get_register(terminal, mode)

        # Potentially modify the result of the pin declaration
        # Now return the pin
        return pin

    def _get_register_mmap(self, register):
        ''' Returns an mmap for the specified register. If the register hasn't
        been opened, opens it.

        This should only be called during setup, not during initialization or
        after the system has started.
        '''
        # Error trap: is the memfile open?
        if not self._memfile:
            raise RuntimeError('System must be started and the memory file '
                'opened for access to pin functions.')

        # If it hasn't already been opened, open it and add it to the dict
        if register not in self._register_mmaps:
            # This will result in a (start, end) tuple, so unpack it
            register_start, register_end = self._resolve_map(register)
            # Convert to start, size
            register_size = register_end - register_start
            # Open and add the mmap
            self._register_mmaps[register] = mmap.mmap(
                self._memfile.fileno(), register_size, offset=register_start)

        # Now it's definitely open. Return the mmap.
        return self._register_mmaps[register]

class _gpio():
    ''' Callable class for creating a GPIO terminal for cortex A8 SoCs.
    Functions as a generator for core.Pin update, status, and setup methods,
    as well as any other methods relevant to the gpio.
    '''
    def __init__(self, system, terminal):
        # Doublecheck that the terminal can be set as a gpio and get its deets
        self.desc = system._resolve_mode.describe(terminal, mode='gpio')

        self.system = system
        self.terminal = terminal

        self.direction = None
        self._mmap = None

        # Use the description dictionary to figure out which gpio register
        self.register_name = \
            system._resolve_mode.get_register(terminal, 'gpio')
        # Now resolve the memory address (start, end tuple)
        self.channel_number = int(self.desc['register_detail'])
        # And generate a bit-shifted description of which channel this is
        self.channel_bit = 1 << self.channel_number
        # Grab the description of all gpio registers:
        self.register_map = self.system._resolve_register_bits('gpio')

        # For fast access store the setdataout and cleardataout bits as slices
        # This yields an (address, bit length) tuple
        set_out = self.register_map['setdataout']
        # We want (byte start: byte end) slice
        self.set_out = slice(set_out[0], set_out[0] + set_out[1]/8)
        # (address, bit length) tuple
        clear_out = self.register_map['cleardataout']
        # To (byte start: byte end) slice
        self.clear_out = slice(clear_out[0], clear_out[0] + clear_out[1]/8)

        # I looooooooooooove late-binding closures right now, this shit is 
        # fucking magical. I can't believe this worked first try.
        self.methods = {}
        # self.methods['setup'] = self.setup
        self.methods['update'] = self.update
        self.methods['status'] = self.status
        self.methods['on_start'] = self.on_start
        self.methods['on_stop'] = self.on_stop
        self.methods['output_high_nocheck'] = self.output_high_nocheck
        self.methods['output_low_nocheck'] = self.output_low_nocheck
        self.methods['config'] = self.config

    def __call__(self):
        return self.methods

    def update(self, status):
        # Check self.direction
        # Check status and call corresponding 
        pass

    def output_high_nocheck(self):
        # Update HIGH/True without checking if input/output.
        self._mmap[self.set_out] = struct.pack('<L', self.channel_bit)

    def output_low_nocheck(self):
        # Update LOW/False without checking if input/output.
        self._mmap[self.clear_out] = struct.pack('<L', self.channel_bit)

    def status(self):
        print(self.direction)

    # Updates all of the methods with the appropriate mmap.
    # I fucking love late binding closures.
    # No __enter__ as this is not intended for external use / context mgmt
    def on_start(self):
        # Error trap: is direction configured?
        if not self.direction:
            raise RuntimeError('GPIO direction (in/out) has not been '
                'configured.')

        # Update my _mmap and direction
        self._mmap = self.system._get_register_mmap(self.register_name)
        self._set_direction()

    # No __exit__ as this is not intended for external use / context managment
    def on_stop(self):
        self._mmap = None

    def _set_direction(self):
        # Update the mmap direction
        pass
        # something something something, function(self.direction)

    def config(self, direction):
        # Error trap the direction (only in/out)
        if direction != 'in' and direction != 'out':
            raise ValueError('GPIO direction must be "in" or "out".')
        
        # Cool, let's set up
        self.direction = direction

_mode_generators['gpio'] = _gpio

def _mode_not_implemented():
    raise NotImplementedError('This package does not yet support that '
        'mode on the cortex A8 chipset.')