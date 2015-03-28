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
import subprocess, tempfile, json
from subprocess import CalledProcessError
from pkg_resources import resource_filename, resource_string

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
        # Get the description from the mapping file
        sitara_description = json.loads(resource_string('hwiopy', 
            'maps/sitara_termmodes.json').decode('utf-8'))

        # Iterate over every SoC terminal
        for terminal_name, terminal_dict in sitara_description.items():
            # Create a list of every available mode for the terminal
            modes = [mode['mode_type'] for mode in 
                terminal_dict['modes'].values()]
            # If gpio is in the modes
            if 'gpio' in modes:
                # Describe it
                desc = 'Terminal ' + terminal_name + ' gpio overlay'
                # Name it
                name = 'hwiopy-gpio-' + terminal_name
                offset = terminal_dict['control_reg_offset']
                # Get the control, convert it to a proper hex string
                control = hex(int(terminal_dict['mux_default'], 16))

                # Build a dts for it
                self._build_dts(desc, name, offset, control)

    @classmethod
    def do(cls):
        self = cls()

    @staticmethod
    def _build_dts(description, name, offset, control, pin=None, device=None):
        ''' 
        description: the overlay description.
        name: the overlay name.
        offset: the register offset address for the SoC terminal.
        control: the pinmux setting.
        pin: the header pin (currently unused)
        device: SPI, UART, etc. (currently unimplemented)

        Ignore the docstring below this bit.
        -----------------------------------------------------------------

        pin_str: ex 'P8_3'

        pin_dict: ex
        {
            "name": "USR0",
            "gpio": 53,
            "led": "usr0",
            "mux": "gpmc_a5",
            "key": "USR0",
            "muxRegOffset": "0x054",
            "options": [
                "gpmc_a5",
                "gmii2_txd0",
                "rgmii2_td0",
                "rmii2_txd0",
                "gpmc_a21",
                "pr1_mii1_rxd3",
                "eqep1b_in",
                "gpio1_21"
            ]
        }

        mux_mode: ex 'Mode7: gpio1_21'

        If the pin_dict contains options:
            # bspm? 

            if the mux_mode is pwm:
                # bspwm?
                pin sysfs loc = '/sys/devices/ocp.?/pwm_test_'+pinstr+'.??/'

            pin data = slew rate (FAST/slow), 
                direction (OUT/in), 
                pullup (PULLUP/pulldown/disabled),
                muxmode (ex 0x07 mode 7)

            create dts (pin_dict, pin data, bspm/bspwm)

        else:
            could be analog in, which don't require overlays?
            other options are set things like reference voltages and also 
            cannot be overlayed/set/etc


        Note: dtbo filename must include the version. So if the part-number is 
        'BLAHBLAH', the whole thing needs to be 'BLAHBLAH-00A0.dtbo'

        Note: Need to check which numbers to unexport (see adafruit tutorial) 
        before exporting, for the sake of cleanup. That said, we should be 
        careful with that, since evidently it can cause a kernel panic 
        situation?

        Note: I hear that PWM overlay generation works differently?
        '''
        # Maybe define this elsewhere?
        version = '00A0'

        # Define the header
        template = \
            resource_string('hwiopy', 'overlays/bbb_template_gpio.dts').\
            decode()

        # Make a name that contains no dashes
        safename = name.replace('-', '_')

        # Replace applicable fields in the template
        dts = template.replace('__NAME__', name)
        dts = dts.replace('__DESCRIPTION__', description)
        dts = dts.replace('__VERSION__', version)
        dts = dts.replace('__SAFENAME__', safename)
        dts = dts.replace('__OFFSET__', offset)
        dts = dts.replace('__PINCONTROL__', control)

        # Output the dts
        dts_filename = resource_filename('hwiopy', 'overlays') + '/' + name +\
            '-' + version + '.dts'
        with open(dts_filename, 'w+') as dts_file:
            dts_file.write(dts)

    def _compile_dts(self, name):
        # Maybe define this elsewhere?
        version = '00A0'

        # Get the before and after filenames
        overlays_path = resource_filename('hwiopy', 'overlays') + '/'
        dts_filename = overlays_path + name + '-' + version + '.dts'
        dtbo_filename = overlays_path + name + '-' + version + '.dtbo'

        # Make the system call
        subprocess.check_call([self._dtc_string, '-O', 'dtb', '-o', 
            dtbo_filename, '-b', '0', '-@', dts_filename])

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