// Keep track of which names are used so that there are no duplicates
var parent = module.parent.exports,
  app = parent.app,
  server = parent.server,
  express = require('express'),
  redisClient = parent.redisClient,
  redisPublisher = parent.redisPublisher,
  logger = parent.logger,
  sessionStore = parent.sessionStore,
  sio = require('socket.io'),
  connect = require('connect'),
  parseCookies = require('connect').utils.parseSignedCookies,
  cookie = require('cookie'),
  passportSocketIo = require("passport.socketio"),
  xtend = require('xtend'),
  config = parent.config,
  fs = require('fs'),
  sysinfo = parent.sysinfo;

var sessionStore = new connect.session.MemoryStore(),
  sessionSecret = 'asdasdsdas1312312',
  sessionKey = 'odin-session-key',
  sessionOptions = {
    store: sessionStore,
    key: sessionKey,
    secret: sessionSecret
  };

var options = {};
//
//
var io = sio.listen(server);
io.set('log level', 1);
//io.set('authorization', function () {
//this.set('authorization', passportSocketIo.authorize(xtend(sessionOptions, options)));
/*  this.set('log level', 0);
  if(hsData.headers.cookie) {
    var cookies = parseCookies(cookie.parse(hsData.headers.cookie), config.server.cookieSecret)
      , sid = cookies['Odin'];

    sessionStore.load(sid, function(err, session) {
      if(err || !session) {
        return accept('Error retrieving session!', false);
      }

      hsData.balloons = {
        user: session.passport.user,
        room: /\/(?:([^\/]+?))\/?$/g.exec(hsData.headers.referer)[1]
      };

      return accept(null, true);
      
    });
  } else {
    return accept('No cookie transmitted.', false);
  }*/
//});
/*io.configure(function() {
  console.log("io.configure ");
  io.set('store', new sio.RedisStore({client: client}));
  io.enable('browser client minification');
  io.enable('browser client gzip');
});*/

/**
 * Connected socket.io users
 * Keep the tuple user/socket for dispatching private messages to users
 */
var ioUsers = (function() {
  var users = {};

  var set = function(name, socket) {
    if (!name || users[name]) {
      return false;
    } else {
      users[name] = socket;
      return true;
    }
  };

  var getSocket = function(name) {
    if (!users[name]) {
      return null;
    } else {
      return users[name];
    }
  };

  // serialize claimed names as an array
  var get = function() {
    var res = [];
    for (user in names) {
      res.push(user);
    }

    return res;
  };

  var free = function(name) {
    if (users[name]) {
      delete users[name];
    }
  };

  return {
    set: set,
    free: free,
    get: get,
    getSocket: getSocket
  };
}());

//
redisClient.subscribe('odin_snmp_channel');
redisClient.subscribe('odin_ami_data_channel');

redisClient.on("subscribe", function(channel, msg) {
  logger.info("redis client subscribe to channel : %s", channel);
});

redisClient.on("message", function(channel, msg) {
  var redisMsg = JSON.parse(msg);
  if (channel === 'odin_snmp_channel') {
    logger.info("I got message from redis  : %s", msg);
    io.sockets.emit(redisMsg.id, msg);
  } else if (channel === 'odin_ami_data_channel') {
    logger.info("I got message from redis channel %s message : %s", channel, redisMsg.id);
    io.sockets.emit('ami:' + redisMsg.id, msg);
  } else {
    logger.debug("I got message from redis  : %s channel, this channel is ignored.", channel);
  }

});

