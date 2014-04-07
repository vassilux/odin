from basicproperty import propertied, basic, common, boundary

try:
	import Persistence
	class ContactObject( propertied.Propertied, Persistence.Persistent):
		"""A basic object within the contact database

		Each object within the database supports some number of note fields
		"""
		notes = basic.BasicProperty(
			"notes", "Notes about the given value",
			boundaries = [
				boundary.Type( list ),
				boundary.ForEach( boundary.Type( unicode )),
			],
			defaultFunction = lambda x,y: [],
		)
except ImportError:
	class ContactObject( propertied.Propertied ):
		"""A basic object within the contact database

		Each object within the database supports some number of note fields
		"""
		notes = basic.BasicProperty(
			"notes", "Notes about the given value",
			boundaries = [
				boundary.Type( list ),
				boundary.ForEach( boundary.Type( unicode )),
			],
			defaultFunction = lambda x,y: [],
		)

class Name(ContactObject):
	"""A name, which may be an alias for an official legal name

	I'm not sure about the internationalization issues
	here, given that "family names" in certain countries are
	mutable depending on individual gender and the like.

	No attempt is made to automatically support display names
	which are reverse order (for instance Chinese).

	Note: multiple names can be defined for an individual
	so you would record a nickname as a separate "given" name,
	rather than encoding it as part of the person's primary name.
	"""
	given = common.StringProperty(
		"given", """Given name(s), personal name(s) or only name, for instance "Cher", "Peter" or "Michael Colin".""",
		defaultValue = "",
	)
	family = common.StringProperty(
		"family", """Family name, clan name, or group name(s). Note that is value may be unspecified.""",
		defaultValue = "",
	)
	display = common.StringProperty(
		"display", """Display name, should be defined if this name should be displayed in the manner other than the application's default display mechanism (for instance "Family, Personal"). Note that is value may be unspecified.""",
		defaultValue = "",
	)
	formOfAddress = common.StringProperty(
		"formOfAddress", """Form of address (title), for example "Dr.", "His Eminence", "Her Majesty", "Ms.". Note that is value may be unspecified, applications may use it if present during default display calculation.""",
		defaultValue = "",
	)
	preferred = common.BooleanProperty(
		"preferred", """Indicate that this name/nickname is the preferred form of address for the individual""",
		defaultValue = 0,
	)

class CommunicationsObject( ContactObject ):
	"""Base type for communication-oriented contact object properties
	"""
	type = common.StringProperty(
		"type", """Indicates the role of this particular communications address, for example "home", "work", "mobile".""",
		defaultValue = ""
	)
	preferred = common.BooleanProperty(
		"preferred", """Indicate that this name/nickname is the preferred address of its type for the individual""",
		defaultValue = 0,
	)
	
	

class PhoneNumber( CommunicationsObject ):
	"""A phone number, includes satellite and videophones"""
	number = common.StringProperty(
		"number", "The telephone number",
		defaultValue = "",
	)
	messaging = common.BooleanProperty(
		"messaging", "Whether this connection has messaging (voicemail) support",
		defaultValue = 0,
	)
class EmailAddress( CommunicationsObject ):
	"""An e-mail address, generally an Internet e-mail address"""
	address = common.StringProperty(
		"address", "The email address",
		defaultValue = "",
	)

class DeliveryAddress( CommunicationsObject):
	"""A physical delivery address (mailing address)
	
	From the vCard spec:
		Post Office Address (first field)
		Extended Address (second field),
		Street (third field),
		Locality (fourth field),
		Region (fifth field),
		Postal Code (six field),
		Country (seventh field)
	"""
	address = common.StringProperty(
		"address", """The post-office address e.g. "Widgets Inc." or "Great Guy".""",
		defaultValue = "",
	)
	extendedAddress =  common.StringProperty(
		"extendedAddress", "The extended address e.g. Purchasing Department",
		defaultValue = "",
	)
	street = common.StringProperty(
		"street", "The street address e.g. 1426 Someroad Place.",
		defaultValue = "",
	)
	unit = common.StringProperty(
		"unit", "The unit/apartment address e.g.  #32b or Apt. 32 or Suite 32b",
		defaultValue = "",
	)
	locality = common.StringProperty(
		"locality", "The town, post-office district or city e.g. Toronto",
		defaultValue = "",
	)
	region = common.StringProperty(
		"region", "The state, province, district, or territory e.g. Ontario",
		defaultValue = "",
	)
	postalCode = common.StringProperty(
		"postalCode", "The post-office designation (zip-code, postal-code) e.g. M5P 3K8 or 90210",
		defaultValue = "",
	)
	country = common.StringProperty(
		"country", "The country e.g. Canada or United States of America",
		defaultValue = "",
	)
	
	domestic = common.BooleanProperty(
		"domestic", "Whether this address is domestic or international",
		defaultValue = 0,
	)
	postal = common.BooleanProperty(
		"postal", "Whether this address is served by the post office",
		defaultValue = 1,
	)
	parcel = common.BooleanProperty(
		"parcel", "Whether this address accepts parcel deliveries",
		defaultValue = 1,
	)

class Contact( ContactObject ):
	names = basic.BasicProperty(
		"names", "List of names for the contact",
		boundaries = [
			boundary.ForEach( boundary.Type( Name ))
		],
		defaultFunction = lambda x,y: [],
	)
	phones = basic.BasicProperty(
		"phones", "List of phone numbers for the contact",
		boundaries = [
			boundary.ForEach( boundary.Type( PhoneNumber ))
		],
		defaultFunction = lambda x,y: [],
	)
	emails = basic.BasicProperty(
		"emails", "List of email addresses for the contact",
		boundaries = [
			boundary.ForEach( boundary.Type( EmailAddress ))
		],
		defaultFunction = lambda x,y: [],
	)
	deliveries = basic.BasicProperty(
		"deliveries", "List of delivery addresses for the contact",
		boundaries = [
			boundary.ForEach( boundary.Type( DeliveryAddress ))
		],
		defaultFunction = lambda x,y: [],
	)



class OrganisationMember( ContactObject ):
	title = common.StringProperty(
		"title", "The title of this position",
		defaultValue = "",
	)
_members = basic.BasicProperty(
	"members", "The members/contacts in the position",
	boundaries = [
		boundary.ForEach( boundary.Type( (Contact, OrganisationMember) ))
	],
	defaultFunction = lambda x,y: [],
)
OrganisationMember.members = _members

class Organisation( Contact ):
	members = _members

	
