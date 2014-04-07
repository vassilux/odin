#!/usr/bin/env python
"""Installs properties using distutils

Run:
	python setup.py install
to install the packages from the source archive.
"""
import os, sys
from setuptools import setup, find_packages, Extension

if __name__ == "__main__":
	from sys import hexversion
	if hexversion >= 0x2030000:
		# work around distutils complaints under Python 2.2.x
		extraArguments = {
			'classifiers': [
				"""License :: OSI Approved :: BSD License""",
				"""Programming Language :: Python""",
				"""Topic :: Software Development :: Libraries :: Python Modules""",
				"""Intended Audience :: Developers""",
			],
			'download_url': "https://sourceforge.net/project/showfiles.php?group_id=87034",
			'keywords': 'descriptor,property,basicproperty,coerce,propertied,enumeration',
			'long_description' : """Core data-types and property classes

BasicProperty and BasicTypes provide the core datatypes for
both wxoo and the PyTable RDBMS Wrapper project.
""",
			'platforms': ['Any'],
		}
	else:
		extraArguments = {
		}

	setup (
		name = "basicproperty",
		version = "0.6.12a",
		description = "Core data-types and property classes",
		author = "Mike C. Fletcher",
		author_email = "mcfletch@users.sourceforge.net",
		url = "http://basicproperty.sourceforge.net/",
		license = "BSD-style, see license.txt for details",
		packages = find_packages(),
		include_package_data = True,
		zip_safe = False,

		ext_modules=[
			Extension("basicproperty.propertyaccel", [
				os.path.join( 
					'basicproperty', 'accellerate', "propertyaccel.c"
				)
			]),
		],
		**extraArguments
	)
	
