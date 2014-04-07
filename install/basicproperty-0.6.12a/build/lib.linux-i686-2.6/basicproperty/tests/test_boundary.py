import unittest
from basicproperty import basic, propertied, common
from basictypes import boundary

class BoundaryErrorCase( unittest.TestCase ):
	def testBaseRepr(self):
		"""Test representation code"""
		repr( boundary.BoundaryError(None, None, None, None, "somemessage" ) )
	def testRepr( self ):
		"""Test representation code with real objects"""
		property = basic.BasicProperty( "this" )
		bound = boundary.Type( str )
		client = self
		value = "some value"
		object = boundary.BoundaryError(property, bound, client, value, "somemessage" )
		repr( object )
	def testStr( self ):
		"""Test string-conversion code with real objects"""
		property = basic.BasicProperty( "this" )
		bound = boundary.Type( str )
		client = self
		value = "some value"
		object = boundary.BoundaryError(property, bound, client, value, "somemessage" )
		str(object)

class ErrorTest:
	def _testError( self, bound, badValue ):
		"""Test that the error object is properly configured"""
		property = basic.BasicProperty( "this" )
		client = self
		try:
			bound( badValue, property, client )
		except boundary.BoundaryError, error:
			assert error.property is property, """Improper error attribute %s"""% (property,)
			assert error.boundary is bound, """Improper error attribute %s"""% (bound,)
			assert error.client is client, """Improper error attribute %s"""% (client,)
			assert error.value is badValue, """Improper error attribute %s"""% (badValue,)

class BoundaryTestCase(unittest.TestCase):
	def setUp(self):
		self.boundary = boundary.Boundary()
	def testCallParams(self):
		self.boundary( None, None, None )

class TypeBoundaryTestCase(unittest.TestCase, ErrorTest):
	def testGood(self):
		"""Test a string value"""
		boundary.Type( str )( "some value" )
	def testGood2(self):
		"""Test a unicode value"""
		bound = boundary.Type( str )
		self.failUnlessRaises( boundary.BoundaryTypeError, bound, None, None, u"some value")
	def testBad1(self):
		"""Test a non-string value"""
		bound = boundary.Type( str )
		self.failUnlessRaises( boundary.BoundaryTypeError, bound, None, None, 1)
	def testImported(self):
		"""Test a unicode value"""
		bound = boundary.Type( "basictypes.boundary.Boundary" )
		self.failUnlessRaises( boundary.BoundaryTypeError, bound, None, None, None)
		bound( boundary.Boundary(), None, None)
	def testError( self ):
		"""Test that the reported error is properly configured"""
		bound = boundary.Type( "basictypes.boundary.Boundary" )
		self._testError( bound, 'object' )

class RangeBoundaryTestCase(unittest.TestCase, ErrorTest):
	def testGood(self):
		"""Test values within range"""
		bound = boundary.Range( minimum=0,maximum=10 )
		bound(  0 )
		bound( 10 )
		bound( 5 )
		bound( 5.0 )
	def testBad(self):
		"""Test values outside range"""
		bound = boundary.Range( minimum=0,maximum=10 )
		self.failUnlessRaises( boundary.BoundaryValueError, bound, -1)
		self.failUnlessRaises( boundary.BoundaryValueError, bound, 'a')
		self.failUnlessRaises( boundary.BoundaryValueError, bound, [])
		self.failUnlessRaises( boundary.BoundaryValueError, bound, None)
		self.failUnlessRaises( boundary.BoundaryValueError, bound, 11)
		self.failUnlessRaises( boundary.BoundaryValueError, bound, 10.00001)
		self.failUnlessRaises( boundary.BoundaryValueError, bound, -.00001)
	def testError( self ):
		"""Test that the reported error is properly configured"""
		bound = boundary.Range( minimum=0,maximum=10 )
		self._testError( bound, 20 )

class LengthBoundaryTestCase(unittest.TestCase, ErrorTest):
	def testGood(self):
		"""Test values within range"""
		bound = boundary.Length( minimum=0,maximum=3 )
		bound( () )
		bound( (1,2,3) )
		bound( '123' )
		bound( [] )
	def testBad(self):
		"""Test values outside range"""
		bound = boundary.Length( minimum=1,maximum=3 )
		self.failUnlessRaises( boundary.BoundaryValueError, bound, [])
		self.failUnlessRaises( boundary.BoundaryValueError, bound, '')
		self.failUnlessRaises( boundary.BoundaryValueError, bound, '1234')
	def testError( self ):
		"""Test that the reported error is properly configured"""
		bound = boundary.Length( minimum=0,maximum=3 )
		self._testError( bound, range(5) )
