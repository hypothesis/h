module.exports = function () {
  return {
    restrict: 'E',
    scope: {
      filterActive: '=',
      filterMatchCount: '=',
      onClearSelection: '&',
      searchQuery: '=',
      selectionCount: '=',
    },
    templateUrl: 'search_status_bar.html',
  };
};
