''' Beaglebone Black hardware-specific operations.

Something something sooooomething goes here.
'''
# Global dependencies
import io
import json

# Intrapackage dependencies
from . import __path__
from .. import core
# from .. import platforms

# Get the memory mappings and mode register locations
with open(__path__[0] + '/cortexA8_memmap.json', 'r', newline='') \
        as json_mem_map:
    _cortexA8_mem_map = json.load(json_mem_map)
with open(__path__[0] + '/cortexA8_registers.json', 'r', newline='') \
        as json_mem_map:
    _cortexA8_registers = json.load(json_mem_map)

class sitara335(core.system):
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
        self.mem_filename = mem_filename

        # Get the imported definitions of the memory mapping itself and the 
        # memory registers, both from the datasheets / TRM / etc. The map 
        # describes the block, ex: the GPIO1 register is at 0x??????, while
        # the registers describe the bitwise breakup of each type of register,
        # ex: within the GPIO1 register, the first bit is _, second is _, etc
        self.mem_mapping = _cortexA8_mem_map
        self.register_bits = _cortexA8_registers

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