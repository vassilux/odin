"""Object for linearizing a node-graph to XML
"""
import types, cStringIO, operator, traceback, sys, struct
from xml.sax import saxutils
from copy_reg import dispatch_table
from pickle import whichmodule, PicklingError

class RootCellarError(PicklingError):
	"""Root error raised by the rootcellar lineariser"""
	def append( self, element ):
		"""Append an element to the stack"""
		if not hasattr( self, 'stack' ):
			self.stack = []
		self.stack.append( element )
	def __str__( self ):
		base = PicklingError.__str__( self )
		if hasattr( self, 'stack' ):
			stack = self.stack[:3]
			stack.reverse()
			base = "%s\nLinearisation Stack:\n\t%s"%(
				base,
				"\n\t".join(map(repr,self.stack[-3:]))
			)
		return base
			

__metatype__ = type

defaults = {\
'subelspacer':', ',\
'courtesyspace':' ',\
'curindent':'',\
'indent':'\t',\
'numsep':',',\
'full_element_separator':'\n',\
'mffieldsep':'\n',
# EndComments say: if more than this many lines are between node start
# and end, put a comment at the closing bracket saying what node/proto is
# being closed.
'EndComments': 10 \
}


def linearise( value, linvalues=defaults, **namedargs ):
	"""Linearise the given (node) value to a string"""
	l = Lineariser( linvalues, **namedargs)
	return l.linear( value )


def _findUnusedKey( dictionary, baseName ):
	"""Find an unused name similar to baseName in dict"""
	count = 1
	name = baseName
	while dictionary.has_key( name ):
		name = '%s%s'%(baseName, count )
		count += 1
	return name

class Generator( saxutils.XMLGenerator ):
	"""Friendly generator for XML code"""
	def startElement( self, name, attributes=None, **named ):
		"""Start a new element with given attributes"""
		if attributes is None:
			attributes = {}
		attributes.update( named )
		saxutils.XMLGenerator.startElement(
			self,
			name,
			self._fixAttributes(attributes)
		)
	def _fixAttributes( self, attributes=None ):
		"""Fix an attribute-set to be all unicode strings"""
		for key,value in attributes.items():
			if not isinstance( value, (str,unicode)):
				attributes[key] = unicode( value )
			elif isinstance( value, str ):
				attributes[key] = value.decode( 'latin-1' )
		return attributes

		
