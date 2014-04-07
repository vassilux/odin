"""Mix-in providing weakref-based storage for properties"""
import weakref
from basicproperty import basic
class WeakStore( object ):
	"""Mix-in providing weak-references to held objects"""
	def _getValue( self, client ):
		"""Perform a low-level retrieval of the "raw" value for the client
		"""
		base = super( WeakStore, self )._getValue( client )
		if isinstance( base, weakref.ReferenceType):
			base = base()
			if base is None:
				self._delValue( client )
				raise AttributeError( """Property %r on object %r references an object which has been garbage collected"""%(
					self.name,
					client,
				))
		return base
	def _setValue( self, client, value ):
		"""Perform a low-level set of the "raw" value for the client
		"""
		try:
			value = weakref.ref( value )
		except TypeError:
			raise TypeError( """Attempted to set non weak-referencable object %r for property %r of object %r"""%(
				value, self.name, client,
			))
		return super( WeakStore, self)._setValue( client, value )

class WeakProperty( WeakStore, basic.BasicProperty ):
	"""Weak-referencing version of BasicProperty"""
	