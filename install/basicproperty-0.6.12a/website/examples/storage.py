class Original( object ):
	currentState = 3
	def __getattr__( self, key ):
		if key != 'currentState':
			if self.currentState == 3:
				try:
					return self.__dict__[key]
				except KeyError:
					pass
			elif self.currentState == 4:
				try:
					return self.__dict__['someSource'][key]
				except KeyError:
					pass
		raise AttributeError( """%s instance has no %r attribute"""%(
			self.__class__.__name__, key,
		))

from basicproperty import common, basic
class StateBased( object ):
	"""Mix in: use client.someSource as source if currentState==4"""
	def _getValue( self, client ):
		"""Called by __get__ of basic.BasicProperty"""
		assert self.name not in ('currentState','someSource'), """StateBasedProperty created with %r name!"""%(self.name, )
		source = self.getClientSource( client )
		return source[ self.name ]
	def _setValue( self, client, value ):
		assert self.name not in ('currentState','someSource'), """StateBasedProperty created with %r name!"""%(self.name, )
		source = self.getClientSource( client )
		source[ self.name ] = value
		return value
	def getClientSource( self, client ):
		if client.currentState == 3:
			return client.__dict__
		elif client.currentState == 4:
			return client.someSource
		else:
			raise TypeError( """%s instance found with inconsistent currentState %r"""%(
				client.__class__.__name__, client.currentState,
			))
class StateBasedProperty( StateBased, basic.BasicProperty ):
	"""Simple state-based property"""
class DictStateBasedProperty( StateBased, common.DictionaryProperty ):
	"""A dictionary-typed state-based property"""

class WithProps( object ):
	currentState = common.IntegerProperty(
		"currentState", """The current state of this instance""",
		defaultValue = 3,
	)
	someSource = common.DictionaryProperty(
		"someSource", """Source for properties in state 4""",
	)

	someProp = StateBasedProperty(
		"someProp", """A state-aware generic property""",
		defaultFunction = lambda prop, client: client.__class__.__name__,
		setDefaultOnGet = 0,
	)
	someOtherProp = DictStateBasedProperty(
		"someOtherProp", """A state-aware dictionary property (with automatic default""",
	)

if __name__ == "__main__":
	w = WithProps()
	print 'currentState %r someSource %r'%( w.currentState, w.someSource )
	print 'someProp %r someOtherProp %r'%( w.someProp, w.someOtherProp )
	print
	print 'changing the properties with same state'
	w.someProp = 32
	w.someOtherProp[ 'this' ] = 'them'
	print 'currentState %r someSource %r'%( w.currentState, w.someSource )
	print 'someProp %r someOtherProp %r'%( w.someProp, w.someOtherProp )
	print
	print 'changing state'
	w.currentState = 4
	print 'currentState %r someSource %r'%( w.currentState, w.someSource )
	print 'someProp %r someOtherProp %r'%( w.someProp, w.someOtherProp )
	