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
from .. import systems

# from . import generic
# from .generic import device

class _header_map():
    ''' Callable class that resolves the header pins into their connections, 
    as well as providing several utility functions to describe the device.

    _header_map():
    ======================================================

    Returns the header connection, be it a hardwired one (ex 5VDC) or a SoC
    terminal.

    *args
    ------------------------------------------------------

    pin_num:            str             'pin number'

    return
    -------------------------------------------------------

    str                 'SoC terminal or other'

    _header_map.list_system_headers():
    ========================================================

    Returns all of the header pins that connect to the sitara SoC.

    return
    --------------------------------------------------------

    dict                {'pin num': 

    _memory_map.list_all_headers():
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
        with open(__path__[0] + '/bbb_sysmap.json', 'r', newline='') \
                as json_sysmap:
            # Store that information in the pinmap
            self._sys_map = json.load(json_sysmap)
        self._header_pins = tuple(self._sys_map.keys())

        # Predeclare 
        self._hardwired = {}
        self._connected = {}
        self._all_headers = {}
        # Separate any hardwired (5VDC, GND, etc) pins from SoC connections
        # Need way to collapse dict list into single item for _all_headers
        for pin_num, pin_dict in self._sys_map.items():
            if pin_dict['connections']:
                self._hardwired[pin_num] = pin_dict['connections']
                self._all_headers[pin_num] = pin_dict['connections']
            elif pin_dict['terminals']:
                self._connected[pin_num] = pin_dict['terminals']
                self._all_headers[pin_num] = pin_dict['terminals']

    def __call__(self, pin_num, pin_941=None, pin_942=None *args, **kwargs):
        # Grab the start and convert it to int (aka long)
        # NOTE THAT HERE IS THE PLACE TO DEAL WITH THE TWO HEADER PINS THAT
        # ARE CONNECTED TO TWO SOC PINS!! (pin 9_41 and pin 9_42)

        # Don't necessarily want to error trap out declaring pin_941 and/or
        # pin_942 with each other, or with a different pin number

        which_connection = 0
        if pin_num == '9_41':
            if pin_941:
                which_connection = pin_941
            else:
                raise RuntimeWarning('Lookup on pin 9_41 without specifying '
                    'which mode to connect to. Defaulting to Sitara pin D14. '
                    'Consult the BBB system reference manual for details.')
        if pin_num == '9_42':
            if pin_942:
                which_connection = pin_942
            else:
                raise RuntimeWarning('Lookup on pin 9_42 without specifying '
                    'which mode to connect to. Defaulting to Sitara pin C18. '
                    'Consult the BBB system reference manual for details.')
        
        # Now use whatever information we have to output the connection
        return self._all_headers[pin_num][which_connection]

    # Returns all header pins that are configurable
    def list_system_headers(self):
        return self._connected

    # Very simply return a description of the queried register
    def list_all_headers(self):
        return self._all_headers


class BBB(core.Device):
    ''' A beaglebone black. Must have kernel version >=3.8, use overlays, etc.
    '''
    # Where is the memory mapping stored to?
    # mem_reg_loc = '/dev/mem'
    # What pins correspond to what possible mappings?
    

    def __init__(self, mem_filename='/dev/mem'): 
        ''' Creates the device and begins setting it up.
        '''
        # Call super, initializing all of the abstract base class attributes
        super().__init__(systems.sitara335(mem_filename), _header_map())

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

    def create_pin(self, pin_num, mode, name=None):
        ''' Gets a pin object from the self.chipset object and connects it to 
        a pin on the self.pinout dict.

        which_terminal is redundant with mode?
        '''
        # NOTE THAT DUE TO THE ODDITY OF THE BBB, pins 9_41 and 9_42 need to 
        # be specially configured, as they each connect to two SoC terminals.
        super().create_pin(pin_num, mode, name)

        pin = self.pinout[pin_num]

        # Need to add update, status, setup methods
        # Should pin.register, pin.bits, etc be defined first in core.Pin, or
        # should they be added specifically and only to the BBB?
        # Perhaps a pin.location? 

    def validate(self):
        ''' Checks the device setup for conflicting pins, etc.

        Actually this is probably unnecessary, as individual pin assingments
        should error out with conflicting setups.
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