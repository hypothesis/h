var angular = require('angular');

module.exports = function () {
  return {
    link: function (scope, elem, attr) {
      var active = true;
      var html = elem.prop('ownerDocument').documentElement;
      var view = elem.prop('ownerDocument').defaultView;

      function onScroll() {
        var clientHeight = html.clientHeight;
        var scrollHeight = html.scrollHeight;
        if (view.scrollY + clientHeight >= scrollHeight - clientHeight) {
          if (active) {
            active = false;
            scope.$apply(attr.windowScroll);
          }
        } else {
          active = true;
        }
      }

      view.addEventListener('scroll', onScroll, false);

      scope.$on('$destroy', function () {
        view.removeEventListener('scroll', onScroll);
      });
    }
  };
};
