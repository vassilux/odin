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
    function sendCommand(sock, cmd) {
        var message = JSON.stringify(cmd) + '\r\n';
        sock.write(message);
    }

    try {
        var socket = new net.Socket();
        socket.connect(port, host, function() {
            logger.debug("sysinfo connected to the server, send the sysinfo command.");
            var cmd = {};
            cmd.type = 'getsysinfo';
            sendCommand(socket, cmd)
        });

        socket.on('data', function(data) {
            // Send the message to end the connection
            logger.debug("sysinfo write quit command to the server.");
            callback(data);
            var cmd = {};
            cmd.type = 'quit';
            sendCommand(socket, cmd)

        }).on('end', function() {
            logger.debug("sysinfo the connection to the server ended.");
        }).on('error', function(error) {
            logger.debug("Try get the system informations from server on address " + host + ' and port ' + port + '. Get an error' + error);
            return callback('{}');
        });
    } catch (e) {
        logger.debug("Can not connect to the system informations server on address " + host + ' and port ' + port + '.');
        callback('{}');
    }



};

exports.get = function(port, host, callback) {
    try {
        logger.debug("Try get the system informations from server on address " + host + ' and port ' + port + '.');
        return doit(port, host, function(data) {
            data.info = info();
            return callback(data);
        });
    } catch (e) {
        logger.error("doit function failed with the exception : " + e + '.');
        return callback('{}');
    }


};