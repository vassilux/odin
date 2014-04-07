"""Python 2.2 property sub-classes

This package provides a hierarchy of Python 2.2 property classes
for use in a wide range of applications.

Rationale:

	[About Python 2.2 Properties]

	The built in property type assumes that the user will define two or
	three functions for every property to store, retrieve, and/or delete
	the particular property.  For example:

		class X(object):
			def seta( self, value ):
				self.__dict__['an'] = int(value)
			def geta( self):
				return self.__dict__['an']
			def dela( self ):
				del self.__dict__['an']
			a = property( geta,seta,dela,"A simple property a" )

	In this approach, a property object is considered to be a way
	of organizing "accessor methods" so that the accessor methods
	will be triggered by standard python attribute access mechanisms.
	
	This is obviously useful in many situations where particular
	property values require custom code for each of their accessor
	methods.  Unfortunately, the approach tends to require considerable
	extra code for every property so defined.  Where properties
	are highly customized and different from each other this is
	acceptable, as the code would need to be written somewhere.

	[About basicproperty Properties]

	In many real world applications, however, most of the properties
	defined are not radically different from other properties
	within the application.  Instead, the properties tend to share
	most of their semantics and needs.  Furthermore, there are common
	patterns in property usage which tend to be shared across
	applications.

	The basicproperty package defines a framework for creating families
	of properties for use in real world applications.  These properties
	provide basic implementations of most features needed for simple
	data modeling applications, for instance:

		bounds checking -- automatic checking of data values against
			defined bounds objects, with appropriately raised errors
			
		optional coercion -- allows you to define property classes
			which can modify given data types to match the property's
			required data types (particularly useful in GUI
			applications)

		optional method-name-based accessors -- to allow for functionality
			similar to the built-in property type, while maintaining
			the features of the basicproperty properties.  This
			functionality, however, allows for redefining client
			accessor methods by simple subclassing and overriding.

		optional default values -- either static or calculated for
			use when a particular property is not currently defined

		propertied object class -- an object sub-class explicitly
			designed for use with basicproperty property objects
			providing a default __init__ function to automatically
			assign values to defined properties from named
			arguments.

	The end goal of the package is to reduce the amount of code needed
	to write applications which want to model complex data types using
	consistent property classes.  In practice, this goal seems to be met,
	though the early-alpha status of the project means that there are
	still considerable areas for improvement.
"""
