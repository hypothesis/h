module.exports = function () {
  return {
    restrict: 'E',
    scope: {
      sortBy: '=',
      sortOptions: '=',
      showAsIcon: '=',
      onChangeSortBy: '&',
    },
    templateUrl: 'sort_dropdown.html',
  }
}
