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
       * An object representing the current authentication status.
       */
      auth: '<',
      /**
       * Called when the user clicks on the "Sign in" text.
       */
      onLogin: '&',
      /**
       * Called when the user clicks on the "Sign out" text.
       */
      onLogout: '&',
      /**
       * Whether or not to use the new design for the control.
       *
       * FIXME: should be removed when the old design is deprecated.
       */
      newStyle: '<',
    },
    templateUrl: 'signin_control.html',
  };
};
