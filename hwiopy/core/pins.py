''' Core: pins. Abstract base classes for various types of pins.

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
'''
# Global dependencies
from abc import ABCMeta, abstractmethod

# Package dependencies
from .core import PinBase

class GPIO(PinBase):
    ''' Abstract base class for a gpio pin.
    '''
    @property
    @abstractmethod
    def info(self):
        ''' Returns configuration information for the pin. Read only.
        '''
        pass

    @property
    @abstractmethod
    def state(self):
        ''' Returns the current state of the pin. Read only for input; r/w for
        output.
        '''
        pass

    @state.setter
    @abstractmethod
    def state(self, value):
        ''' Setter for the current pin state. Only available when the pin is
        configured in the output direction.
        '''
        pass
