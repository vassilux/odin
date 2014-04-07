"""Holders for property default values/functions

The default object simply provides an interface for
different approaches to defining default arguments.
The current implementation provides static and
dynamic default values.
"""

class Default( object ):
	"""Abstract holder for a default-value or function

	This is the base class for property default
	classes.  It is primarily an interface definition.
	"""
	def __init__( self, value ):
		"""Initialize the Default holder

		value -- the base value stored in the
			object, see sub-classes for semantics
			of how the object is treated.
		"""
		self.value = value
	def __call__( self, property, client ):
		"""Return appropriate default value

		This just returns the results of:
			self.get( property, client )
		"""
		return self.get( property, client )
	def get( self, property, client ):
		"""Get the value"""
		raise AttributeError( """Object %s does not currently have a value for property %s"""%( repr(client), property.name ))

class DefaultValue( Default ):
	"""A holder for a default value

	The default value is returned without modification,
	so using mutable objects will retrieve the same
	instance for all calls to get()
	"""
	def get( self, property, client ):
		"""Get the value unmodified"""
		return self.value

class DefaultCallable( Default ):
	"""A holder for a callable object producing default values

	The callable object is called with the signature:
	
		callable( property, client )

	where client is the instance object and property
	is the BasicProperty itself.
	"""
	def get( self, property, client ):
		"""Return the result of our callable value"""
		return self.value( property, client )
	def __init__( self, value ):
		"""Initialize the Default holder

		value -- the base value stored in the
			object, see sub-classes for semantics
			of how the object is treated.
		"""
		self.value = value
		self.get = value
	
