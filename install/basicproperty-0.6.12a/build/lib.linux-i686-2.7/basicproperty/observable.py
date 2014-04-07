"""Demonstration of observable properties

This module provides Observable sub-classes of all of the 
property types in the "common" module.  It uses PyDispatcher
to send messages synchronously from the property whenever a
property value is set on a client.
"""
from dispatch import dispatcher 
from basicproperty import basic, common

class Observable( basic.BasicProperty ):
	"""Observable mix-in for sending PyDispatcher messages
	
	We override __set__ and __delete__ to send messages, SET_SIGNAL and
	DELETE_SIGNAL respectively.  The messages are sent *after* setting,
	from the property instance, with the parameter client, and "value"
	for SET_SIGNAL.  Note that you can customise the message sent 
	by passing the desired value as named arguments SET_SIGNAL and/or 
	DELETE_SIGNAL to the property constructor.
	
	You can watch all events with code like this:
	
		dispatcher.connect( 
			onSet,
			signal = Model.propertyName.SET_SIGNAL,
		)
		dispatcher.connect( 
			onDel,
			signal = Model.propertyName.DELETE_SIGNAL,
		)
	
	or only handle messages from a particular property like this:
	
		dispatcher.connect( 
			onSet,
			sender = Model.propertyName,
			signal = Model.propertyName.SET_SIGNAL,
		)
	"""
	SET_SIGNAL = "basicproperty.observable.set"
	DELETE_SIGNAL = "basicproperty.observable.set"
	def __set__( self, client, value ):
		"""Override to send dispatcher messages on setting"""
		value = super( Observable, self ).__set__( client, value )
		try:
			dispatcher.send(
				signal = self.SET_SIGNAL,
				sender = self,
				value = value,
				client = client,
			)
		except Exception, err:
			# you'd actually want to log here...
			pass
		return value
	def __delete__( self, client ):
		"""Override to send dispatcher messages on deletion"""
		value = super( Observable, self ).__delete__( client )
		try:
			dispatcher.send(
				signal = self.DELETE_SIGNAL,
				sender = self,
				client = client,
			)
		except Exception, err:
			# you'd actually want to log here...
			pass
		return value

# Now mirror all of the "common" types with observable versions...
for name in dir(common):
	cls = getattr(common, name)
	if isinstance( cls, type ) and issubclass( cls, basic.BasicProperty ):
		newcls = type( name, (Observable,cls), {
			'__doc__': 'Observable version of basicproperty.common.%s'%(name,),
		})
		exec "%s = newcls"%(name,)


if __name__ == "__main__":
	from basicproperty import propertied
	import random
	class Model( propertied.Propertied ):
		name = StringProperty(
			"name", """The name of the object, for some purpose""",
			defaultValue = "Uncle Tim",
		)
		age = IntegerProperty(
			"age", """How old the object is, often just a guess""",
			defaultFunction = lambda prop, client: random.randint( 1, 100),
		)
		values = IntegersProperty(
			"values", """Set of observable integers""",
		)
	
	def onDel( sender, client ):
		"""Process a change to a Model Object"""
		print 'DEL', sender.name, client
	def onSet( sender, client, value ):
		"""Process value from *any* property"""
		print 'SET', sender.name, client, value
	dispatcher.connect( 
		onSet,
		# we assume the default SET_SIGNAL here
		signal = Observable.SET_SIGNAL,
	)
	dispatcher.connect( 
		onDel,
		# we assume the default DELETE_SIGNAL here
		signal = Observable.DELETE_SIGNAL,
	)
	m = Model()
	m.name = 'Peters'
	m.age # note we send a message, as the default is __set__ on retrieval
	m.age = 18
	m.values = [2,3,4,'8']
	del m.values
