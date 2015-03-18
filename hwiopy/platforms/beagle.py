''' Beaglebone/Beagleboard/Etc hardware-specific operations.

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

Something something sooooomething goes here.
'''
# Global dependencies
import io
import struct
import mmap
import json
from warnings import warn
from pkg_resources import resource_string
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
        # Load the corresponding json file and create a map dict
        self._sys_map = json.loads(
            resource_string('hwiopy', 'maps/bbb_sysmap.json').\
            decode('utf-8'))
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

    def __call__(self, pin_num, pin_941=None, pin_942=None, *args, **kwargs):
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
                warn(RuntimeWarning('Lookup on pin 9_41 without specifying '
                    'which mode to connect to. Defaulting to Sitara pin D14. '
                    'Consult the BBB system reference manual for details.'))
        if pin_num == '9_42':
            if pin_942:
                which_connection = pin_942
            else:
                warn(RuntimeWarning('Lookup on pin 9_42 without specifying '
                    'which mode to connect to. Defaulting to Sitara pin C18. '
                    'Consult the BBB system reference manual for details.'))
        
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
        super().__init__(systems.Sitara335(mem_filename), _header_map())

    def create_pin(self, pin_num, mode, name=None):
        ''' Gets a pin object from the self.chipset object and connects it to 
        a pin on the self.pinout dict.

        which_terminal is redundant with mode?
        '''
        # NOTE THAT DUE TO THE ODDITY OF THE BBB, pins 9_41 and 9_42 need to 
        # be specially configured, as they each connect to two SoC terminals.
        super().create_pin(pin_num, mode, name)


        # pin = self.pinout[pin_num]
        # return pin

        return self.pinout[pin_num]

    def validate(self):
        ''' Checks the device setup for conflicting pins, etc.

        Actually this is probably unnecessary (?), as individual pin 
        assignments should error out with conflicting setups.
        '''
        pass