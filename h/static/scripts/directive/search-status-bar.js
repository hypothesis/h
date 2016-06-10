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
      selectionCount: '<',
      totalCount: '<',
    },
    template: require('../../../templates/client/search_status_bar.html'),
  };
};
