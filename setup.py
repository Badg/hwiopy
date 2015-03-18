''' hwiopy: A common API for hardware input/output access.

hwiopy, "hardware input/output, python", is a general purpose IO library 
intended to provide a common, simple python API to physical systems, 
particularly ones running embedded linux. The hope is to allow a single, 
unified codebase to run on multiple hardware platforms with minimal (if any) 
modification. Early development targets include the Beaglebone Black and 
Raspberry Pi.
'''

# Global dependencies
import subprocess
from warnings import warn

# Bootstrap setuptools
import ez_setup
# Dunno why I need this but I think I do?
try:
    del pkg_resources, setuptools
except NameError:
    pass
# Carry on then
ez_setup.use_setuptools()

# Import global dependencies required for setup.py
from setuptools import setup, find_packages

metadata = dict(
    name = 'hwiopy',
    version = '0.0.0',
    description = 'A common API for hardware input/output access.',
    long_description = 'hwiopy, "hardware input/output, python", '
    'is a general purpose IO library intended to provide a common, simple '
    'python API to physical systems, particularly ones running embedded '
    'linux. The hope is to allow a single, unified codebase to run on '
    'multiple hardware platforms with minimal (if any) modification. Early '
    'development targets include the Beaglebone Black and Raspberry Pi.',
    url = 'https://github.com/Badg/hwiopy',
    author = 'Nick Badger',
    author_email = 'badg@nickbadger.com',
    license = 'GNU LGPL v2.1',
    classifiers = [
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'Intended Audience :: Education',
        'Intended Audience :: Science/Research',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.3',
        'Topic :: Home Automation',
        'Topic :: Scientific/Engineering',
        'Topic :: Software Development :: Embedded Systems',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: System :: Hardware'
        ],
    keywords = 'hardware io input output embedded',
    packages = find_packages(exclude=['doc', 'test']),
    install_requires = [],
    package_data = {
        # Include any .json files in the maps directory
        'hwiopy': ['maps/*.json'],
    })

def get_platform():
    ''' Figures out what platform the library is being installed onto for 
    deciding what install script to run.
    '''
    # This will complain about not being sudo but it shouldn't matter
    try:
        # Get the system hardware string and convert it into a string
        hw_str = subprocess.check_output(['lshw'], 
            stderr=subprocess.DEVNULL).decode()
        hw_list = hw_str.split('\n')

        # Quick. Dirty. Whatevs. Make better later.
        # Try to autodetect the hardware platform. Currently only works on the
        # beaglebone black. Currently also pretty damn janky.
        am355 = None
        beaglebone = None

        for line in hw_list:
            if line.lower().find('am335') >= 0:
                am355 = True
            if line.lower().find('beaglebone') >= 0:
                beaglebone = True

        # If we found both am355 and beaglebone, then it's a BBB
        if am355 and beaglebone:
            return {'name': 'bbb', 'system': 'AM335x'}
        else:
            return False

    # If that doesn't work, we're just going to go with "platform unknown!"
    except OSError:
        return False

def setup_device():
    ''' Handle creation of any necessary device tree overlays, etc.
    '''
    # First figure out what platform we're on
    platform_info = get_platform()

    try:
        if platform_info['name'] == 'bbb':
            # Grab the platform-specific setup library
            import platform_setup
            platform_setup.bbb_setup()
            # Return True for successful config
            return True
        else:
            # This currently cannot happen. But if it could, well...
            return False

    # If a keyerror or typeerror are thrown, then it's an unknown plaform.
    except (KeyError, TypeError):
        return False

def setup_generic():
    ''' Handles setting up of a generic device.
    '''
    warn(RuntimeWarning('Could not autodetect platform. Continuing with '
        'standard installation.'))
    return True

if __name__ == '__main__':
    # Since this is going to require escalation, let's go ahead and do the
    # device tree stuff first.
    # Run the setup_device. If it returns false, there was no device detected
    # and we should do a generic setup.
    if not setup_device():
        setup_generic()

    # Now go ahead and install the package
    setup(**metadata)