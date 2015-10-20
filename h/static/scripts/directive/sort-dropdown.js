module.exports = function () {
  return {
    restrict: 'E',
    scope: {
      /** The name of the currently selected sort criteria. */
      sortBy: '=',
      /** A list of choices that the user can opt to sort by. */
      sortOptions: '=',
      /** If true, the menu uses just an icon, otherwise
       * it displays 'Sorted by {{sortBy}}'
       */
      showAsIcon: '=',
      /** Called when the user changes the current sort criteria. */
      onChangeSortBy: '&',
    },
    templateUrl: 'sort_dropdown.html',
  }
}
