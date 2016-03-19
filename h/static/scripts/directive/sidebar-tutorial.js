'use strict';

// @ngInject
function SidebarTutorialController(session) {
  /*jshint validthis:true */
  var vm = this;

  vm.showSidebarTutorial = function () {
    if (session.state.preferences) {
      if (session.state.preferences.show_sidebar_tutorial) {
        return true;
      }
    }
    return false;
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
module.exports = {
  directive: function () {
    return {
      bindToController: true,
      controller: SidebarTutorialController,
      controllerAs: 'vm',
      restrict: 'E',
      scope: {},
      template: require('../../../templates/client/sidebar_tutorial.html'),
    };
  },
  Controller: SidebarTutorialController
};
