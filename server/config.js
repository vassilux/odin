path = require('path');

module.exports = {
  mongo: {
    dbUrl: '127.0.0.1',            // The base url of the MongoLab DB server
    apiKey: '4fb51e55e4b02e56a67b0b66'                 // Our MongoLab API key
  },
  security: {
    dbName: 'odin',                                   // The name of database that contains the security information
    usersCollection: 'users'                            // The name of the collection contains user information
  },
  server: {
    listenPort: 3001,                                   // The port on which the server is to listen (means that the app is at http://localhost:3000 for instance)
    distFolder: path.resolve(__dirname, '../client/app'),  // The folder that contains the application files (note that the files are in a different repository) - relative to this file
    staticUrl: '/static',                               // The base url from which we serve static files (such as js, css and images)
    cookieSecret: 'odin-app'                         // The secret for encrypting the cookie
  }
};
