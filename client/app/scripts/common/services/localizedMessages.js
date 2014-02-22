angular.module('services.localizedMessages', []).factory('localizedMessages', ['$interpolate', 'localize', 
  function ($interpolate, localize) {

  var handleNotFound = function (msg, msgKey) {
    return msg || '?' + msgKey + '?';
  };

  return {
    get : function (msgKey, interpolateParams) {
      var msg =  localize.getLocalizedString(msgKey); //i18nmessages[msgKey];
      if (msg) {
        return $interpolate(msg)(interpolateParams);
      } else {
        return handleNotFound(msg, msgKey);
      }
    }
  };
}]);