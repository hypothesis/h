'use strict';

// @ngInject
function controller(session) {
  /*jshint validthis:true */
  var vm = this;

  vm.showSidebarTutorial = function () {
    return session.state.preferences.show_sidebar_tutorial;
  };

  vm.dismiss = function () {
    session.dismiss_sidebar_tutorial();
  };
}

/**
 * @ngdoc directive
 * @name sidebarTutorial
 * @description Displays a short tutorial in the sidebar.
 */
// @ngInject
module.exports = function () {
  return {
    bindToController: true,
    controller: controller,
    controllerAs: 'vm',
    restrict: 'E',
    scope: {},
    templateUrl: 'sidebar_tutorial.html'
  };
};
