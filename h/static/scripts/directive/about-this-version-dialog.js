'use strict';

/**
 * @ngdoc directive
 * @name aboutThisVersionDialog
 * @description Displays product version and environment info
 */
// @ngInject
module.exports = function () {
  return {
    bindToController: true,
    controllerAs: 'vm',
    // @ngInject
    controller: function ($scope, $window, settings, crossframe) {
      this.userAgent = $window.navigator.userAgent;
      this.version = settings.release;
      this.dateTime = new Date();

      $scope.$watchCollection(
        function () {
          return crossframe.frames;
        },
        function (frames) {
          if (frames.length === 0) {
            return;
          }
          this.url = frames[0].uri;
          this.documentFingerprint = frames[0].documentFingerprint;
        }.bind(this)
      );
    },
    restrict: 'E',
    template: require('../../../templates/client/about_this_version_dialog.html'),
    scope: {
      auth: '<',
      onClose: '&',
    }
  };
};
