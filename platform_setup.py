''' Platform-specific installation scripts.

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
import subprocess, tempfile
from subprocess import CalledProcessError
from pkg_resources import resource_filename

class bbb_setup():
    ''' Performs installation setup for a Beaglebone Black.

    Basically using this as a local namsepace container so that all platform 
    setup files can be contained within this file. Flat is better than nested
    and all that.
    '''

    def __init__(self):
        ''' Handles all of the prerequisites we need to actually set up the
        beaglebone black.
        '''
        # Verify that dtc can be used. If not, install it. Then we can just 
        # do a subprocess.check_call([self._dtc_string, ...])
        if not self._check_dtc():
            # Declare the self dtc string as the included bbb_dtc.sh
            self._dtc_string = \
                resource_filename('hwiopy', 'setup_utils/bbb_dtc.sh')

            # Make the included dtc.sh executable
            subprocess.check_call(['chmod', '+x', self._dtc_string])
        else: 
            # Successfull verification; use built-in dtc
            self._dtc_string = 'dtc'

        # Okay, now we need to compile dtbos
        # Get the filenames for the relevant files
        test_overlay = resource_filename('hwiopy', 'overlays/test.dts')
        test_compiled = resource_filename('hwiopy', 'overlays') + '/test.dtbo'
        subprocess.check_call([self._dtc_string, '-O', 'dtb', '-o', 
            test_compiled, '-b', '0', '-@', test_overlay])

    @classmethod
    def do(cls):
        self = cls()

    def compile_overlays(self):
        pass

    def _check_dtc(self):
        ''' Checks for capability to run the device tree compiler. If 
        unavailable, uses a DTC copied from 
        https://raw.github.com/RobertCNelson/tools/master/pkgs/dtc.sh
        '''
        # Get the filenames for the relevant files
        test_overlay = resource_filename('hwiopy', 'overlays/test.dts')
        test_compiled = resource_filename('hwiopy', 'overlays') + '/test.dtbo'

        try:
            # Try using the system dtc on the example device tree
            subprocess.check_call(['dtc', '-O', 'dtb', '-o', 
                test_compiled, '-b', '0', '-@', test_overlay])

            # If that works, well, dandy
            return True
        # If it didn't work, an oserrror will be raised
        except (CalledProcessError, OSError):
            # Can't compile, get our own compiler.
            return False