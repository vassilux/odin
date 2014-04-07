import unittest
from basicproperty import basic
from basictypes import boundary
from basicproperty.common import ClassByNameProperty

class TestClass( object ):
	simple = ClassByNameProperty(
		"simple", "Class stored as string and restored on access"
	)
	default = ClassByNameProperty(
		"default", "Access with a default value",
		defaultValue = basic.BasicProperty
	)
	default2 = ClassByNameProperty(
		"default2", "Access with a default value",
		defaultValue = "basicproperty.basic.BasicProperty",
	)


class ClassPropertyTest( unittest.TestCase ):
	def testStandard( self ):
		"""Test standard get/set/del semantics"""
		object = TestClass()
		self.failUnless( not hasattr(object, 'simple' ), 'property is defined before setting')
		object.simple = basic.BasicProperty
		self.failUnless( hasattr(object, 'simple' ), 'class not stored on setattr')
		self.failUnless( object.simple is basic.BasicProperty, 'class returned is not the same as given')
	def testDefault( self ):
		"""Test default value semantics"""
		object = TestClass()
		self.failUnless( hasattr(object, 'default' ), """default isn't available""")
		self.failUnless( object.default is basic.BasicProperty, 'class returned is not the same as default, was %r'%(object.default))
		object.default = boundary.Type
		self.failUnless( object.default is boundary.Type, 'class returned is not the same as set, was %r'%(object.default))

if __name__ == "__main__":
	unittest.main()
	