class Lineariser:
	'''
	A data structure & methods for linearising
	sceneGraphs, nodes, scripts and prototypes.
	Should be used only once as member vars are not
	cleared after the initial linearisation.
	'''
	volatile = 0
	protoalreadydone = {
		# already occupied by core-functionality tags...
		# block below populates us with our helpers...
		'property': 1,
		'globals':1,
		'global':1,
		'globalid':1,
		"globalversion":1,
		'tagname':1,
		'reference':1,
		'picklestate':1,
		'pickleargs':1,
		'picklereg':1,
		'rootcellar':1,
	}
	lowLevelHelpers = {}
	def registerHelper( cls, clientClass, helper ):
		"""Register a helper object with the linearise class"""
		name = clientClass.__name__.split('.')[-1]
		name = _findUnusedKey( cls.protoalreadydone, name )
		cls.lowLevelHelpers[clientClass] = helper
		cls.protoalreadydone[clientClass] = name
		cls.protoalreadydone[name] = clientClass
		# now integrate helper's sub-tags into our own...
		newSet = {}
		for key,name in getattr( helper, 'tagNames', {}).items():
			if cls.protoalreadydone.get(name) is not type(helper):
				newName = _findUnusedKey( cls.protoalreadydone, name )
				cls.protoalreadydone[ newName ] = type(helper)
			else:
				newName = name
			newSet[key] = newName
		helper.tagNames = newSet
	registerHelper = classmethod( registerHelper )
	
	def __init__(self, linvalues=None, alreadydone=None, encoding='utf-8', *args, **namedargs):
		self.encoding = encoding
		if linvalues is None:
			linvalues = defaults
		if namedargs:
			linvalues = linvalues.copy()
			linvalues.update( namedargs )
		self.linvalues = linvalues
		if alreadydone is None:
			self.alreadydone = {}
		else:
			self.alreadydone = alreadydone
		
	def linear(
		self, clientNode,
		buffer=None,
		skipProtos = None,
		*args, **namedargs
	):
		'''Linearise a node/object
		'''
		# prototypes in this dictionary will not be linearised
		self.skipProtos = {}
		# protobuffer is a seperate buffer into which the class definitions are stored
		self.protobuffer = cStringIO.StringIO()
		self.protogenerator = Generator( self.protobuffer, self.encoding )
		self.protogenerator.startDocument()
		self.protogenerator.startElement('rootcellar')
		self.protogenerator.startElement('globals')
		self.fullsep(1)
		# protoalreadydone is used in place of the scenegraph-specific
		# node alreadydone.  This allows us to push all protos up to the
		# top level of the hierarchy (thus making the process of linearisation much simpler)
		self.protoalreadydone = self.protoalreadydone.copy()
		# main working algo...
		self.typecache = {
		}
		self.buffer = buffer or cStringIO.StringIO()
		self.generator = Generator( self.buffer, self.encoding)
		self.alreadydone.clear()
		self.indentationlevel = 0
		self._linear( clientNode )
		del( self.typecache ) # to clear references to this node...
		self.alreadydone.clear()
		# side effect has filled up protobuffer for us
		self.protogenerator.endElement('globals')
		self.fullsep(1)
		self.generator.endElement('rootcellar')
		self.generator.endDocument()
		rval = self.protobuffer.getvalue() + self.buffer.getvalue()
		self.buffer.close()
		self.protobuffer.close()
		return rval

	### High-level constructs...
	def _class( self, clientNode):
		"""Linearise a class, or more precisely, a class-reference"""
		# check that we haven't yet done this prototype
		if self.protoalreadydone.has_key( clientNode ):
			return self.protoalreadydone.get( clientNode )
		# else, want to export a class-definition line at the top of the file...
		module,name = self.globalname( clientNode )
		tagName = _findUnusedKey(
			self.protoalreadydone,
			name,
		)
		self.protoalreadydone[tagName] = clientNode
		self.protoalreadydone[clientNode] = tagName

		position = self.protobuffer.tell()
		start = self.protogenerator.startElement
		end = self.protogenerator.endElement
		chars = self.protogenerator.characters
		start( "global" )
		start( "globalname" )
		chars( tagName )
		end( "globalname" )
		start( "globalid" )
		chars( "%s.%s"%(module, name) )
		end( "globalid" )
		if hasattr(clientNode,'__version__'):
			start( 'globalversion' )
			chars( clientNode.__version__ )
			end( "globalversion" )
		end( "global" )
		self.protobuffer.write( self.linvalues['full_element_separator'] )
		self.alreadydone[ clientNode ] = position, self.protobuffer.tell()
		return tagName

	def _Node( self, clientNode, *args,**namedargs):
		'''Linearise an individual node
		'''
		tagName = self._class( clientNode.__class__ )
		buffer = self.buffer
		# now calculate the representation of this node...
		position = buffer.tell()
		self.alreadydone[ id(clientNode) ] = (position,position)
		start = self.generator.startElement
		end = self.generator.endElement
		start( tagName, id=self.refName(clientNode) )
		self._indent()
		self.nodeContent( clientNode )
		self._dedent()
		self.fullsep()
		self.indent()
		end( tagName )
		self.alreadydone[ id(clientNode) ] = position, buffer.tell()
		return None
	def nodeContent( self, clientNode ):
		"""Export the contents of a given node"""
		start = self.generator.startElement
		end = self.generator.endElement
		if hasattr( clientNode, 'getProperties' ):
