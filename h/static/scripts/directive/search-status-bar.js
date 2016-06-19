'use strict';

// @ngInject
module.exports = function () {
  return {
    controller: function () {},
    restrict: 'E',
    scope: {
      filterActive: '<',
      filterMatchCount: '<',
      onClearSelection: '&',
      searchQuery: '<',
      selectedTab: '<',
      selectionCount: '<',
      tabAnnotations: '<',
      tabNotes: '<',
      totalAnnotations: '<',
      totalNotes: '<',
    },
    template: require('../../../templates/client/search_status_bar.html'),
  };
};