class NonNullBoundaryTestCase(unittest.TestCase, ErrorTest):
	def testGood(self):
		"""Test values within range"""
		bound = boundary.NotNull()
		bound( (1,), None, None,  )
		bound( 1, None, None,  )
		bound( '1', None, None,  )
		bound( [1], None, None,  )
	def testBad(self):
		"""Test values outside range"""
		bound = boundary.NotNull()
		self.failUnlessRaises( boundary.BoundaryValueError, bound, None, None, [])
		self.failUnlessRaises( boundary.BoundaryValueError, bound, None, None, '')
		self.failUnlessRaises( boundary.BoundaryValueError, bound, None, None, 0)
		self.failUnlessRaises( boundary.BoundaryValueError, bound, None, None, None)
		self.failUnlessRaises( boundary.BoundaryValueError, bound, None, None, u'')
	def testError( self ):
		"""Test that the reported error is properly configured"""
		bound = boundary.NotNull()
		self._testError( bound, None )

class ForEachBoundaryTestCase(unittest.TestCase, ErrorTest):
	def testGood(self):
		"""Test values within range"""
		bound = boundary.ForEach( boundary.NotNull())
		bound( (), None, None,  )
		bound( [1,2,3], None, None,  )
		bound( '', None, None,  )
		bound( ' ', None, None,  )
	def testBad(self):
		"""Test values outside range"""
		bound = boundary.ForEach( boundary.NotNull())
		self.failUnlessRaises( boundary.BoundaryValueError, bound, [0])
		self.failUnlessRaises( boundary.BoundaryValueError, bound, [None])
		self.failUnlessRaises( boundary.BoundaryValueError, bound, [1,2,3,0])
		self.failUnlessRaises( boundary.BoundaryValueError, bound, (0,1,2,3))
	def testError( self ):
		"""Test that the reported error is properly configured"""
		bound = boundary.ForEach( boundary.NotNull())
		self._testError( bound, [None] )

class FunctionTestCase(unittest.TestCase, ErrorTest):
	def testTrue(self):
		"""Test function test with True"""
		def x( value ):
			return value
		bound = boundary.Function( x, boundary.Function.TRUE_VALUES)
		bound( 1 )
		bound( [1,2] )
		bound( "this" )
		bound( True )
	def testFalse(self):
		"""Test function test with False"""
		def x( value ):
			return value
		bound = boundary.Function( x, boundary.Function.FALSE_VALUES)
		self.failUnlessRaises( boundary.BoundaryValueError, bound, [0])
		self.failUnlessRaises( boundary.BoundaryValueError, bound, [None])
		self.failUnlessRaises( boundary.BoundaryValueError, bound, [1,2,3,0])
		self.failUnlessRaises( boundary.BoundaryValueError, bound, (0,1,2,3))
	def testOther(self):
		"""Test function test with other"""
		def x( value ):
			return value + 1
		bound = boundary.Function( x, 5)
		bound( 4 )
		self.failUnlessRaises( boundary.BoundaryValueError, bound, 3)
		


class TestData( propertied.Propertied ):
	str1 = common.StringProperty(
		"str1", """Test string property""",
		boundaries = (
			boundary.Range( minimum= "", maximum="z" ),
			boundary.Length( maximum = 10 ),
		)
	)
	str2 = common.StringProperty(
		"str2", """Test string property""",
		boundaries = (
			boundary.Range( minimum= "a", maximum="z" ),
			boundary.Length( maximum = 10 ),
		)
	)


class PropertyTestCases(unittest.TestCase):
	def testGood(self):
		"""Test values that should not trigger a property meltdown..."""
		TestData().str1 = 'abc'
		TestData().str1 = 'z'
		TestData().str1 = 's'
		TestData().str1 = ''
	def testBad(self):
		"""Test values that should raise errors"""
		self.failUnlessRaises( ValueError, setattr, TestData(), 'str2', '12345678901' )
		self.failUnlessRaises( ValueError, setattr, TestData(), 'str2','' )
		self.failUnlessRaises( ValueError, setattr, TestData(), 'str2','A' )
		self.failUnlessRaises( ValueError, setattr, TestData(), 'str2','Z' )
		
		

if __name__ == "__main__":
	unittest.main()
	
