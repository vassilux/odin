from basicproperty import linearise

if __name__ == "__main__":
	from pytable import dbschema
	#Lineariser.registerHelper( dbschema.TableSchemas, SequenceLin() )
	class _x:
		def __getinitargs__( self ):
			return (1,2,3)
	class _y:
		def __getstate__( self ):
			return {'a':'b',1:3}
	class _z:
		pass
	x = _x()
	y = _y()
	z = _z()
	z.this = 'that'
	q = dbschema.DatabaseSchema(
		name="this", tables=[
			dbschema.TableSchema( name = "blah" ),
		],
	)
	print linearise.linearise( [
		2,3,4,
		"this",
		(4,5,6),
		{'a':4,2:[],'8':{}},
		('a',23L,23.4),
		4j,
		linearise.Lineariser,
		linearise.saxutils.XMLGenerator,
		linearise.Lineariser,
		float,
		linearise.linearise,
		x,y,z,
		q,
		None,
	])
	from cinemon import tableschema
	result = linearise.linearise( tableschema.schema )
	open('v:\\cinemon\\table_schema.xml','w').write( result )
	