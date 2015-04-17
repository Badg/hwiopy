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

class Sitara335x(core.System):
    ''' The sitara 335x SoC.
    '''
    def __init__(self, mem_filename):
        super().__init__()
        
    def setup(self):
        super().setup()

    def on_start(self, *args, **kwargs):
        ''' Must be called to start the device.
        '''
        super().on_start()

    def on_stop(self, *args, **kwargs):
        ''' Cleans up the started device.
        '''
        super().on_stop()