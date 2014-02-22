/*
 * Initialize the security module
 * Module used also as tiny wrapper for users CRUD
 */
//the logger must be initialized by parent, server;js
var log4js = require("log4js");
var logger = log4js.getLogger('odin_server');
//
var express = require('express');
var passport = require('passport');
var LocalStrategy = require('passport-local').Strategy;



var mongoose = require('mongoose');
var Schema = mongoose.Schema;

var User = require('./user');

var MongoStrategy = require('./mongo-strategy');
var app = express();

var filterUser = function(user) {
    if(user) {
      return {
        user: {
          id: user._id.$oid,
          username: user.username,
          firstName: user.firstName,
          lastName: user.lastName,
          admin: user.admin
        }
      };
    } else {
      return {
        user: null
      };
    }
  };

// Define local strategy for Passport
passport.use(new LocalStrategy({
  usernameField: 'username',
  passwordField: 'password'
}, function(username, password, done) {
  logger.debug("passport authenticate for user : " + username);
  User.authenticate(username, password, function(err, user) {
    return done(err, user);
  });
}));

// serialize user on login
passport.serializeUser(function(user, done) {
  logger.debug("passport.serializeUser : " + user);
  done(null, user.id);
});

// deserialize user on logout
passport.deserializeUser(function(id, done) {
  logger.debug("passport.deserializeUser : " + id);
  User.findById(id, function(err, user) {
    done(err, user);
  });
});



var security = {// Note * allows ALL domains consider listing out trusted domains 
    
  initialize: function(dbUrl, dbName) {
    mongoose.connect('mongodb://' + dbUrl + '/' + dbName);
    // Check connection to mongoDB
    mongoose.connection.on('open', function() {
      logger.info('We have connected to mongodb');
      logger.debug('I check for defautls users : admin and demo.');
      //
      User.findOne({
        username: 'admin'
      }, function(err, obj) {
        if(obj == null) {
          var newUser = new User({
            firstName: "Default",
            lastName: "Administrator",
            username: "admin",
            password: "admin",
            admin: true
          });
          newUser.save(function(e) {
            if(e) {
              throw e;
            } else {
              logger.info('I create default user admin.Please change the password.');
            }
          });

        }
        //
        User.findOne({
          username: 'user'
        }, function(err, obj) {
          if(obj == null) {
            var newUser = new User({
              firstName: "ESI",
              lastName: "User",
              username: "user",
              password: "user"
            });
            newUser.save(function(e) {
              if(e) {
                throw e;
              } else {
                console.info('I create default user.Please change the password.');
              }
            });
          }
        });

      });



    });

  },



  // save a user
  saveUser: function(userInfo, callback) {
    console.log('saveUser : ' + JSON.stringify(userInfo));
    var newUser = new User({
      firstName: userInfo.firstName,
      lastName: userInfo.lastName,
      username: userInfo.username,
      password: userInfo.password,
      admin: userInfo.admin
    });

    newUser.save(function(err) {
      if(err) {
        callback(err, userInfo);
      } else {
        callback(null, userInfo);
      }

    });
  },

  checkIfUserExist: function(username, callback) {
    User.findOne({
      username: username
    }, function(err, obj) {
      callback(err, obj);
    });
  },

  updateUser: function(userInfo, callback) {
    User.findOne({
      username: userInfo.username
    }, function(err, result) {
      if(err) {
        logger.debug('Can not find the user user updated ' + userInfo.username + ' to update.');
        callback(err, null);
      } else {
        if(result == null) {
          logger.debug('result is null  ' + JSON.stringify(result) + '.');
          callback(err, null);
        } else {
          try {
            result.firstName = userInfo.firstName;
            result.lastName = userInfo.lastName;
            result.username = userInfo.username;
            result.admin = userInfo.admin;
            result.password = userInfo.password;

            result.update();
            result.save(function(err) {
              if(!err) {
                logger.debug('user updated ' + JSON.stringify(result) + '.');
                callback(null, result);
              } else {
                logger.debug('Can not update the user ' + userInfo.username + ' ' + err + '.');
                callback(err, null);
              }
            });
          } catch(e) {
            logger.error('Got an exception when update the user ' + userInfo.username + ' ' + e + '.');
            callback(e, null);
          }

        }

      }
    });
  },

  deleteUser: function(username, callback) {
    User.findOne({
      username: username
    }, function(err, result) {
      if(err) {
        callback(err, null);
      } else {
        if(result == null) {
          callback(err, null);
        } else {
          result.remove();
          result.save(function(err) {
            if(!err) {
              callback(null, {});
            } else {
              callback(err, null);
            }
          });
        }

      }
    });
  },

  authenticationRequired: function(req, res, next) {
    console.log('authRequired');
    if(req.isAuthenticated()) {
      next();
    } else {
      res.send(401, filterUser(req.user));
    }
  },
  adminRequired: function(req, res, next) {
    console.log('adminRequired');
    if(req.user && req.user.admin) {
      next();
    } else {
      res.send(401, filterUser(req.user));
    }
  },
  sendCurrentUser: function(req, res, next) {
  	  console.log("sendCurrentUser");
     
    res.json(200, filterUser(req.user));
    res.end();
  },

  login: function(req, res, next) {
    function authenticationFailed(err, user, info) {
      logger.error("authenticationFailed " + info + " user " + user);
      if(err) {
        return next(err);
      }
      if(!user) {
        return res.json(filterUser(user));
      }
      req.logIn(user, function(err) {
        if(err) {
          return next(err);
        }
        return res.json(filterUser(user));
      });
    }
    //
	console.log("passport authenticate local");
	//
    return passport.authenticate('local', authenticationFailed)(req, res, next);
  },

  logout: function(req, res, next) {
    req.logout();
    res.send(204);
  },

  listUsers: function(cb) {
    User.find({}, function(err, users) {
      if(!err) {
        cb(err, users);
      } else {
        cb(err);
      }

    });
  }


};

module.exports = security;
