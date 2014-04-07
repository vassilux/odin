"""Core property classes"""
NULL = []
from basicproperty import propertied, defaults
from basictypes import registry
import new
try:
	from basicproperty import propertyaccel
except ImportError, err:
	propertyaccel = None

class BasicProperty (propertied.Propertied):
	"""The base class for all of our enhanced property classes

	A BasicProperty has two distinct levels of accessor-methods:

		The first level, comprised of the following methods (these
		were renamed in version 0.5 to match the standard descriptor
		API):
			__get__(self, client, klass)
			__set__(self, client, value)
			__delete__(self, client)
		allows you to override the entire get/set/delete process
		in your subclass.  Overriding these methods allows you to
		short-circuit around bounds checking and coercion.  You
		become responsible for implementing everything.

		The second level, comprised of the following methods:
			_getValue(self, client)
			_setValue(self, client, value)
			_delValue(self, client)
		allows you to override only the storage/retrieval process
		in your subclass without affecting the bounds checking or
		coercion functions of the property.  See: the MethodStore
		mix-in for an example of overriding just these methods.
	"""
	setDefaultOnGet = 1
	trueProperty = 1
	baseType = None
	boundaries = ()
	
	## Undefined by default, but possibly available attributes...
	# defaultValue
	# defaultFunction
	# friendlyName
	
	def __init__(
		self, name, documentation = "",
		**namedarguments
	):
		"""Create a new basic property object

		name -- name of the property, used for storage and reporting
		documentation -- appears in automated documentation systems

		baseType -- an object representing the base-type of the
			property's values.  May include the following values:

				coerce( value ) -- coerce value to acceptable type
				check( value ) -- check that given value is acceptable,
					return false if it is not.
				factories( ) -- return a list of factory functions/classes
					for creating new instances of the class
				dataType -- string specifying a data-type key for the
					values.  This specifier is entirely local to the
					properties system, with no neccessary relation to
					class or type names.  With that said, generally the
					values are the dotted-name of the class/type allowed
					for the property.
					
					Note: This can be a dotted name with the trailing
					items specifying more specific data types, so, for
					instance, str.long will use the "long string" editor if
					it's registered, or the "string" editor if not.
					
			if coerce is not present, the class should have an initialiser
			that allows passing a single value as the value to coerce.

			if check is not present, check will be done as
			isinstance( value, baseType).

			if factories is not present, factories will be assumed to be
			the baseType itself.
		
		defaultValue -- static value to be used as default, if not
			specified, not provided
		defaultFunction -- function with signature function( property,
			client ) which returns a dynamic default value
		setDefaultOnGet -- if true (default), then retrieving a
			default value causes the value to be explicitly set as the
			current value

		boundaries -- series of callable Boundary objects which are
			(if present) called for each set/getDefault in order to
			confirm that the given value abides by the boundaries
			defined.  Should generally only raise ValueError, TypeError,
			KeyError or AttributeError (or sub-classes of those) as
			appropriate to the boundary violation.

			Called as:
				boundary( value, property, client )
			note that the basictypes.boundary module defines a number
			of Boundary objects which are designed to be used in this
			field of the property.

		friendlyName -- user-friendly name for use in UIs and the like,
			defaults to the current value of name
		trueProperty -- if true, this property really does describe a
			property, that is, a descriptor for an attribute which is
			accessed using object.x notation.
			
			if false, this property is used to interact with the
			property system, but is not actually a property of an
			object (for instance when the object is an old-style class
			which cannot support properties, you can define virtual
			properties for use with the class)  The property system
			can examine the value of trueProperty to determine whether
			to use setattr(object,name,value) or call
			property.__set__(object, value) to use the property.


		Notes:
			You can specify _any_ name=value set to store a value, so,
			for instance, you could specify __get__ to override the
			__get__ method, or similarly _getValue or getDefault.

			Sub-classes may (and do) define extra name=value pairs to
			support extended functionality.  You will need to look at
			the sub-class's documentation for details on other
			significant attribute names.
		"""
		assert isinstance( name, (str,unicode)), """Property name is not a string or unicode value, was a %s"""%(type(name))
		self.name = name
		assert isinstance( documentation, (str,unicode)), """Property documentation is not a string or unicode value, was a %s"""%(type(documentation))
		self.__doc__ = documentation

		if namedarguments.has_key('defaultValue'):
			namedarguments[ 'default' ] = defaults.DefaultValue(
				namedarguments[ 'defaultValue' ]
			)
			del namedarguments[ 'defaultValue' ]
		elif namedarguments.has_key('defaultFunction'):
			namedarguments[ 'default' ] = defaults.DefaultCallable(
				namedarguments[ 'defaultFunction' ]
			)
			del namedarguments[ 'defaultFunction' ]
		elif namedarguments.has_key('default'):
			current = namedarguments.get('default')
			if not isinstance( current, defaults.Default ):
				namedarguments['default' ] = defaults.DefaultValue(current)
		propertied.Propertied.__init__( self, **namedarguments )

	### Storage customisation points
	def _getValue( self, client ):
		"""Perform a low-level retrieval of the "raw" value for the client

		The default implementation uses the property's name as a key
		into the client's __dict__ attribute.  Note that this will
		fail with objects using __slots__.
		"""
		return client.__dict__[ self.name ]
	def _setValue( self, client, value ):
		"""Perform a low-level set of the "raw" value for the client

		The default implementation sets the value using the property's
		name as a key in the client's __dict__ attribute.  Note that this
		will fail with objects using __slots__.
		"""
		# if the client has a __setattr__, it isn't getting called here
		# should we defer to it by default? I don't know...
		client.__dict__[ self.name ] = value
	def _delValue( self, client ):
		"""Perform a low-level delete of the value for the client

		The default implementation deletes the property's name 
		from the client's __dict__ attribute.  Note that this will
		fail with objects using __slots__.
		"""
		name = self.name
		try:
			del client.__dict__[ name ]
		except KeyError:
			raise AttributeError( '%r instance has no %r attribute'%(client.__class__.__name__, name) )

	### Type and bounds-checking customisation points
	def getFactories( self ):
		"""Attempt to determine the factory callables for this property"""
		baseType = self.getBaseType()
		if baseType:
			if hasattr( baseType, 'factories'):
				if callable(baseType.factories):
					return baseType.factories()
				else:
					return baseType.factories
			elif callable( baseType ):
				return [ baseType ]
		return []
	def getBaseType( self ):
		"""Get our base-type object or None if not set"""
		if isinstance(self.baseType, (str,unicode)):
			from basictypes import latebind
			self.baseType = latebind.bind( self.baseType )
		return registry.getDT( self.baseType )
	def getDataType( self ):
		"""Get our data-type string"""
		if hasattr( self, 'dataType' ):
			return self.dataType
		baseType = self.getBaseType()
		if baseType:
			if hasattr( baseType, 'dataType'):
				self.dataType = value = baseType.dataType
				return value
		return ""
		
	def coerce(self, client, value ):
		"""Attempt to convert the given value to an appropriate data type

		Tries to use the baseType's coerce function,
		failing that, calls the base type with the
		value as the first positional parameter.
		"""
		base = self.getBaseType()
		if base:
			if isinstance( value, base ):
				return value
			elif hasattr(base, 'coerce' ):
				return base.coerce( value )
			raise ValueError( """Couldn't automatically coerce value %r for property %s of object %s"""%(value, self, client))
		return value
	def check (self, client, value):
		"""Use our basetype to check the coerced value's type
		"""
		base = self.getBaseType()
		if base:
			if hasattr(base, 'check' ):
				return base.check( value )
			elif not isinstance( value, base ):
				return 0
		return 1

	### Type and bounds-checking machinery-enabling functions...
	def __get__( self, client, klass=None ):
		"""Retrieve the current value of the property for the client

		This function provides the machinery for default value and
		default function support.  If the _getValue method raises
		a KeyError or AttributeError, this method will attempt to
		find a default value for the property using self.getDefault
		"""
		try:
			if client is None:
				pass
			else:
				return self._getValue( client )
		except (KeyError, AttributeError):
			return self.getDefault( client )
		else:
			# client was None
			if klass:
				return self
			else:
				raise TypeError( """__get__ called with None as client and class arguments, cannot retrieve""" )
	def getDefault( self, client ):
		"""Get the default value of this property for the given client

		This simply calls the Default object registered as self.default,
		which, depending on whether defaultValue or defaultFunction was
		specified during initialisation, will return a value or the
		result of a function call.  If neither was specified, an
		AttributeError will be raised.
		"""
		if not hasattr( self, 'default' ):
			raise AttributeError( """Property %r doesn't define a default value for <%s object @ %s>"""%(self.name, type(client),id(client)))
		value = self.default( self, client )
		if self.setDefaultOnGet:
			if self.trueProperty:
				# allows __setattr__ hook to function,
				# but it's seriously ugly :(
				value = self.coerce( client, value )
				assert self.check ( client, value ), """Value %r is not of the correct type even after coercian for property %s"""%( value, self )
				if self.boundaries:
					self.checkBoundaries( value, client )
				setattr( client, self.name, value )
				return value
			else:
				return self.__set__( client, value )
		else:
			value = self.coerce( client, value )
			assert self.check ( client, value ), """Value %r is not of the correct type even after coercian for property %s"""%( value, self )
			return value
	def __set__( self, client, value ):
		"""Set the current value of the property for the client

		This function provides the machinery for coercion and
		bounds checking.  Before calling the _setValue method,
		__set__ calls self.coerce( client, value ), with the return
		value from the coercion becoming the value to be set.
		Coercion may raise TypeError or ValueError exceptions,
		and the application should be ready to catch these errors.

		Once coercion is finished, __set__ calls
		self.check( client, value ) to allow each boundary
		condition to check the current value.  The boundary
		conditions may raise BoundaryErrors (with the particular
		error classes generally being sub-classes of ValueError
		or TypeError).
		"""
		value = self.coerce( client, value )
		assert self.check ( client, value ), """Value %r is not of the correct type even after coercian for property %s"""%( value, self )
		if self.boundaries:
			self.checkBoundaries( value, client )
		self._setValue( client, value )
		return value
	def __delete__( self, client ):
		"""Delete the current value of the property for the client

		At the moment, this method does nothing beyond calling
		self._delValue( client ), as there does not appear to be
		any common feature required from __delete__.  The method is
		here primarily to maintain the consistency of the interface
		and allow for applications to override _delValue without
		worrying about losing future features added to __delete__.
		"""
		return self._delValue( client )

	def __repr__( self ):
		"""Get a representation of this property object"""
		return """<%s %s>"""%( self.__class__.__name__, repr(self.name) )
	__str__ = __repr__

	def getState( self, client ):
		"""Helper for client.__getstate__, gets storable value for this property"""
		return self._getValue(client)
	def setState( self, client, value ):
		"""Helper for client.__setstate__, sets storable value"""
		return self._setValue( client, value )

	def checkBoundaries( self, value, client=None ):
		"""Check given value against boundaries"""
		for boundary in self.boundaries:
			boundary( value, self, client )

