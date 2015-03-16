''' hwiopy: A common API for hardware input/output access.

hwiopy, "hardware input/output, python", is a general purpose IO library 
intended to provide a common, simple python API to physical systems, 
particularly ones running embedded linux. The hope is to allow a single, 
unified codebase to run on multiple hardware platforms with minimal (if any) 
modification. Early development targets include the Beaglebone Black and 
Raspberry Pi.
'''

# Bootstrap setuptools
import ez_setup
ez_setup.use_setuptools()

# Import global dependencies required for setup.py
from setuptools import setup, find_packages

metadata = dict(
    name = 'hwiopy',
    version = '0.0.1.dev1',
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
        'License :: OSI Approved :: GNU Lesser General Public License ' \
            'v2.1 (LGPLv2.1)',
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
    install_requires = ['json', 'struct', 'mmap', 'io', 'pkg_resources'],
    package_data = {
        # Include any .json files in the maps directory
        'hwiopy': ['maps/*.json'],
    })

def get_platform():
    ''' Figures out what platform the library is being installed onto for 
    deciding what install script to run.
    '''
    pass

def check_dtc():
    ''' Checks for capability to run the device tree compiler.
    '''
    pass

    # ~/
    # wget -c https://raw.github.com/RobertCNelson/tools/master/pkgs/dtc.sh
    # chmod +x dtc.sh
    # ./dtc.sh

def setup_device():
    ''' Handle creation of any necessary device tree overlays, etc.
    '''
    pass

if __name__ == '__main__':
    setup_device()
    setup(**metadata)