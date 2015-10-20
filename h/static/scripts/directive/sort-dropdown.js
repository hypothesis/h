module.exports = function () {
  return {
    restrict: 'E',
    scope: {
      sortBy: '=',
      sortOptions: '=',
      onChangeSortBy: '&',
    },
    templateUrl: 'sort_dropdown.html',
  }
}
