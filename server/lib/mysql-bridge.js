/**
 * MySql bridge
 * Used for CRUD of the recorder number
 */

var mysql = require('mysql')
var dbcrud = require('dbcrud')

var recorderModel = {
        recordNumbers: {
            id: { name: 'id', type: 'id' },
            number: { name: 'number', type: 'varchar(45)', orderBy: true },
            comments: { name: 'comments', type: 'varchar(120)' },
            recorded: { name: 'recorded', type: 'tinyint(1)' }

        }
    }

var mySqlBridge = {
	init: function(app, user, password, host, database) {
		var url = 'mysql://' + user + ':' + password + '@' + host + '/' + database;
		mysqlClient = mysql.createConnection(url);
		dbcrud = require('dbcrud').init(mysqlClient, database, recorderModel );
		dbcrud.addRoutes(app)
	}

};

module.exports = mySqlBridge;