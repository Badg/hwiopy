''' TI-built systems, especially SoCs.

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

Missing a great many error traps.

This should all be made threadsafe. It is currently HIGHLY un-threadsafe.

TODO: remove cyclic references between pins and systems.
'''
# Global dependencies
import io
import json
import struct
import mmap
from pkg_resources import resource_string
from math import ceil

# Intrapackage dependencies
from .. import core
# from .. import platforms

class Sitara335x(core.SystemBase):
    ''' The sitara 335x SoC.
    
    Todo: enormously prune and clean up the sitara335x.json file.
    '''
    # Internal constants
    MAP_FILE = resource_string('hwiopy', 'system_maps/sitara335x.json')
    SYSTEM_MAP = json.loads(MAP_FILE.decode('utf-8'))
    
    def __init__(self, mem_filename='/dev/mem'):
        super().__init__()
        # Store the memory file details
        self._mem_filename = mem_filename
        self._mem_file = None
        self._mmaps = {}
        # Initialize the pin dictionary
        self.pins = {}
        
    def hardware_setup(self):
        ''' Hardware setup only. Good place for overlays, etc.
        
        Currently unimplemented. 
        '''
        super().hardware_setup()

    def on_start(self, *args, **kwargs):
        ''' Must be called to start the device.
        '''
        # Call super to get things started.
        super().on_start()
        
        # Open the memfile
        self._memfile = open(self._mem_filename, "r+b")
        # Should first set up the clock modules, control registers, etc.
        # Set up all of the pins
        for name, pin in self.pins:
            pin.on_start(self.mmaps[pin.register_name])

    def on_stop(self, *args, **kwargs):
        ''' Cleans up the started device.
        '''
        super().on_stop()
        # Close all mmaps.
        for name, _mmap in self._mmaps:
            _mmap.close()
        
    def get_register_mmap(self, name):
        ''' Gets the mmap for the named register. If it hasn't already
        been opened, opens it, and stores in in self._mmaps.
        '''
        pass
        
    @property
    def mmaps(self):
        ''' Provides read-only access to self._mmaps.
        '''
        return tuple(self._mmaps)