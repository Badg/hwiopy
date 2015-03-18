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

def bbb_setup():
    ''' Performs installation setup for a Beaglebone Black.
    '''
    pass

def _check_dtc():
    ''' Checks for capability to run the device tree compiler.
    '''
    pass

    # ~/
    # wget -c https://raw.github.com/RobertCNelson/tools/master/pkgs/dtc.sh
    # chmod +x dtc.sh
    # ./dtc.sh