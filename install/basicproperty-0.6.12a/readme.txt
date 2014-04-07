BasicTypes and BasicProperty

What Is It:

	A rapid application development framework based on
	Python 2.2 rich types and properties.  This package
	provides the Python developer with a mechanism for
	easily declaring business-domain objects with rich,
	self-documenting properties.  This allows for 
	implementing "naked objects", or objects which 
	directly model the problem domain and are immediately
	visible to the end-user.

		basicproperty -- Python 2.2 property sub-classes
			Provide a framework for higher-level property classes
			which substantially automate the bookkeeping of
			type checking, type coercion, bounds checking,
			and storage of data values.
			
		basictypes -- A collection of class interfaces and
			base-class definitions which describe the meta-
			data required to interact with the data-types in
			an intelligent manner.

Installation:

	The homepage for the distribution is:

		http://basicproperty.sourceforge.net/

	You'll need to install the following dependencies before
	installing the wxPython properties distribution:

		Python 2.2(.1) or above
			http://www.python.org/

		[optional]
		mx.DateTime (part of the mx.Base distribution)
			http://www.egenix.com/files/python/eGenix-mx-Extensions.html#Download-mxBASE
			Presently most of the date-specific code relies on
			the mx.DateTime extension library.  This is largely
			an artifact of the original project from which the
			properties distribution was derived.  Making this
			dependency non-critical is an open project.
			
	To install the properties distribution from the source archive,
	you will use the standard python distutils approach.

		Unzip the source archive (for example, properties-0.5.7a.zip)
		into a temporary directory.  Be sure to maintain the internal
		directory structure of the zip file.

		Run:  python setup.py install
			Note: There is currently an error in the installer which
			causes the installation of the source graphics for the
			collection editors to fail.  As these are merely source
			files (the images are compiled into Python modules), the
			error is non-critical, and the message can be ignored.

	To install the properties distribution from CVS, the recommended
	approach is:

		check out the properties "module" (WinCVS term) from CVS into
		some directory on your hard disk (the location is unimportant)
		
			This will create a directory "properties" with subdirectories
			named wxprop, wxoo, and basicproperty.

		add the properties directory created in the previous step to
		your PythonPath.  The easiest way to do this is to add a file
		to your Python/Lib directory named properties.pth containing a
		single line specifying the properties directory.

Testing/Demonstration:

	basicproperty/tests/test.py will run the basicproperty test suite
	(which is currently fairly spotty).

