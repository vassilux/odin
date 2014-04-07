from basicproperty import basic
from basictypes import boundary, latebind

import weakref

class UncoercedDictionaryProperty (basic.BasicProperty):
	"""Dictionary property object, with type checking"""
	dataType = "dict"
	baseType = dict
	def default( self, property, client ):
		return self.getBaseType()()

class DictionaryProperty (UncoercedDictionaryProperty):
	"""Dictionary property object, with type checking and basic coercion"""
	def coerce (self, client, value):
		"""Coerce the value to/from dictionary value"""
		base = self.getBaseType()
		if base:
			if isinstance( value, base ):
				return value
			elif hasattr(base, 'coerce' ):
				return base.coerce( value )
			return base( value )
		return value


class WeakKeyDictionaryProperty(DictionaryProperty):
	"""Weak-Key dictionary property object"""
	dataType = "dict.weakkey"
	boundaries = [ boundary.Type( weakref.WeakKeyDictionary )]
	baseType = weakref.WeakKeyDictionary
	def coerce (self, client, value):
		"""Ensure that value is a weak-key dictionary

		If the value is not already a dictionary or
		WeakKeyDictionary, will go through DictionaryProperty's
		coercion mechanism first.
		"""
		if not isinstance( value, (dict, weakref.WeakKeyDictionary)):
			value = super (WeakKeyDictionaryProperty, self).coerce (
				client, value
			)
		if isinstance( value, dict):
			value = weakref.WeakKeyDictionary(value)
		return value

class WeakValueDictionaryProperty(DictionaryProperty):
	"""Weak-Value dictionary property object"""
	dataType = "dict.weakvalue"
	boundaries = [ boundary.Type( weakref.WeakValueDictionary )]
	baseType = weakref.WeakValueDictionary
	def coerce (self, client, value):
		"""Ensure that value is a weak-value dictionary

		If the value is not already a dictionary or
		WeakKeyDictionary, will go through DictionaryProperty's
		coercion mechanism first.
		"""
		if not isinstance( value, (dict, weakref.WeakValueDictionary)):
			value = super (WeakValueDictionaryProperty, self).coerce (
				client, value
			)
		if isinstance( value, dict):
			value = weakref.WeakValueDictionary(value)
		return value

