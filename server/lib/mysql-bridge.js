/**
 * MySql bridge
 * Used for CRUD of the recorder number
 */

var mysql = require('mysql')
var dbcrud = require('dbcrud')
var ConnectionConfig = require('mysql/lib/ConnectionConfig')

var recorderModel = {
    recordNumbers: {
        id: {
            name: 'id',
            type: 'id'
        },
        number: {
            name: 'number',
            type: 'varchar(45)',
            orderBy: true
        },
        comments: {
            name: 'comments',
            type: 'varchar(120)'
        },
        recorded: {
            name: 'recorded',
            type: 'tinyint(1)'
        }
    },
    settings: {
        id: {
            name: 'id',
            type: 'id'
        },
        variable: {
            name: 'variable',
            type: 'varchar(45)'
        },
        value: {
            name: 'value',
            type: 'varchar(45)'
        },
    }
}

var mySqlBridge = {
    init: function(app, user, password, host, database) {
        var url = 'mysql://' + user + ':' + password + '@' + host + '/' + database;
        var mysqlConnectionConfig = new ConnectionConfig(url);
        //var pool = mysql.createPool(mysqlConnectionConfig);
        connection = mysql.createConnection(url);
        dbcrud = require('dbcrud').init(connection, database, recorderModel);
            log = true;
            //very ... bad
            app.del('/rc1/recordNumbers/:id', function(req, res) {
                var id = req.params.id;

                res.contentType('json');
                var sql = "delete from recordNumbers where id = " + dbcrud.client.escape(id);
                console.log("query " + sql + "\n");

                dbcrud.client.query(sql, function(error, data, fields) {
                    res.send("");

                });


            });
            //
            dbcrud.addRoutes(app);
        
    }

};

module.exports = mySqlBridge;