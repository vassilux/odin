import unittest, time
from basicproperty import common, basic
from basictypes import factory, callable


def test( a = None ):
	pass
class t( object ):
	def test( self, a = None ):
		pass
	n = classmethod (test)
	m = staticmethod (test)
	def __call__(self):
		pass
u = t()

class TestClass( object ):
	arg = basic.BasicProperty(
		"arg", "Single Argument",
		baseType = callable.Argument,
	)
	args = basic.BasicProperty(
		"args", "Multiple Arguments",
		baseType = callable.listof_Arguments,
	)
	call = basic.BasicProperty(
		'call', 'single callable',
		baseType = callable.Callable,
	)

DATATABLE = [ # attribute, testTable, badValues
	('arg', [
		(
			callable.Argument( name="test" ),
			[
				"test",
				("test",),
			],
		),
		(
			callable.Argument( name="test", default=2 ),
			[
				("test",2),
				{'name':"test","default":2},
			],
		),
		(
			callable.Argument( name="test", default=2, baseType=str ),
			[
				("test",2,str),
				{'name':"test","default":2,'baseType':str},
			],
		),
	], [ # (bad value, error expected)
##		("a", ValueError),
##		(None, TypeError),
##		("am", ValueError),
	]),
	('args', [
		(
			[callable.Argument( name="test" )],
			[
				["test"],
				[("test",)],
			],
		),
		(
			[callable.Argument( name="test", default=2 )],
			[
				[("test",2)],
				[{'name':"test","default":2}],
			],
		),
		(
			[callable.Argument( name="test", default=2, baseType=str )],
			[
				[("test",2,str)],
				[{'name':"test","default":2,'baseType':str}],
			],
		),
	], [ # (bad value, error expected)
##		("a", ValueError),
##		(None, TypeError),
##		("am", ValueError),
	]),
	('call', [
		(#regular function
			callable.Callable(
				name='test',
				implementation=test,
				arguments =[
					callable.Argument(name='a',default=None)
				]
			),
			[
				test,
			],
		),
		(# unbound instance method, self is an argument
			callable.Callable(
				name='test',
				implementation=t.test,
				arguments =[
					callable.Argument(name='self'),
					callable.Argument(name='a',default=None),
				]
			),
			[
				t.test,
			],
		),
		(#classmethod, self is already curried
			callable.Callable(
				name='test',
				implementation=t.n,
				arguments =[
					callable.Argument(name='a',default=None),
				]
			),
			[
				t.n,
			],
		),
		(#staticmethod, self is an argument
			callable.Callable(
				name='test',
				implementation=t.m,
				arguments =[
					callable.Argument(name='self'),
					callable.Argument(name='a',default=None),
				]
			),
			[
				t.m,
			],
		),
		(#instance method, self is not an argument
			callable.Callable(
				name='test',
				implementation=u.n,
				arguments =[
					callable.Argument(name='a',default=None),
				]
			),
			[
				u.n,
			],
		),
		(#callable instance, with zero arguments
			callable.Callable(
				name="<unknown>",
				implementation=u,
				arguments =[
				]
			),
			[
				u,
			],
		),
	], [ # (bad value, error expected)
##		("a", ValueError),
##		(None, TypeError),
##		("am", ValueError),
	]),
]
		

class DTPropertyTest( unittest.TestCase ):
	def testCoerce( self ):
		"""Test the whole DATATABLE set for coercion"""
		object = TestClass()
		for attribute, table, bad in DATATABLE:
			for value, set in table:
				for v in set:
					setattr( object, attribute, v)
					got = getattr( object, attribute )
					assert got == value, """COERCE(%s): %r -> %r failed, got %r"""%( attribute, v, value, got)
			for value, err in bad:
				try:
					setattr(object, attribute, value)
				except err:
					continue
				except Exception, e:
					raise TypeError( """Wrong exc: set %(attribute)r to %(value)r\nExpected: %(err)s\nGot: %(e)s"""%(locals()))
				else:
					result = getattr( object, attribute)
					import pdb
					pdb.set_trace()
					setattr(object, attribute, value)
					raise TypeError( """No exc: set %(attribute)r to %(value)r\nExpected: %(err)r %(err)s\nValue:%(result)s"""%(locals()))
		

if __name__ == "__main__":
	unittest.main()
	