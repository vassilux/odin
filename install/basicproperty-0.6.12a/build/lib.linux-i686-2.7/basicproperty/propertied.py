"""Generic services for propertied objects"""

class Propertied( object ):
	"""Base class providing support for property-using objects

	The Propertied class provides a number of basicproperty
	support features which are helpful in many situations.
	
	These features are not required by the properties, instead
	they are common services which can be provided because of
	the properties, such as automatic cloning, fairly intelligent
	repr representations, and automatic initialization of properties
	from named initialization arguments.  The class also provides
	some basic introspection features.
	"""
	def __init__( self, *arguments, **namedarguments ):
		"""Propertied object initialisation, allows passing in initial values for properties by name"""
		for name, value in namedarguments.items():
			setattr(self, name, value )
		super( Propertied, self).__init__(*arguments)
	def __str__( self ):
		"""Get a friendly representation of the object"""
		return "%s( @%s )"%( self.__class__.__name__, id(self) )
		
	def getProperties( cls ):
		"""Get the BasicProperty properties for a particular object's class"""
		import inspect
		from basicproperty.basic import BasicProperty
		def isABasicProperty( object ):
			"""Predicate  which checks to see if an object is a property"""
			return isinstance( object, BasicProperty )
		return dict(getmembers( cls, isABasicProperty)).values()
	getProperties = classmethod( getProperties )

	def clone( self, ** newValues ):
		"""Clone this object, with optional new property values

		This method calls the __init__ method of your class with
		the current property values of your class.  Providing newValues
		(a dictionary) overrides property settings with new values.
		"""
		values = self.getCloneProperties()
		values.update( newValues )
		return self.__class__( **values )
	def getCloneProperties( self ):
		"""Get properties dictionary (key:value) for use in cloning of the instance

		By default you get getProperties()' values, with an
		attempt made to use the property's name, then the property's
		direct "__get__" method.
		"""
		values = {}
		for descriptor in self.getProperties():
			try:
				if descriptor.trueProperty:
					values[ descriptor.name ] = getattr( self, descriptor.name )
				else:
					values[ descriptor.name ] = descriptor.__get__( self, type(self) )
			except (AttributeError, ValueError, TypeError):
				pass
		return values

	def toString(self, indentation= "", alreadyDone = None, indentString='  '):
		"""Get a nicely formatted representation of this object

		This version assumes that getProperties returns
		the list of properties which should be presented,
		it recursively calls it's children with greater
		indents to get their representations.

		indentation -- current string indentation level
		alreadyDone -- set of object ids which are already finished

		XXX Needs a far better API, likely a stand-alone class
			without the automatic inheritance problems here :(
		"""
		properties = self.getProperties()
		if alreadyDone is None:
			alreadyDone = {}
		if alreadyDone.has_key( id(self) ):
			if hasattr( self, 'name' ):
				return """%s( name = %r)"""%( self.__class__.__name__, self.name)
			return """<Already Done %s@%s>"""%(self.__class__.__name__, id(self))
		alreadyDone[id(self)] = 1
		def sorter( x,y ):
			if x.name == 'name':
				return -1
			if y.name == 'name':
				return -1
			return cmp( x.name, y.name )
		def reprChild( x, indentation= "", alreadyDone=None ):
			"""Get representation of child at indentation level if possible"""
			if hasattr( x, 'toString'):
				try:
					return x.toString(indentation=indentation, alreadyDone=alreadyDone)
				except TypeError:
					# for instance if the object is a class
					pass
			return repr(x)
		properties.sort( sorter )
		fragments = ['%s('%(self.__class__.__name__)]
		indentation = indentation + indentString
		dictionary = self.__dict__
		for property in properties:
			if dictionary.has_key( property.name ):
				value = dictionary.get( property.name )
				if (
					hasattr( property, 'default' ) and 
					hasattr( property.default, 'value' ) and 
					property.default.value == value 
				):
					pass
				elif isinstance( value, list ):
					fragments.append(
						'%s%s = ['%(
							indentation,
							property.name,
					))
					indentation = indentation + indentString
					for item in value:
						fragments.append( '%s%s,'%(indentation,reprChild( item, indentation, alreadyDone)))
					indentation = indentation[:-(len(indentString))]
					fragments.append( '%s],'%(indentation))
				else:
					fragments.append(
						'%s%s = %s,'%(
							indentation,
							property.name,
							reprChild( value, indentation, alreadyDone )
					))
		indentation = indentation[:-(len(indentString))]
		fragments.append( '%s)'%(indentation))
		return "\n".join(fragments)


def getmembers(object, predicate=None):
	"""Version of inspect.py which catches keys not available from object"""
	results = []
	for key in dir(object):
		try:
			value = getattr(object, key)
		except AttributeError, err:
			pass
		else:
			if not predicate or predicate(value):
				results.append((key, value))
	results.sort()
	return results
	
