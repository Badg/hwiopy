''' Beaglebone Black hardware-specific operations.

Something something sooooomething goes here.
'''
# Global dependencies
import io
import struct
import mmap
import json
# from os import listdir
# from os.path import isfile, join, split

# Intrapackage dependencies
from . import __path__
from .. import core
from .. import chipsets

# from . import generic
# from .generic import device

class bbb(core.device):
    ''' A beaglebone black. Must have kernel version >=3.8, use overlays, etc.
    '''
    # Where is the memory mapping stored to?
    # mem_reg_loc = '/dev/mem'
    # What pins correspond to what possible mappings?
    

    def __init__(self, mem_filename='/dev/mem'): 
        ''' Creates the device and begins setting it up.
        '''
        # Grab the json file describing what processor pins, voltages, etc
        # are tied to which header pins
        with open(__path__[0] + '/bbb_pinmap.json', 'r', newline='') \
                as json_pinmap:
            # Store that information in the pinmap
            pinmap = json.load(json_pinmap)

        # Now let's store the memory location
        self.mem_filename = mem_filename

        # Add the chipset; pass it the mem_filename
        self.chipset = chipsets.sitara335(self.mem_filename)

        # Finally, call super
        super().__init__(pinmap=pinmap)

    def __enter__(self):
        ''' Initializes hardware control and readies device for input/output.
        '''
        # Call super __enter__ ??
        super().__enter__()

        # Figure out the required memory range
        # Note this is currently the beginning of the GPIO2 register
        # self._map_start = 0x481AC000
        # self._map_size = 0x00000FFF

        # Get the memory map file
        # self._memfile = open(self.__class__.mem_reg_loc, "r+b")
        self._memfile = open(self.mem_filename, "r+b")

        # Get the memory map
        # self._mmap = mmap.mmap(self._memfile.fileno(), self._map_size, 
        #    offset=self._map_start)

        return self


    def __exit__(self, type, value, traceback):
        ''' Closes memory maps, cleans up variables, handles errors, etc.
        '''
        # Close and purge the memory map
        # self._mmap.close()
        # del self._mmap

        # Close and purge the memory map file
        self._memfile.close()
        del self._memfile

        # Clean up other variables
        # del self._map_start
        # del self._map_size

        # Call super
        super().__exit__()

    def validate(self):
        ''' Checks the device setup for conflicting pins, etc.
        '''
        pass

    # These numbers come from the ARM Cortex TRM, in Section 2.1 (Memory Map)
    # Can be found from the 
    # [AM3359 product page](http://www.ti.com/product/am3359). Note that, if
    # searching the TRM for these numbers, they will be in the format
    # 0x44E0_7000 -- INCLUDING the underscore.
    #define GPIO0_BASE 0x44E07000
    #define GPIO1_BASE 0x4804C000
    #define GPIO2_BASE 0x481AC000
    #define GPIO3_BASE 0x481AE000
    #define GPIO_SIZE  0x00000FFF

class bbb_gpio_pin(core.pin):
    def __init__(self, mode, bbb_device):
        super.__init__()