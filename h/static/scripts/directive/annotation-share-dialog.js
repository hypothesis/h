'use strict';

var angular = require('angular');

module.exports = function () {
  return {
    bindToController: true,
    controllerAs: 'vm',
    restrict: 'E',
    template: require('../../../templates/client/annotation_share_dialog.html'),
    // @ngInject
    controller: function ($scope, $element) {
      var shareLinkInput = $element.find('input')[0];

      $scope.$watch('vm.isOpen', function (isOpen) {
        if (isOpen) {
          // Focus the input and select it once the dialog has become visible
          setTimeout(function () {
            shareLinkInput.focus();
            shareLinkInput.select();
          });

          var hideListener = function (event) {
            $scope.$apply(function () {
              if (!$element[0].contains(event.target)) {
                document.removeEventListener('click', hideListener);
                this.onClose();
              }
            }.bind(this));
          }.bind(this);

          // Stop listening for clicks outside the dialog once it is closed.
          // The setTimeout() here is to ignore the initial click that opens
          // the dialog.
          setTimeout(function () {
              document.addEventListener('click', hideListener);
            },
            0
          );
        }
      }.bind(this));

      this.copyToClipboard = function (event) {
        var $container = angular.element(event.currentTarget).parent();
        var shareLinkInput = $container.find('input')[0];

        try {
          shareLinkInput.select();
          document.execCommand('copy');

          this.copyToClipboardMessage = 'Link copied to clipboard!';
        } catch (ex) {
          this.copyToClipboardMessage = 'Select and copy to share.';
        } finally {
          setTimeout(function () {
              this.copyToClipboardMessage = null;
              $scope.$digest();
            }.bind(this),
            1000);
        }
      }.bind(this);
    },
    scope: {
      group: '<',
      uri: '<',
      isPrivate: '<',
      isOpen: '<',
      onClose: '&',
    }
  };
};
