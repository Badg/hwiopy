''' Beaglebone Black hardware-specific operations.

Something something sooooomething goes here.

Missing a great many error traps.
'''
# Global dependencies
import io
import json

# Intrapackage dependencies
from . import __path__
from .. import core
# from .. import platforms

# Get the imported definitions of the memory mapping itself and the 
# memory registers, both from the datasheets / TRM / etc. The map 
# describes the block, ex: the GPIO1 register is at 0x??????, while
# the registers describe the bitwise breakup of each type of register,
# ex: within the GPIO1 register, the first bit is _, second is _, etc

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
    register_function:  str             'ex: dataout, cleardataout, etc'
    bit_command=None:   str             'ex: autoidle, enawakeup, etc'

    return
    -------------------------------------------------------

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

    def __call__(self, register_type, register_function, bit_command=None):
        # Grab the function's definition
        # Then resolve the offset and size for the register function
        function_dict = \
            self._register_dict[register_type][register_function]
        # Return a tuple of (offset, bitsize)
        resolved = [int(function_dict['address'], base=16), 
            function_dict['bitsize']]

        # If we're trying to call a specific bit command, resolve which bits
        # correspond to that setting.
        if bit_command:
            # Grab the dictionary of possible bits for this function
            bit_range_dict = \
                self._register_dict[register_type][register_function]['bits']
            # Extract the bits as a list and return it
            bit_range = list(range(
                bit_range_dict[bit_command][0], 
                bit_range_dict[bit_command][1] + 1
                ))
            resolved.append(bit_range)

        return tuple(resolved)

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

class Sitara335(core.System):
    ''' The sitara 335 SoC. Used in the Beaglebone Black.
    '''
    def __init__(self, mem_filename):
        # First grab the termmodes file, which describes which terminals
        # are capable of which modes, what mem map to look up, etc
        with open(__path__[0] + '/sitara_termmodes.json', 'r', newline='') \
                as json_termmodes:
            terminal_modes = json.load(json_termmodes)

        # Call the super() with the parsed terminal modes
        super().__init__(terminal_modes=terminal_modes)

        # Grab the filename for the memory mapping
        self._mem_filename = mem_filename

        # Now create the _memory_map object for callable use
        self._resolve_map = _memory_map()
        # Now create the _resolve_register_bits for calling
        self._resolve_register_bits = _register_map()

    def __enter__(self):
        ''' Overrides the generic chipset entry method.
        '''
        self.on_start()

    def __exit__(self, type, value, traceback):
        ''' Overrides the generic chipset exit method.
        '''
        self.on_stop()

    def on_start(self, *args, **kwargs):
        ''' Must be called to start the device.
        '''
        super().on_start()
        # Need to parse over all pin modes and open mmaps for each

    def on_stop(self, *args, **kwargs):
        ''' Cleans up the started device.
        '''
        super().on_stop()

    def declare_linked_pin(self, terminal, mode, *args, **kwargs):
        ''' Sets up a pin as something, checks for available modes, etc.
        '''
        # Don't forget to assign the result of the pin declaration
        pin = super().declare_linked_pin(terminal, mode)
        # Potentially modify the result of the pin declaration
        # Now return the pin
        return pin

    def _setup_term(self, term, mode):
        ''' Gets the terminal ready for use. Handles muxing, mode select, etc.
        '''
        # Need to figure out the appropriate mmap for the term
        #    That said, the mmap should already be opened, probably in the 
        #    on_start method. Then go over each mmap that the SoC needs to 
        #    make. This would be after the super() call.
        # Need to mux the term
        # Might need an overlay for the term
        pass