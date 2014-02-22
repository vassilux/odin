'use strict';

/* Directives */

var fadeToggleDirective = function() {
    return {
        link: function(scope, element, attrs) {
        	console.log('fadeToggleDirective');
            scope.$watch(attrs.uiFadeToggle, function(val, oldVal) {
                if(val === oldVal) return; // Skip inital call
                // console.log('change');
                element[val ? 'fadeIn' : 'fadeOut'](1000);
            });
        }
    }
}


angular.module('app.directives', []).
  directive('appVersion', ['version', function(version) {
    console.log("app.directives appVersion");
    return function(scope, elm, attrs) {
      elm.text(version);
    };
  }]).
  directive('ngDsFade', function () {
  return function(scope, element, attrs) {
  	console.log("ngDsFade");
    element.css('display', 'none');
    scope.$watch(attrs.ngDsFade, function(value) {
      if (value) {
        element.fadeIn(200);
      } else {
        element.fadeOut(100);
      }
    });
  };
 }).
  directive('cellHighlight', function() {
    return {
      restrict: 'C',
      link: function postLink(scope, iElement, iAttrs) {
        iElement.find('td')
          .mouseover(function() {
            $(this).parent('tr').css('opacity', '0.7');
          }).mouseout(function() {
            $(this).parent('tr').css('opacity', '1.0');
          });                
      }
    };
  }).
  directive('context', [function() {
    return {
      restrict    : 'A',
      scope       : '@&', 
      compile: function compile(tElement, tAttrs, transclude) {
        return {
          post: function postLink(scope, iElement, iAttrs, controller) {
            var ul = $('#' + iAttrs.context),
                last = null;
            
            ul.css({ 'display' : 'none'});
  
            $(iElement).click(function(event) {
              ul.css({
                position: "fixed",
                display: "block",
                left: event.clientX + 'px',
                top:  event.clientY + 'px'
              });
              last = event.timeStamp;
            });
            
            $(document).click(function(event) {
              var target = $(event.target);
              if(!target.is(".popover") && !target.parents().is(".popover")) {
                if(last === event.timeStamp){
                  return;  
                }             
                ul.css({
                  'display' : 'none'
                });
              }
            });
          }
        };
      }
    };
  }]);
 
  
