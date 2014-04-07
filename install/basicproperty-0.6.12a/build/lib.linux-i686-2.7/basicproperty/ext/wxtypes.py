"""wxPython-specific property classes"""
from basicproperty import basic, common
from basictypes.wxtypes import colour, pen, font
from basictypes import enumeration

## DATA-model properties
class ColourProperty(basic.BasicProperty):
	"""wxColour property"""
	baseType = colour.wxColour_DT
	friendlyName = "Colour"
	
class PenProperty( basic.BasicProperty ):
	"""wxPen property"""
	baseType = pen.wxPen
	friendlyName = "Pen"

class FontProperty( basic.BasicProperty ):
	"""wxFont property"""
	baseType = font.wxFont_DT
	friendlyName = "Font"

## LIVE properties
class wxPenStyleProperty(
	enumeration.EnumerationProperty,
	basic.MethodStore,
	basic.BasicProperty
):
	"""wxPen Style property (live)"""
	baseType = pen.PenStyle
	getMethod = "GetStyle"
	setMethod = "SetStyle"
	friendlyName = "Line Style"
class wxPenCapProperty(
	enumeration.EnumerationProperty,
	basic.MethodStore,
	basic.BasicProperty
):
	"""wxPen Cap property (live)"""
	baseType = pen.PenCap
	getMethod = "GetCap"
	setMethod = "SetCap"
	friendlyName = "Cap Style"
class wxPenJoinProperty(
	enumeration.EnumerationProperty,
	basic.MethodStore,
	basic.BasicProperty
):
	"""wxPen Join property (live)"""
	baseType = pen.PenJoin
	getMethod = "GetJoin"
	setMethod = "SetJoin"
	friendlyName = "Corner Style"
	
class wxWidthProperty( basic.MethodStore, common.IntegerProperty ):
	"""wxObject Width property (live)"""
	getMethod = "GetWidth"
	setMethod = "SetWidth"
	friendlyName = "Width"
class wxColourProperty( basic.MethodStore, ColourProperty ):
	"""wxObject Colour property (live)"""
	getMethod = "GetColour"
	setMethod = "SetColour"
	friendlyName = "Colour"
	
	
	