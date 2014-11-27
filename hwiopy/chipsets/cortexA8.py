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

class sitara335(core.soc):
    ''' The sitara 335 SoC. Used in the Beaglebone Black.
    '''
    def __init__(self, mem_filename):
        # First grab the pinmodes file, which describes which processor pins
        # are capable of which modes, what mem map to look up, etc
        with open(__path__[0] + '/sitara_pinmodes.json', 'r', newline='') \
                as json_pinmodes:
            pin_modes_all = json.load(json_pinmodes)
        # Call the super() with the parsed pin modes
        super().__init__(pin_modes_all=pin_modes_all, 
                mem_map=_cortexA8_mem_map, 
                registers=_cortexA8_registers, 
                mem_filename=mem_filename)

    def __enter__(self):
        ''' Overrides the generic chipset entry method.
        '''
        self.on_start()

    def __exit__(self, type, value, traceback):
        ''' Overrides the generic chipset exit method.
        '''
        self.on_stop()

    def on_start():
        ''' Must be called to start the device.
        '''
        super().on_start()
        # Need to parse over all pin modes and open mmaps for each

    def on_stop():
        ''' Cleans up the started device.
        '''
        super().on_stop()

    def declare_pin():
        ''' Sets up a pin as something, checks for available modes, etc.
        '''
        super().declare_pin()

    def _setup_pin(self, pin, mode):
        ''' Gets the pin ready for use. Handles muxing, mode select, etc.
        '''
        # Need to figure out the appropriate mmap for the pin
        #    That said, the mmap should already be opened, probably in the 
        #    on_start method. Then go over each mmap that the SoC needs to 
        #    make. This would be after the super() call.
        # Need to mux the pin
        # Might need an overlay for the pin
        pass


def create_gpio():
    ''' Initializes a processor pin as a GPIO pin.
    '''
    pass