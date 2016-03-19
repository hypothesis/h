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
    template: require('../../../templates/client/loggedout_message.html'),
  };
};