##			self.fullsep()
##			self.indent()
			self._properties( clientNode )
		elif hasattr( clientNode, '__getstate__' ):
			self.fullsep()
			self.indent()
			start( 'picklestate' )
			self._linear( clientNode.__getstate__(), volatile=1 )
			end( 'picklestate' )
		elif hasattr( clientNode, '__getinitargs__' ):
			self.fullsep()
			self.indent()
			start( 'pickleargs' )
			self._linear( clientNode.__getinitargs__(), volatile=1)
			end( 'pickleargs')
		elif dispatch_table.has_key( clientNode.__class__ ):
			self.fullsep()
			self.indent()
			start( 'picklereg' )
			reducer = dispatch_table.get( clientNode.__class__ )
			self._linear( reducer( clientNode ), volatile=1)
			end( 'picklereg')
		elif hasattr( clientNode, '__reduce__') and callable(clientNode.__reduce__):
			tup = clientNode.__reduce__()
			if len(tup) == 3:
				target,args,state = tup
			else:
				target,args = tup
				state = None
			self.fullsep()
			self.indent()
			start( 'picklereduce' )
			self._linear( target )
			self._linear( args, volatile=1 )
			self._linear( state, volatile=1 )
			end( 'picklereduce' )
		elif hasattr( clientNode, '__dict__'):
			self.fullsep()
			self.indent()
			start( 'picklestate' )
			self._linear( clientNode.__dict__, volatile=1 )
			end( 'picklestate' )
		else:
			raise RootCellarError( """Don't know how to store %r object"""%(
				clientNode,
			))
		
	def reference( self, target ):
		"""Reference an object"""
		if hasattr( target, '__class__'):
			refType = self._class( target.__class__ )
		else:
			refType = "class"
		self.generator.startElement( 'reference', id = self.refName(target), type=refType)
		self.generator.endElement( 'reference')
	def refName( self, target ):
		"""Get a reference id/name for a given object"""
		return hex(id(target))[2:].lower()
	def _properties(self, object ):
		"""Write out the attribute dictionary for an object"""
		properties = object.getProperties()
		propertyTags = []
		for property in properties:
			if not getattr( property, 'volatile', None):
				getState = getattr( property, 'getState', None )
				try:
					if getState:
						value = getState( object )
					else:
						value = property.__get__( object )
				except (AttributeError,KeyError):
					# no non-default value set, so ignore...
					pass
					#print 'skipping', property.name
					# XXX strip values where value is default? option maybe?
				else:
					propertyTags.append( (property, value ) )
		start = self.generator.startElement
		end = self.generator.endElement
		for property, value in propertyTags:
			self.fullsep()
			self.indent()
			start( 'property', {"name":property.name} )
			self.fullsep()
			self._indent()
			self.indent()
			self._linear( value )
			self._dedent()
			self.fullsep()
			self.indent()
			end( 'property' )
			

	### Utility functions...
	def _dedent( self ):
		self.indentationlevel = self.indentationlevel-1
		self.linvalues['curindent'] = self.linvalues['indent']*self.indentationlevel
	def _indent( self, exact = None ):
		if exact is not None:
			self.indentationlevel = exact
		else:
			self.indentationlevel = self.indentationlevel+1
		self.linvalues['curindent'] = self.linvalues['indent']*self.indentationlevel
	def fullsep( self, proto=0 ):
		"""Add full seperator to the indicated buffer"""
		if proto:
			buffer = self.protobuffer
		else:
			buffer = self.buffer
		buffer.write( self.linvalues['full_element_separator'] )
	def indent( self, proto=0 ):
		"""Add current indent to the indicated buffer"""
		if proto:
			buffer = self.protobuffer
		else:
			buffer = self.buffer
		buffer.write( self.linvalues['curindent'])

	def _linear( self, clientNode, volatile=0):
		'''Linearise a particular client node of whatever type by dispatching to
		appropriate method...'''
		self.volatile = volatile
		try:
			if isinstance( clientNode, (type, types.ClassType)):
				helper = self.lowLevelHelpers.get( type )
			else:
				helper = self.lowLevelHelpers.get( type(clientNode))
			if helper:
				return helper( clientNode, self )
			elif self.alreadydone.has_key( id(clientNode)) and not volatile:
				return self.reference( clientNode )
##			elif isinstance( type(clientNode), (type, types.ClassType)):
##				return self.lowLevelHelpers.get( type )( clientNode, self )
			else:
				return self._Node( clientNode )
		except RootCellarError, err:
			err.append( clientNode )
			raise
		except Exception:
			f = cStringIO.StringIO()
			traceback.print_exc( file = f )
			error = f.getvalue()
			raise RootCellarError(
				"""Failure attempting to linearise %r: %s"""%(
					clientNode,
					error,
				)
			)

	def globalname( self, client):
		"""Try to find the name for the client"""
		name = getattr( client, '__name__', None )
		if not name:
			raise ValueError( """Attempt to put %r in the root cellar, has no __name__ attribute, so can't create a global reference to it"""%( client,))
		module = getattr( client, '__module__', None )
		if not module:
			module = whichmodule( client, name )
		# sanity check...
		try:
			__import__(module)
			mod = sys.modules[module]
			klass = getattr(mod, name)
		except (ImportError, KeyError, AttributeError), error:
			raise RootCellarError(
				"""Can't store %r: can't import %s.%s: %r"""%(
					client, module, name, error
				)
			)
		else:
			if klass is not client:
				raise RootCellarError(
					"""Can't store %r (id=%s): importing %s.%s does not give the same object, gives %r (id=%s)"""%(
						client, id(client), module, name, klass, id(klass),
					)
				)
		return module,name


