'use strict';

module.exports = function () {
  return {
    bindToController: true,
    controllerAs: 'vm',
    restrict: 'E',
    template: require('../../../templates/client/help_link.html'),
    controller: function () {},
    scope: {
      version: '<',
      userAgent: '<',
      url: '<',
      documentFingerprint: '<',
      auth: '<',
      dateTime: '<',
    },
  };
};