if propertyaccel:
	for name in ('_getValue','__get__'):
		setattr( 
			BasicProperty,
			name,
			new.instancemethod( 
				getattr(propertyaccel,name),
				None,
				BasicProperty,
			)
		)


class MethodStore( object ):
	"""Mix-in class calling object methods for low-level storage/retrieval

	This mix-in class provides three attributes, setMethod, getMethod
	and delMethod.  You use the class by setting these attributes to
	the name of methods on your client with the following signatures:
		getMethod( )
		setMethod( value )
		delMethod( )

	You can set these attributes either by defining class-attributes
	to override the MethodStore class attributes, or by passing the named
	arguments "getMethod", "setMethod", "delMethod" to the property's
	__init__ method.  Note: these attributes are always strings, do not
	use function or instance method objects!

	If you have failed to provide one of the attributes, or have provided
	a null value (""), a NotImplementedError will be raised when you
	attempt to store/retrieve the value using that attribute.
	"""
	setMethod = ""
	getMethod = ""
	delMethod = ""
	trueProperty = 0

	def _getValue( self, client ):
		"""Perform a low-level retrieval of the "raw" value for the client

		This implementation forwards the request to
			getattr( client, self.getMethod )()
		An assert will be generated if self.getMethod is null
		"""
		assert self.getMethod, """MethodStore property %s hasn't specified a getMethod"""%(self)
		return getattr( client, self.getMethod )()
	def _setValue( self, client, value ):
		"""Perform a low-level set of the "raw" value for the client

		This implementation forwards the request to
			getattr( client, self.setMethod )( value )
		An assert will be generated if self.setMethod is null
		"""
		assert self.setMethod, """MethodStore property %s hasn't specified a setMethod"""%(self)
		return getattr( client, self.setMethod )( value )
	def _delValue( self, client ):
		"""Perform a low-level delete of the value for the client

		This implementation forwards the request to
			getattr( client, self.delMethod )( )
		An assert will be generated if self.delMethod is null
		"""
		assert self.delMethod, """MethodStore property %s hasn't specified a delMethod"""%(self)
		return getattr( client, self.delMethod )( )

