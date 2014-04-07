from basicproperty import common, propertied, basic

class Simple( propertied.Propertied ):
	count = common.IntegerProperty(
		"count", """Count some value for us""",
		defaultValue = 0,
	)
	names = common.StringsProperty(
		"names", """Some names as a list of strings""",
	)
	mapping = common.DictionaryProperty(
		"mapping", """Mapping from name to number""",
		defaultValue = [
			('tim',3),
			('tom',4),
			('bryan',5),
		],
	)
	def __repr__( self ):
		className = self.__class__.__name__
		def clean( value ):
			value = value.splitlines()[0]
			if len(value) > 30:
				value = value[:27] + '...'
			return value
		props = ", ".join([
			'%s=%s'%(prop.name, repr(prop.__get__(self)))
			for prop in self.getProperties()
			if hasattr(self,prop.name)
		])
		return '<%(className)s %(props)s>'%locals()
	__str__ = __repr__

s = Simple()
s.names.append( 'this' )
s2 = s.clone( count=500 )
s.names.append( 23 )
s.names.append( u'\xf0' )
s.mapping[ 'kim' ] = 32
s.count += 1
print s
print s2