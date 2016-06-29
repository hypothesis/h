'use strict';

module.exports = function () {
  return {
    bindToController: true,
    controllerAs: 'vm',
    //@ngInject
    controller: function (annotationUI) {
      this.selectTab = function (type) {
        annotationUI.clearSelectedAnnotations();
        annotationUI.selectTab(type);
      };
    },
    restrict: 'E',
    scope: {
      selectedTab: '<',
      totalAnnotations: '<',
      totalNotes: '<',
      tabAnnotations: '<',
      tabNotes: '<',
    },
    template: require('../../../templates/client/selection_tabs.html'),
  };
};
