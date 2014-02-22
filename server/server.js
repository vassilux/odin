var express = require('express'),
  //mongoProxy = require('./lib/mongo-proxy'),
  //config = require('./config.js'),
  passport = require('passport'),
  path = require('path'),
  security = require('./lib/security'),
  xsrf = require('./lib/xsrf'),
  //socket = require('./lib/socket.js'),
  redis = require('redis'),
  RedisStore = require('connect-redis')(express),
  log4js = require("log4js"),
  cjson = require('cjson'),
  config = cjson.load('./config/config.json'),
  cors = require('./lib/cors'),
  sysinfo = require('./lib/sysinfo');

require('express-namespace');
require('./lib/response');

var logfile = path.join(__dirname, '/logs/odin_server.log');

log4js.addAppender(require('log4js/lib/appenders/file').appender(logfile), 'odin_server');
log4js.loadAppender('file');
log4js.addAppender(log4js.appenders.file(logfile), 'odin_server');
var logger = exports.logger = log4js.getLogger('odin_server');
logger.setLevel(config.ODIN_LOG_LEVEL);

/*
 * Instantiate redis
 */

if (process.env.REDISTOGO_URL) {
  var rtg = require('url').parse(process.env.REDISTOGO_URL);
  var redisClient = exports.redisClient = redis.createClient(rtg.port, rtg.hostname);
  redisClient.auth(rtg.auth.split(':')[1]); // auth 1st part is username and 2nd is password separated by ":"
  //
  var redisPublisher = exports.redisPublisher = redis.createClient(rtg.port, rtg.hostname);
  redisPublisher.auth(rtg.auth.split(':')[1]); // auth 1st part is username and 2nd is password separated by ":"
  //
} else {
  var redisClient = exports.redisClient = redis.createClient(config.redis_port, config.redis_host);
  var redisPublisher = exports.redisPublisher = redis.createClient(config.redis_port, config.redis_host);
}

var sessionStore = exports.sessionStore = new RedisStore({
  client: redisClient
});

/** **/
var app = express();


// Serve up the favicon
app.use(express.favicon(config.server_distFolder + '/favicon.ico'));
logger.log("Distribution folder : " + config.server_distFolder);
// First looks for a static file: index.html, css, images, etc.
console.log("static directory : " + config.server_distFolder);
//
app.use(config.server_staticUrl, express.compress());
app.use(config.server_staticUrl, express['static'](path.resolve(__dirname, config.server_distFolder)));
app.use(express.static(config.server_distFolder));
app.use(config.server_distFolder, function(req, res, next) {
  res.send(404); // If we get here then the request for a static file is invalid
});

app.use(express.logger()); // Log requests to the console
app.use(express.bodyParser()); // Extract the data from the body of the request - this is needed by the LocalStrategy authenticate method
app.use(express.cookieParser(config.server_cookieSecret)); // Hash cookies with this secret
app.use(express.cookieSession()); // Store the session in the (secret) cookie
app.use(passport.initialize()); // Initialize PassportJS
app.use(passport.session()); // Use Passport's session authentication strategy - this stores the logged in user in the session and will now run on any request
//app.use(xsrf); // Add XSRF checks to the request
//initialize cross domain options 
var corsOptions = {
  maxAge: 60 * 60 * 24 * 7, //1 week
};
//
app.use(cors(corsOptions));

app.use(express.session({
  key: "Odin",
  store: sessionStore
}));

security.initialize(config.mongo_dbUrl, config.security_dbName, config.security_usersCollection); // Add a Mongo strategy for handling the authentication
//
app.use(function(req, res, next) {
  if (req.user) {
    logger.log('Current User:', req.user.firstName, req.user.lastName);
  } else {
    logger.log('Unauthenticated');
  }
  next();
});

/**
 * Helper to make a call from a http request
 * Source and destiantion http parameters must be provided by caller
 *
 */
app.get('/originate', function(req, res) {
  var source = req.query["source"];
  var destination = req.query["destination"];
  var type = req.query["dial"];
  var user = req.query["user"];
  var servername = req.query["servername"];
  //
  if (type == undefined) {
    type = "dial";
  };
  if (user == undefined) {
    user = "annonymus";
  }
  if (servername == undefined) {
    res.send("Hey buddy, Please provide the server target name");
    return;
  }

  if (source == undefined || destination == undefined) {
    res.send("Hey buddy, I can not originate a call for source 11[" +
      source + "]" + " and destination [" + destination + "]");
    return;
  }

  var msg = {
    id: 'originate',
    servername: servername,
    type: type,
    user: user,
    source: "SIP/" + source,
    destination: destination
  };
  redisPublisher.publish('odin_ami_request_channel', JSON.stringify(msg));
  res.send("Hey buddy, the call is originated from " + source + " to " + destination);

});

/**
 *
 */
app.get('/chan_spy', function(req, res) {
  var servername = req.query['servername'];
  var user = req.query['user'];
  var spyer = req.query['spyer'];
  var spyee = req.query['spyee'];
  var type = req.query['type'];

  if (servername == undefined) {
    res.send("Hey buddy, Please provide the server target name");
    return;
  }

  if (spyer == undefined || spyee == undefined) {
    res.send("Hey buddy, I can not spy for spyer [" +
      spyer + "]" + " and spyee [" + spyee + "]");
    return;
  }

  if(type == undefined){
    res.send("Hey buddy, I can not spy without the type spyer [" +
      spyer + "]" + " and spyee [" + spyee + "]");
    return;
  }

  if (user == undefined) {
    user == "annonymus";
  }

  var msg = {
    id: 'chan_spy',
    servername: servername,
    type: type,
    user: user,
    spyer: spyer,
    spyee: spyee
  };
  redisPublisher.publish('odin_ami_request_channel', JSON.stringify(msg));
  res.send("Start spyig for spyer " + spyer + " and spyee " + spyee);

});

