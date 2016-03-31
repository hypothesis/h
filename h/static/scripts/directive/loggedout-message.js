'use strict';

module.exports = function () {
  return {
    bindToController: true,
    controllerAs: 'vm',
    //@ngInject
    controller: function (settings) {
      this.serviceUrl = settings.serviceUrl;
    },
    restrict: 'E',
    scope: {
      /**
       * Called when the user clicks on the "Sign in" text.
       */
      onLogin: '&',
    },
    templateUrl: 'loggedout_message.html',
  };
};
