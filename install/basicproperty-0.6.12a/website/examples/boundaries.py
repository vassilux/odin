"""Simple demo showing creation and use of boundary for string property"""
from basicproperty import propertied, common

def checkEmailAddress( address, property=None, client=None ):
	try:
		prefix, suffix = address.split( '@' )
	except ValueError:
		raise ValueError( """Require exactly one @ symbol in email addresses, got: %r"""%(address,))
	else:
		if not prefix or not suffix:
			raise ValueError( """Require non-null username and domain in email addresses, got: %r"""%(address,))

class User( propertied.Propertied ):
	email = common.StringProperty(
		"email", """The user's email address""",
		boundaries = (
			checkEmailAddress,
		),
	)

if __name__ == "__main__":
	good = [
		'this@that.com',
		'that.those@some.com',
	]
	bad = [
		'this at that dot com',
		'that.those.them',
		'@somewhere.net',
	]
	for name in good:
		User().email = name
	for name in bad:
		try:
			User().email = name
		except ValueError, err:
			pass
		else:
			raise RuntimeError( """Should have rejected %r, didn't"""%(name,))
	