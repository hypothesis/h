'use strict';

// @ngInject
module.exports = function () {
  return {
    restrict: 'E',
    scope: {
      filterActive: '<',
      filterMatchCount: '<',
      onClearSelection: '&',
      searchQuery: '<',
      selectionCount: '<',
      totalCount: '<',
    },
    templateUrl: 'search_status_bar.html',
  };
};