class LineariserHelper(object):
	clientClasses = ()
	tagNames = {}
	def __call__( self, value, lineariser ):
		"""Linearise the value using given lineariser"""
		if not self.doRef( value, lineariser ):
			position = lineariser.buffer.tell()
			self.do( value, lineariser )
			lineariser.alreadydone[ id(value) ] = position,lineariser.buffer.tell()
	def doRef( self, value, lineariser ):
		"""Check if we can just reference this value"""
		if lineariser.alreadydone.has_key( id(value)) and not lineariser.volatile:
			lineariser.reference(value)
			return 1
		return 0
	def do( self, value, lineariser ):
		"""Do the primary work of linearising"""
		
class NoneLin(LineariserHelper):
	clientClasses = [types.NoneType]
	tagNames = {'none':'none'}
	def doRef( self, value, lineariser ):
		"""Check if we can just reference this value"""
		return 0
	def do( self, value, lineariser ):
		lineariser.generator.startElement( self.tagNames.get('none') )
		lineariser.generator.endElement( self.tagNames.get('none') )

class IntLin(LineariserHelper):
	clientClasses = [int,long,float]
	tagNames = {}
	maxRefSize = 18446744073709551616L
	minRefSize = -18446744073709551616L
	def doRef( self, value, lineariser ):
		"""Check if we can just reference this value"""
		if isinstance( value, long):
			if value > self.maxRefSize or value < self.minRefSize:
				return super( IntLin, self).doRef(value, lineariser)
		return 0
	def do( self, value, lineariser ):
		tagName = lineariser._class( type(value) )
		if isinstance( value, long) and value > self.maxRefSize or value < self.minRefSize:
			lineariser.generator.startElement( tagName, id=lineariser.refName(value) )
		else:
			lineariser.generator.startElement( tagName )
		lineariser.generator.characters( repr(value))
		lineariser.generator.endElement( tagName )
class StringLin(LineariserHelper):
	clientClasses = [str, unicode]
	tagNames = {}
	minRefLength = 64
	def doRef( self, value, lineariser ):
		"""Check if we can just reference this value"""
		if len(value) > self.minRefLength:
			return super( StringLin, self).doRef(value, lineariser)
		return 0
	def do( self, value, lineariser ):
		hexID = lineariser.refName( value)
		tagName = lineariser._class( type(value) )
		if len(value) > self.minRefLength:
			lineariser.generator.startElement( tagName, id=hexID )
		else:
			lineariser.generator.startElement( tagName )
		if isinstance( value, str ):
			value = value.decode( 'latin-1')
		lineariser.generator.characters( value)
		lineariser.generator.endElement( tagName )
class SequenceLin(LineariserHelper):
	clientClasses = [list, tuple]
	tagNames = {'li':'li'}
	def do( self, value, lineariser ):
		tagName = lineariser._class( type(value) )
		start = lineariser.generator.startElement
		end = lineariser.generator.endElement
		start( tagName, id=lineariser.refName(value))
		if value:
			lineariser._indent()
			lineariser.fullsep()
			for item in value:
				lineariser.indent()
				lineariser._linear( item )
				lineariser.fullsep()
			lineariser._dedent()
			lineariser.indent()
		end( tagName )
class MappingLin(LineariserHelper):
	clientClasses = [dict]
	tagNames = {'key':'key','val':'val'}
	def do( self, value, lineariser ):
		tagName = lineariser._class( type(value) )
		start = lineariser.generator.startElement
		end = lineariser.generator.endElement
		start( tagName, id=lineariser.refName(value))
		if value:
			lineariser._indent()
			lineariser.fullsep()
			for key,item in value.items():
				lineariser.indent()
				start(self.tagNames.get('key'))
				lineariser._linear( key )
				end( self.tagNames.get('key'))
				lineariser.fullsep()
				lineariser._indent()
				lineariser.indent()
				start(self.tagNames.get('val'))
				lineariser._indent()
				lineariser._linear( item )
				lineariser._dedent()
				end( self.tagNames.get('val'))
				lineariser._dedent()
				lineariser.fullsep()
			lineariser._dedent()
			lineariser.indent()
		end( tagName )

class GlobalLin( LineariserHelper):
	clientClasses = [type, types.ClassType,type, types.FunctionType,types.BuiltinFunctionType]
	tagNames = {'globalref':"globalref"}
	def do( self, client, lineariser ):
		start = lineariser.generator.startElement
		end = lineariser.generator.endElement
		lineariser._class( client )
		start(
			self.tagNames.get('globalref'),
			tagname= lineariser._class( client ),
			id=lineariser.refName(client),
		)
		end( self.tagNames.get('globalref') )



for cls in NoneLin, IntLin,StringLin,SequenceLin,MappingLin, GlobalLin:
	for clientClass in cls.clientClasses:
		Lineariser.registerHelper( clientClass, cls() )

	