io.sockets.on('connection', function(socket) {
  //
  logger.debug("Sockets : New connection comming, there are " + io.sockets.clients().length + " connected clients.");
  // Handle the comming user
  socket.on('user:join', function(data) {
    var userJoin = JSON.parse(data);
    socket.username = userJoin.username;
    socket.isAdmin = userJoin.isAdmin;
    //
    ioUsers.set(userJoin.username, socket);
    logger.info("user:joint  " + socket.username);
    // notify other users has joined
    var newUserJoin = {
      username: socket.username,
      isAdmin: socket.isAdmin
    };
    socket.broadcast.emit('user:join', newUserJoin);
    //
    var msg = {
      id: 'get_servers',
      user: userJoin.username
    };
    logger.info("Sockets : Get the ami server message get_servers for user: " + userJoin.username);
    redisPublisher.publish('odin_ami_request_channel', JSON.stringify(msg));
    //
  });

  socket.on('ami:originate', function(data) {
    var request = JSON.parse(data);
    logger.info("Sockets : Get the ami server message originate from user: " + data);
    var msg = {
      id: 'originate',
      servername: request.servername,
      type: request.type,
      user: request.username,
      source: request.source,
      destination: request.destination
    };

    redisPublisher.publish('odin_ami_request_channel', JSON.stringify(msg));
  });

  socket.on('ami:chanspy', function(data){
    var request = JSON.parse(data);
    logger.info("Sockets : Get the ami server message chanspy: " + data);
    var msg = {
      id: 'chan_spy',
      servername: request.servername,
      type: request.type,
      user: request.username,
      spyer: request.spyer,
      spyee: request.spyee
    };
    redisPublisher.publish('odin_ami_request_channel', JSON.stringify(msg));
  });

  socket.on('ami:getserverstatus', function(data) {
    var request = JSON.parse(data);
    logger.info("Sockets : Get the ami server message get_server_status for user: " + request.username);
    var msg = {
      id: 'get_server_status',
      servername: request.servername,
      user: request.username
    };

    redisPublisher.publish('odin_ami_request_channel', JSON.stringify(msg));
  });

  socket.on('ami:getactivecalls', function(data) {
    var request = JSON.parse(data);
    var msg = {
      id: 'get_active_calls',
      servername: request.servername,
      user: request.username
    };
    //
    redisPublisher.publish('odin_ami_request_channel', JSON.stringify(msg));
  });

  // handle the user logouts
  socket.on('user:left', function(data) {
    socket.broadcast.emit('user:left', {
      username: socket.username
    });
    ioUsers.free(socket.username);
  });

  socket.on('ami:getpeers', function(data) {
    var msg = {
      id: 'getpeers',
      user: data.username
    };
    redisPublisher.publish('odin_ami_action_channel', JSON.stringify(msg));
  });

  socket.on('ami:request_info', function(data) {
    var request = JSON.parse(data);
    var msg = {
      id: 'request_info',
      servername: request.servername,
      user: request.username,
      command: request.command
    };
    redisPublisher.publish('odin_ami_request_channel', JSON.stringify(msg));
  });

  socket.on('ami:hangupchannel', function(data) {
    var request = JSON.parse(data);
    var msg = {
      id: 'hangupchannel',
      servername: request.servername,
      user: request.username,
      channel: request.channel
    };
    redisPublisher.publish('odin_ami_request_channel', JSON.stringify(msg));
  });

  socket.on('ami:parkchannel', function(data) {
    var request = JSON.parse(data);
    var msg = {
      id: 'parkchannel',
      servername: request.servername,
      user: request.username,
      channel: request.channel,
      announce: request.announce
    };
    redisPublisher.publish('odin_ami_request_channel', JSON.stringify(msg));
  });

  socket.on('ami:transfer', function(data) {
    console.log("got ami:transfer");
    var request = JSON.parse(data);
    var type = request.type;
    if(type == undefined){
      type = "none"
    }
    var msg = {
      id: 'transfer',
      servername: request.servername,
      user: request.username,
      source: request.source,
      destination: request.destination,
      type: type
    };
    redisPublisher.publish('odin_ami_request_channel', JSON.stringify(msg));
  });

  socket.on('ami:start_monitor', function(data){
    var request = JSON.parse(data);
    var format = request.format;
    if(format == undefined){
      format = "wav"
    }
    var file = request.file;
    if(file == undefined){
      file = "test";
    }

    var msg = {
      id: 'start_monitor',
      servername: request.servername,
      user: request.username,
      channel: request.channel,
      file: request.file,
      format: request.format
    };
    redisPublisher.publish('odin_ami_request_channel', JSON.stringify(msg));
  });

  socket.on('ami:stop_monitor', function(data){
    var request = JSON.parse(data);
    var msg = {
      id: 'stop_monitor',
      servername: request.servername,
      user: request.username,
      channel: request.channel,
    };
    redisPublisher.publish('odin_ami_request_channel', JSON.stringify(msg));
  });

  socket.on('ami:chan_spy', function(data){
    var request = JSON.parse(data)
    var msg = {
      id : 'chan_spy',
      servername: request.servername,
      user: request.username,
      spyer: request.spyer,
      spyee: request.spyee,
      type: request.type
    };
    redisPublisher.publish('odin_ami_request_channel', JSON.stringify(msg));

  });

  //system command part
  socket.on('sys:getsysinfo', function(data) {
    sysinfo.get('localhost', 3003, function(err, data){
        console.log("data : " + data);
        socket.emit('sysinfo', data);
      });
  });

  /**
   * Handle disconnects
   * Cleanup user from the user array
   */
  socket.on('disconnect', function() {
    var so = ioUsers.getSocket(socket.username);
    logger.info("User left " + socket.username + " and I find socket : " + (so != null ? true : false));
    var data = {
      username: socket.username,
      isAdmin: socket.isAdmin
    };
    socket.broadcast.emit('disconnect user:left', data);
    ioUsers.free(socket.username);
    logger.debug("Socket.io client disconnected , there are " + io.sockets.clients().length + " connected clients.")
  });
});