//
app.post('/login', function(req, res) {
  logger.log('Get request to user login : ');
  security.login(req, res);
});

//
app.post('/logout', function(req, res) {
  logger.log('Get request to user logout : ');
  security.logout(req, res);
});

// Retrieve the current user
app.get('/current-user', function(req, res) {
  logger.log('server', 'current-user');
  security.sendCurrentUser(req, res);
});

// Retrieve the current user only if they are authenticated
app.get('/authenticated-user', function(req, res) {

  security.authenticationRequired(req, res, function() {
    security.sendCurrentUser(req, res);
  });
});

// Retrieve the current user only if they are admin
app.get('/admin-user', function(req, res) {
  security.adminRequired(req, res, function() {
    security.sendCurrentUser(req, res);
  });
});

/**
 *
 */
app.get('/sysinfo', function(req, res) {
  sysinfo.get('localhost', 3003, function(data) {
    console.log("data : " + data);
    res.contentType('json');
    res.send(data);
  });
});


// inspired http://pixelhandler.com/blog/2012/02/09/develop-a-restful-api-using-node-js-with-express-and-mongoose/
/**
 * Simple REST service for users management
 */
app.get('/api/users', function(req, res) {
  security.listUsers(function(err, users) {
    var empty = [];
    res.contentType('json');
    if (!err) {
      res.send(JSON.stringify(users));

    } else {
      res.send(JSON.stringify(empty));
    }

  });

});

/**
 * Fetch an user by the username
 */
app.get('/api/users/:username', function(req, res) {
  logger.log('Get request to get the user : ' + req.params.username);
  var username = req.params.username;
  res.contentType('json');
  security.checkIfUserExist(username, function(err, user) {
    if (err) {
      res.send('error: An error has occurred when check if the user exist.', 500);
    } else {
      if (user) {
        res.send(user, 200);
      } else {
        res.send('error : Can not find the user ' + username + '.', 404);
      }
    }
  });
});

/**
 * Create a new user
 */
app.post('/api/users', function(req, res) {
  logger.log('Get request to create a user : ' + req.body.username);
  var newUser = {
    firstName: req.body.firstName,
    lastName: req.body.lastName,
    username: req.body.username,
    password: req.body.password,
    admin: req.body.admin
  };

  res.contentType('json');
  security.checkIfUserExist(newUser.username, function(err, user) {
    if (err) {
      res.send('error: An error has occurred when check if the user exist.', 500);
    } else {
      if (!user) {
        security.saveUser(newUser, function(err) {
          if (!err) {
            res.send(newUser, 200);
          } else {
            res.send('error :An error has occurred when create user.', 500);
          }
        });
      } else {
        res.send('error :An error has occurred when create user.', 404);
      }
    }

  });

});

/**
 * Delete an user by username
 */
app.del('/api/users/:username', function(req, res) {
  logger.log('Get request to delete a user : ' + req.params.username);
  var username = req.params.username;

  res.contentType('json');
  security.checkIfUserExist(username, function(err, user) {
    if (err) {
      res.send('error: An error has occurred when check if the user exist.', 500);
    } else {
      if (user) {
        logger.log('Deleting user : ' + req.params.username);
        security.deleteUser(username, function(err, user) {
          if (!err) {
            res.send(username);
          } else {
            res.send('error: An error has occurred when delete the user : ' + +username + '.', 500);
          }
        });
      } else {
        res.send('error :An error has occurred when process the user deleting ' + username + '.', 404);
      }
    }

  });

});

/**
 * Update an user
 */
app.put('/api/users/:username', function(req, res) {
  logger.debug('Get request to update the user : ' + req.params.username);
  var username = req.params.username;
  //logger.log('Get request to update the body part: ' + JSON.stringify(req.body));

  var newUser = {
    firstName: req.body.firstName,
    lastName: req.body.lastName,
    username: req.body.username,
    password: req.body.password,
    admin: req.body.admin
  };
  //logger.log('Get request to update the new user : ' + req.body); //JSON.stringify(newUser.username));

  res.contentType('json');
  security.updateUser(newUser, function(err, user) {
    if (err) {
      console.log(" got error fot updated user : " + err);
      res.send('error: An error has occurred when delete the user : ' + username, 500);
    } else {
      console.log(" updated user : " + JSON.stringify(user));
      res.send(username);
    }
  });

});


// This route deals enables HTML5Mode by forwarding missing files to the index.html
app.all('/*', function(req, res) {
  // Just send the index.html for other files to support HTML5Mode
  console.log("send index.html");
  res.sendfile('index.html', {
    root: config.server_distFolder
  });
});

// A standard error handler - it picks up any left over errors and returns a nicely formatted http 500 error
app.use(express.errorHandler({
  dumpExceptions: true,
  showStack: true
}));
//
// Start up the server on the port specified in the config
if (module.parent === null) {
  exports.server = app.listen(config.server_listenPort);
  logger.log('Odin App Server - listening on port: ' + config.server_listenPort);
  //Hook Socket.io into Express
  require('./lib/sockets');
}