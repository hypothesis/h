// @ngInject
module.exports = function () {
  return {
    restrict: 'E',
    scope: {
      /** Specifies whether to use the new design that is part of
       * the groups roll-out.
       * See https://trello.com/c/GxVkM1eN/
       */
      newDesign: '=',
      filterActive: '=',
      filterMatchCount: '=',
      onClearSelection: '&',
      searchQuery: '=',
      selectionCount: '=',
    },
    templateUrl: 'search_status_bar.html',
  };
};
