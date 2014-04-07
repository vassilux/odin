/* C-level accellerator for basicproperty properties */
#include "Python.h"

static PyObject * PyObject_GetDictKey( PyObject * obj, char * name ) {
	/* low-level retrieval of attr name from self.__dict__ 
	
	Returns a new reference to the object, or NULL
	with the proper AttributeError set.
	*/
	PyObject ** dictptr;
	PyObject * res;
	dictptr = _PyObject_GetDictPtr(obj);
	if (dictptr != NULL) {
		PyObject * dict = *dictptr;
		if (dict != NULL) {
			res = PyDict_GetItemString(dict, name);
			if (res != NULL) {
				Py_INCREF(res);
			} else {
				PyErr_Format(
					PyExc_AttributeError,
					"'%.50s' object has no attribute '%.50s'",
					obj->ob_type->tp_name, name
				);
			}
		} else {
			res = NULL;
			PyErr_Format(
				PyExc_AttributeError,
                "'%.50s' object '__dict__' attribute appears to be NULL, likely has no attributes (searching for %.50s)",
				obj->ob_type->tp_name,
				name
			);
		}
	} else {
		res = NULL;
		PyErr_Format(
			PyExc_AttributeError,
			"'%.50s' object has no '__dict__'",
			obj->ob_type->tp_name
		);
	}
	return res;
}

static PyObject * _getValue( PyObject * self, PyObject * args ) {
	/* C version of the default _getValue for basic properties 
	
	return client.__dict__[ self.name ]
	*/
	char * name = NULL;
	PyObject * obj = NULL;
	PyObject * prop = NULL;
	PyObject * nameObj = NULL;
	PyObject * result = NULL;

	if (!PyArg_ParseTuple( args, "OO", &prop, &obj )) {
		return NULL;
	}
	nameObj = PyObject_GetAttrString( prop, "name" );
	if (nameObj == NULL) {
		return NULL;
	}
	if (!PyString_Check( nameObj )) {
		PyErr_Format(
			PyExc_TypeError,
			"'%.50s' object 'name' attribute is of type %.50s, require str type.",
			prop->ob_type->tp_name,
			nameObj->ob_type->tp_name
		);
		Py_DECREF(nameObj);
		return NULL;
	}
	name = PyString_AsString( nameObj );
	Py_DECREF(nameObj);
	return PyObject_GetDictKey( obj, name );
}

static PyObject * __get__( PyObject * self, PyObject * args ) {
	/* C version of the default __get__ for basic properties 
	
	def __get__( self, client, klass=None ):
		"""Retrieve the current value of the property for the client

		This function provides the machinery for default value and
		default function support.  If the _getValue method raises
		a KeyError or AttributeError, this method will attempt to
		find a default value for the property using self.getDefault
		"""
		try:
			if client is None:
				pass
			else:
				return self._getValue( client )
		except (KeyError, AttributeError):
			return self.getDefault( client )
		else:
			# client was None
			if klass:
				return self
			else:
				raise TypeError( """__get__ called with None as client and class arguments, cannot retrieve""" )
	*/
	PyObject * obj = Py_None;
	PyObject * prop = NULL;
	PyObject * klass = Py_None;
	PyObject * result = NULL;
	PyObject * getValueFunction = NULL;
	PyObject * defaultFunction = NULL;
	if (!PyArg_ParseTuple( args, "O|OO", &prop, &obj, &klass )) {
		return NULL;
	}
	if (obj == Py_None) {
		Py_INCREF( prop );
		return prop;
	}
	getValueFunction = PyObject_GetAttrString( prop, "_getValue" );
	if (getValueFunction) {
		result = PyObject_CallFunction( getValueFunction, "(O)", obj );
		Py_DECREF( getValueFunction );
		if (!result) {
			if (PyErr_ExceptionMatches( PyExc_AttributeError ) ||
				PyErr_ExceptionMatches( PyExc_KeyError )
			) {
				PyErr_Clear();
				defaultFunction = PyObject_GetAttrString( prop, "getDefault" );
				
				if (defaultFunction) {
					result = PyObject_CallFunction( defaultFunction, "(O)", obj);
					Py_DECREF( defaultFunction );
					return result;
				} else {
					PyErr_Format(
						PyExc_AttributeError,
						"'%.50s' object has no 'getDefault'",
						prop->ob_type->tp_name
					);
					return NULL;
				}
			} else {
				/* result here is NULL, with exception already set */
				return result;
			}
		} else {
			/*Py_INCREF( result );*/
			return result;
		}
	} else {
		PyErr_Clear();
		PyErr_Format(
			PyExc_AttributeError,
			"'%.50s' object has no '_getValue'",
			prop->ob_type->tp_name
		);
		return NULL;
	}
}



static PyMethodDef propertyaccel_methods[] = {
	{"_getValue", _getValue, 1, "_getValue( property, client )\n"\
								"C accellerator for default _getValue\n"\
								"property -- basicproperty object, must have \t'name' attribute\n"\
								"client -- must have '__dict__'"},
	{"__get__", __get__, 1, "__get__( property, client )\n"\
								"C accellerator for default __get__\n"\
								"property -- basicproperty object\n"\
								"client -- object being accessed"},
	{NULL, NULL}
};

void
initpropertyaccel(void)
{
	Py_InitModule("propertyaccel", propertyaccel_methods);
}
