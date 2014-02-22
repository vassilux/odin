var os = require("os");
var net = require('net');
var log4js = require("log4js");
var logger = log4js.getLogger('odin_server');


var info = function() {
    return {
        hostname: os.hostname(),
        type: os.type(),
        platform: os.platform(),
        arch: os.arch(),
        release: os.release(),
        time: new Date()
    };

};

var doit = function(host, port, callback) {
    //

    var socket = net.createConnection(port, host, function() {
        logger.debug("sysinfo created connection.");
    });

    /**
     * Send a command to the system info server
     */

    function sendCommand(sock, cmd) {
        var message = JSON.stringify(cmd) + '\r\n';
        sock.write(message);
    }

    socket.on('data', function(data) {
        // Send the message to end the connection
        logger.debug("sysinfo write quit command to the server.");
        callback(data);
        var cmd = {};
        cmd.type = 'quit';
        sendCommand(socket, cmd)

    }).on('connect', function() {
        // Send the request to the server for get the informations
        logger.debug("sysinfo connected to the server, send the sysinfo command.");
        var cmd = {};
        cmd.type = 'getsysinfo';
        sendCommand(socket, cmd)

    }).on('end', function() {
        logger.debug("sysinfo the connection to the server ended.");
    });


};

exports.get = function(port, host, callback) {
    return doit(port, host, function(data) {
        data.info = info();
        return callback(data);
    });
};