class MethodStoreProperty( MethodStore, BasicProperty ):
	"""Class providing default MethodStore + BasicProperty operation"""

class Delegated( BasicProperty ):
	"""BasicProperty which delegates its operation to another object
	
	target -- property name used to retrieve the target (delegate)
	targetName -- property name on the target to which we delegate 
	"""
	setDefaultOnGet = 0
	target = BasicProperty(
		"target", """Target property name to which we delegate our operations""",
	)
	targetName = BasicProperty(
		"targetName", """Name on the target to which we delegate""",
	)
	def _getValue( self, client ):
		"""Perform a low-level retrieval of the "raw" value for the client

		This implementation forwards the request to
			getattr( client, self.getMethod )()
		An assert will be generated if self.getMethod is null
		"""
		return getattr( 
			getattr(client,self.target), 
			getattr(self,'targetName',self.name) 
		)
	def _setValue( self, client, value ):
		"""Perform a low-level set of the "raw" value for the client

		This implementation forwards the request to
			getattr( client, self.setMethod )( value )
		An assert will be generated if self.setMethod is null
		"""
		return setattr( 
			getattr(client,self.target), 
			getattr(self,'targetName',self.name),
			value,
		)
	def _delValue( self, client ):
		"""Perform a low-level delete of the value for the client

		This implementation forwards the request to
			getattr( client, self.delMethod )( )
		An assert will be generated if self.delMethod is null
		"""
		return delattr( 
			getattr(client,self.target), 
			getattr(self,'targetName',self.name) 
		)
