'use strict';

var VIA_PREFIX = 'https://via.hypothes.is/';

// @ngInject
function ShareDialogController($scope, $element, crossframe) {
  var ctrl = this;

  function updateViaLink(frames) {
    if (!frames.length) {
      ctrl.viaPageLink = '';
      return;
    }

    // Check to see if we are on a via page. If so, we just return the URI.
    if (frames[0].uri.indexOf(VIA_PREFIX) === 0) {
      ctrl.viaPageLink = frames[0].uri;
    } else {
      ctrl.viaPageLink = VIA_PREFIX + frames[0].uri;
    }
  }

  var viaInput = $element[0].querySelector('.js-via');
  viaInput.focus();
  viaInput.select();

  $scope.$watchCollection(function () { return crossframe.frames; },
    updateViaLink);
}

module.exports = function () {
  return {
    restrict: 'E',
    bindToController: true,
    controller: ShareDialogController,
    controllerAs: 'vm',
    scope: {
      onClose: '&',
    },
    template: require('../../../templates/client/share_dialog.html'),
  };
};
