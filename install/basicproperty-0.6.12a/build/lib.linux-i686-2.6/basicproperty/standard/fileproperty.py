"""XXX Lots left to do here

* Create a more efficient way of specifying the various boundaries
* Support for saving/restoring open file connections
* Support for defining UI-specific values in the property
	* Should overwrite silently?
	* Should append extension if doesn't match a glob
	* Extensions/types for use in selection dialogs
	* Allow creation of intermediate directories (require parent to exist or not)
* Should have basic support in form of a "Path" class for
  Interacting with the paths in an object-oriented way
	* Support for standard os and os.path queries
		* listdir
		* isfile/dir/symlink
		* create sub-directory
		* join-with-string to get sub-path
		* absolute-path -> Path object
			* support .. and . directory resolution (and elimination)
	* Mime-types
	* ftype and assoc values
	* comparisons
		* parent, child -> boolean
		* shared path -> fragments
		* shared root -> boolean
	* open( *, ** )
		* for directories, create/open file based on standard file() call
		* for zipfile-embedded paths, use zipfile transparently to create/open sub-file
		* for directories, create the directory (possibly recursively)
		* for files, error normally, possibly useful for things
		  like zipfiles and db-interface files which want to provide
		  directory-like interface
	* file( name ) -> Path
		* create a sub-file path
	* sub( name ) -> Path
		* create a sub-directory path

	* newfile( name, *, **)
	* newsub( name, *, ** )
		* create a new sub-directory Path object
		* for real directories, also
* Eventually support zipfiles as Directory paths
"""
from basicproperty import basic
from basictypes.vfs import filepath
import os

class MustExistBoundary( boundary.Boundary ):
	"""Require that a path exist"""
	def __call__(self, value, property, client):
		"""Check value against boundary conditions"""
		testValue = normalise(value)
		if not os.path.exists( testValue ):
			raise boundary.BoundaryValueError(
				property, self, client, value,
				"""This property requires an already-existing path.
  The path specified: %s
  Resolves to: %s
  Which does not appear to exist."""%( repr(value), repr(testValue))
			)

class MustNotExistBoundary( boundary.Boundary ):
	"""Require that a path not exist"""
	def __call__(self, value, property, client):
		"""Check value against boundary conditions"""
		testValue = normalise(value)
		if os.path.exists( testValue ):
			raise boundary.BoundaryValueError(
				property, self, client, value,
				"""This property requires a path which doesn't currently exist
  The path specified: %s
  Resolves to: %s
  Which does not appear to exist."""%( repr(value), repr(testValue))
			)

class IsFileBoundary( boundary.Boundary ):
	"""Require that the path, if it points to anything, points to a file"""
	def __call__(self, value, property, client):
		"""Check value against boundary conditions"""
		testValue = normalise(value)
		if os.path.exists( testValue ) and not os.path.isfile(testValue):
			raise boundary.BoundaryValueError(
				property, self, client, value,
				"""This property can only point to a file, not diretories or symbolic links
  The path specified: %s
  Resolves to: %s
  Which, though it exists, does not appear to be a file."""%( repr(value), repr(testValue))
			)
	
class IsDirBoundary( boundary.Boundary ):
	"""Require that the path, if it points to anything, points to a directory"""
	def __call__(self, value, property, client):
		"""Check value against boundary conditions"""
		testValue = normalise(value)
		if os.path.exists( testValue ) and not os.path.isdir(testValue):
			raise boundary.BoundaryValueError(
				property, self, client, value,
				"""This property can only point to a directory, not files or symbolic links
  The path specified: %s
  Resolves to: %s
  Which, though it exists, does not appear to be a directory."""%( repr(value), repr(testValue))
			)

class GlobBoundary( boundary.Boundary ):
	"""Require that the path match a glob specification (fnmatch)"""
	def __init__(self, specifier="*.*"):
		"""Initialize the boundary with the glob/fnmatch specifier
		"""
		self.specifier= specifier
	def __call__(self, value, property, client):
		"""Check value against boundary conditions"""
		import fnmatch
		if not fnmatch.fnmatch( value, self.specifier ):
			raise boundary.BoundaryValueError(
				property, self, client, value,
				"""This property must match the shell-pattern %s
  The path specified: %s
  does not match this pattern."""%( repr(value), )
			)
	

class PathProperty( basic.BasicProperty ):
	"""Representation of a path as a property"""
	baseType = filepath.FilePath

class FilePathProperty( PathProperty ):
	"""Representation of a file path as a property"""
	boundaries = [ IsFileBoundary() ]

class DirPathProperty( PathProperty ):
	"""Representation of a directory path as a property"""
	boundaries = [ IsFileBoundary() ]


def normalise( path ):
	"""Normalise path (and make it absolute"""
	try:
		return os.path.normcase(
			os.path.normpath(
				os.path.expanduser(
					os.path.expandvars(
						path
					)
				)
			)
		)
	except:
		return path

