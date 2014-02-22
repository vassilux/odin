#! /usr/bin/env python
from pkg_resources import Requirement, resource_filename

from setuptools import setup, find_packages, Extension
setup(
    name = "odinsys",
    version = "0.1",
    packages = find_packages(exclude="test"),
    scripts = ['bin/run.py'],
    data_files = [('conf', ['odinsys.sample.conf', 'odinsyslogger.sample.conf'])],

    # Project uses reStructuredText, so ensure that the docutils get
    # installed or upgraded on the target machine
    install_requires = ['docutils>=0.3', 'Twisted>=12.3.0',
    'argparse>=1.2.1', 'basicproperty>=0.6.12a', 'hiredis>=0.1.1',
    'mongoengine>=0.7.9', 'paramiko>=1.9.0', 'psutil>=1.0.1',
    'pycrypto>=2.6', 'pymongo>=2.4.2', 'redis>=2.7.2', 'starpy>=1.0.2',
    'zope.interface>=4.0.5'],

    package_data = {
        # If any package contains *.txt or *.rst files, include them:
        '': ['./config/*.conf', './docs/*.ini'],
    },

    # metadata for upload to PyPI
    author = "vassilux",
    author_email = "vassili.gontcharov@gmail.com",
    description = "This is an monitroing of a system informations",
    license = "MIT",
    keywords = "python odin system monitoring",
    url = "http://esifrance.net/",

)

def copyConfig():
    '''copyConfig()
Copies samples configuration if necessary to /etc/odinsys directory.'''
    from pkg_resources import Requirement, resource_filename
 
    # Get our file.
    filename_odinsys = resource_filename(Requirement.parse("odinsys"),
                                            "config/odinsys.sample.conf")

    filename_odinsys_log = resource_filename(Requirement.parse("odinsys"),
                                            "config/odinsyslogger.sample.conf")
 
    try:
        import shutil
 
        # Create the directory.
        if not os.path.exists("/opt/odinsys"):
            os.mkdir("/opt/odinsys")
 
        # Copy the configuration. Don't clobber existing files.
        if not os.path.exists("/etc/odinsys/odinsys.conf"):
            shutil.copyfile(filename_odinsys, "/etc/odinsys/odinsys.conf")

        if not os.path.exists("/etc/odinsys/odinsyslogger.conf"):
            shutil.copyfile(filename_odinsys_log, "/etc/odinsys/odinsyslogger.conf")
 
    except IOError:
        print "Unable to copy configuration file to /etc/odinsys directory."
