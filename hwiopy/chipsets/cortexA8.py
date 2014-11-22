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

with open(__path__[0] + '/cortexA8_memmap.json', 'r', newline='') \
        as json_mem_map:
    cortexA8_mem_map = json.load(json_mem_map)

class sitara335(core.chipset):
    ''' The sitara 335 SoC. Used in the Beaglebone Black.
    '''
    def __init__(self):
        with open(__path__[0] + '/sitara_pinmodes.json', 'r', newline='') \
                as json_pinmodes:
            pin_modes = json.load(json_pinmodes)
        super().__init__(pin_modes=pin_modes, mem_map=cortexA8_mem_map)