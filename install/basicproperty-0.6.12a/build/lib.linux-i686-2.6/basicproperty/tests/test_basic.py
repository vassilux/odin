import unittest
from basicproperty import basic
from basictypes import boundary

class TestClass( object ):
	simple = basic.BasicProperty(
		"simple", "documentation"
	)
	withBound = basic.BasicProperty(
		"withBound", "documentation",
		boundaries=( boundary.Type(str),)
	)
	withDefaultValue = basic.BasicProperty(
		"withDefaultValue", "documentation",
		defaultValue = 'this',
	)
	withDefaultFunction = basic.BasicProperty(
		"withDefaultFunction", "documentation",
		defaultFunction = lambda x,y: [],
	)
	withDefaultValueNoSet = basic.BasicProperty(
		"withDefaultValueNoSet", "documentation",
		defaultValue = 'this',
		setDefaultOnGet = 0,
	)
	withDefaultFunctionNoSet = basic.BasicProperty(
		"withDefaultFunctionNoSet", "documentation",
		defaultFunction = lambda x,y: [],
		setDefaultOnGet = 0,
	)
	

class BasicPropertyTest( unittest.TestCase ):
	def testInit( self ):
		"""Test initialisation of the property objects"""
		basic.BasicProperty( "name" )
		basic.BasicProperty( "name", "documentation" )
		basic.BasicProperty( "name", "documentation", )
		basic.BasicProperty( "name", "documentation", defaultValue=[1,2,3] )
		basic.BasicProperty( "name", "documentation", defaultFunction = lambda x,y: [] )
		basic.BasicProperty( "name", "documentation", baseType = str )
	def testBadInit( self ):
		"""Test improper initialisation of the property objects"""
		self.failUnlessRaises( TypeError, basic.BasicProperty, "name", "documentation", boundary.Type(str), )
		self.failUnlessRaises( TypeError, basic.BasicProperty )
	def testStandard( self ):
		"""Test standard get/set/del semantics"""
		object = TestClass()
		self.failUnless( not hasattr(object, 'simple' ), 'property is defined before setting')
		value = 'this'
		object.simple = value
		self.failUnless( object.simple is value , 'property value not stored as same object')
		del object.simple
		self.failUnless( not hasattr(object, 'simple' ), 'property deletion failed')
	def testDefaultValue( self ):
		"""Test default value semantics"""
		object = TestClass()
		self.failUnless( object.withDefaultValue == 'this' )
		self.failUnless( object.__dict__.has_key("withDefaultValue"), 'Default value not set as current on access' )
		del object.withDefaultValue
		object.withDefaultValue = 2
		self.failUnless( object.withDefaultValue == 2, "explicitly setting value didn't override default" )
		
	def testDefaultFunction( self ):
		"""Test default function semantics"""
		object = TestClass()
		self.failUnless( object.withDefaultFunction == [] )
		self.failUnless( object.__dict__.has_key("withDefaultFunction"), 'Default function value not set as current on access' )
		del object.withDefaultFunction
		object.withDefaultFunction = 2
		self.failUnless( object.withDefaultFunction == 2, "explicitly setting value didn't override default" )


class TestClass2( object ):
	simple = basic.MethodStoreProperty(
		"simple", "documentation",
		getMethod = "doGet",
		setMethod = "doSet",
		delMethod = "doDel",
	)
	def doGet( self, ):
		return self.value
	def doSet( self, value ):
		self.value = value
	def doDel( self):
		del self.value



class MethodStoreTest( unittest.TestCase ):
	"""Tests for the method-store mix-in"""
	def testSimple( self ):
		"""Test simple method store operation"""
		object = TestClass2()
		object.value = None
		self.failUnless( object.value == None, """Initial value somehow not None""")
		object.simple = 3
		self.failUnless( object.value == 3, """Set failed to update value""")
		self.failUnless( object.simple == 3, """Get failed to access updated value""")
		del object.simple
		self.failUnless( not hasattr( object, "value"), """Del failed to delete value""")
		self.failUnless( not hasattr( object, "simple"), """Get returned value after deletion""")
		
if __name__ == "__main__":
	unittest.main()
	