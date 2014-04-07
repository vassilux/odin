"""Commonly used property types

Most of the property types here are simply using the
basictypes.basic_types type stand-ins to provide the
class interfaces which user-defined classes would
normally define directly.
"""
from basicproperty import basic, defaults
from basictypes import basic_types, list_types, typeunion, decimaldt

BasicProperty = basic.BasicProperty

class BooleanProperty(basic.BasicProperty):
	"""Boolean property"""
	baseType = basic_types.Boolean_DT
class IntegerProperty(basic.BasicProperty):
	"""Integer property"""
	baseType = basic_types.Int_DT
class LongProperty(basic.BasicProperty):
	"""Long/large integer property"""
	baseType = basic_types.Long_DT
class FloatProperty(basic.BasicProperty):
	"""Floating-point property"""
	baseType = basic_types.Float_DT

if decimaldt.decimal:
	class DecimalProperty(basic.BasicProperty):
		"""Decimal property"""
		baseType = decimaldt.DecimalDT

class StringProperty(basic.BasicProperty):
	"""Human-friendly (unicode) text property"""
	baseType = basic_types.String_DT
class StringLocaleProperty(basic.BasicProperty):
	"""Byte-string (locale-specific) property

	Normally used for storing low-level types such
	as module or file names which are not unicode-
	aware.
	"""
	baseType = basic_types.StringLocale_DT
class ClassNameProperty(basic.BasicProperty):
	"""Class-name property"""
	baseType = basic_types.ClassName_DT
class ClassProperty(basic.BasicProperty):
	"""Class property"""
	baseType = basic_types.Class_DT
ClassByNameProperty = ClassProperty

def _defaultList( property, client ):
	"""Get a default list value for list-type properties"""
	base = property.getBaseType()
	if issubclass( base, list ):
		return base()
	return []

class ListProperty(basic.BasicProperty):
	"""Generic list property"""
	baseType = basic_types.List_DT
	default = defaults.DefaultCallable( _defaultList )

class BooleansProperty(basic.BasicProperty):
	"""Booleans list property"""
	baseType = list_types.listof_bools
	default = defaults.DefaultCallable( _defaultList )
class IntegersProperty(basic.BasicProperty):
	"""Ints list property"""
	baseType = list_types.listof_ints
	default = defaults.DefaultCallable( _defaultList )
class LongsProperty(basic.BasicProperty):
	"""Longs list property"""
	baseType = list_types.listof_longs
	default = defaults.DefaultCallable( _defaultList )
class FloatsProperty(basic.BasicProperty):
	"""Floats list property"""
	baseType = list_types.listof_floats
	default = defaults.DefaultCallable( _defaultList )
class StringsProperty(basic.BasicProperty):
	"""Strings list property"""
	baseType = list_types.listof_strings
	default = defaults.DefaultCallable( _defaultList )
class ClassNamesProperty(basic.BasicProperty):
	"""ClassNames list property"""
	baseType = list_types.listof_classnames
	default = defaults.DefaultCallable( _defaultList )
class ClassesProperty(basic.BasicProperty):
	"""Classes list property"""
	baseType = list_types.listof_classes
	default = defaults.DefaultCallable( _defaultList )
ClassByNamesProperty = ClassesProperty

##class TypedListProperty(ListProperty):
##	"""List property with dynamically-specified baseType
##
##	Under the covers, if there is no baseType specified
##	but there are acceptableTypes specified, the
##	TypedListProperty will create a new baseType class
##	to use as it's baseType.  The mechanism to support
##	this is provided by the typeunion and list_types
##	modules in the basictypes package.
##	"""
##	def __init__( self, *arguments, **named ):
##		"""Initialise the TypedListProperty
##
##		baseType -- if specified, used as the baseType for
##			the list
##		acceptableTypes -- if false, the default list baseType
##			is used.  Otherwise should be a single-value tuple
##			with baseType (XXX eventually we should allow
##			multiple types), a new listof datatype will be
##			created to act as baseType.
##		"""
##		baseType = named.get( 'baseType', None )
##		if baseType is None:
##			# possibly we have an "acceptable types" value
##			acceptable = named.get( 'acceptableTypes', None )
##			if not acceptable:
##				baseType = basic_types.List_DT
##			else:
##				# construct a new list_of type for given types
##				# XXX should be a Union type for the types
##				# this is just using the first type...
##				if len(acceptable) > 1:
##					acceptable = typeunion.TypeUnion( acceptable )
##				else:
##					acceptable = acceptable[0]
##				baseType = list_types.listof(
##					baseType = acceptable,
##				)
##		named["baseType"] = baseType
##		super( TypedListProperty, self).__init__( *arguments, **named )


from basictypes import date_types
if date_types.haveImplementation:
	class DateTimeProperty(basic.BasicProperty):
		"""DateTime property"""
		baseType = date_types.DateTime_DT
		#default = defaults.DefaultCallable( lambda x,y: date_types.today() )
	class DateTimeDeltaProperty(basic.BasicProperty):
		"""DateTimeDelta property"""
		baseType = date_types.DateTimeDelta_DT
		#default = defaults.DefaultCallable( lambda property,client: date_types.DateTimeDelta(0) )
	class TimeOfDayProperty(basic.BasicProperty):
		"""DateTimeDelta property"""
		baseType = date_types.TimeOfDay
		#default = defaults.DefaultCallable( lambda property,client: date_types.TimeOfDay() )
	# here's where we would do the Python 2.3 datetime module version
	# and then possibly a wxDateTime module version
	# and maybe even a standard time module version if we really wanted

	# then add in any implementation-specific stuff
	# such as RelativeDateTime, JulianDateTime or
	# whatever is provided by one module and not the others
#else:
	# should we print a warning? would rather not in case the
	# developer just isn't using it, so didn't include it.
try:
	from basictypes import datedatetime_types as ddt
except ImportError, err:
	pass 
else:
	class DateTimeDTProperty( basic.BasicProperty ):
		"""DateTime property implemented using Python 2.3 datetime objects"""
		baseType = ddt.DateTime

from basicproperty.standard.dictionaryproperty import DictionaryProperty, WeakKeyDictionaryProperty, WeakValueDictionaryProperty
