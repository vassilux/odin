"""Completely unfinished XML encoder"""
from basicproperty import basic, common, boundary, propertied

class Tag (propertied.Propertied):
	"""Represents a particular tag within a document"""
	name = common.StringProperty(
		"name", "The name of the tag",
		defaultValue = "",
	)
	attributes = common.DictionaryProperty (
		"attributes", """The in-tag attributes of the tag""",
		defaultFunction = lambda x,y: {},
	)
	content = common.ListProperty (
		"content", """The content (children) of the tag""",
		setDefaultOnGet = 1,
		defaultFunction = lambda x,y: [],
	)
	def __cmp__( self, other ):
		"""Compare this tag to another"""
		if not isinstance(other, Tag):
			return -1
		if other.name != self.name:
			return cmp( self.name, other.name)
		if other.attributes != self.attributes:
			return cmp( self.attributes, other.attributes)
		if other.content != self.content:
			return cmp( self.content, other.content)
		return 0
	def __repr__( self ):
		"""Create a decent representation of this tag"""
		fragments = []
		name = self.name.decode().encode('utf-8')
		fragments.append( "<"+name )
		for key, value in self.attributes.items ():
			fragments.append ("""%s=%r"""%(key, value))
		fragments = [ " ".join(fragments)]
		if self.content:
			fragments.append(">")
			for item in self.content:
				if isinstance(item, str):
					fragments.append(item)
				else:
					fragments.append(repr(item))
			fragments.append ("</%s>"%(name))
		else:
			fragments.append ("/>")
		return "".join(fragments)
		

class Storage (object):
	def tag(self, name, content = None, **attributes):
		if content is not None:
			return Tag (name = name, content = content, attributes = attributes)
		return Tag (name = name, attributes = attributes)


class Encoder (object):
	"""Base class for all encoder objects"""
	def __call__( self, value, storage):
		"""Encode the value for the storage"""

class PrimitiveEncoder(Encoder):
	"""Encoder for a primitive object-type

	This will include objects such as:
		integer, long, float
		string, Unicode
		boolean
	and lists/sequences of objects.
	"""

class StringEncoder (PrimitiveEncoder):
	"""Encoder for string values"""
	def __call__( self, value, storage):
		"""Encode the value for the storage"""
		tag = storage.tag( "str", enc = "utf-8")
		if isinstance (value, str):
			tag.content.append( value.decode().encode( 'utf-8' ) )
		elif isinstance( value, unicode):
			tag.content.append( value.encode( 'utf-8' ) )
		else:
			raise ValueError ("""Attempt to encode non-string, non-Unicode object with StringEncoder: %r"""%(value,))
		return tag
		
class NumberEncoder (PrimitiveEncoder):
	"""Encoder for numeric values"""

class DateEncoder (PrimitiveEncoder):
	"""Encoder for mxDateTime values"""

class PropertiedEncoder (Encoder):
	"""Encoder for a Propertied-object sub-class"""

