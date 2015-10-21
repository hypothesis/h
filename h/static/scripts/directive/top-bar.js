var parseAccountID = require('../filter/persona').parseAccountID;

module.exports = function () {
  return {
    link: function (scope) {
      scope.$watch('authUser', function () {
        scope.account = parseAccountID(scope.authUser);
      });
    },
    restrict: 'E',
    scope: {
      authUser: '=',
      groupsEnabled: '=',
      isSidebar: '=',
      onLogin: '&',
      onLogout: '&',
      searchController: '=',
      accountDialog: '=',
      shareDialog: '=',
      sortBy: '=',
      sortOptions: '=',
      onChangeSortBy: '&',
    },
    templateUrl: 'top_bar.html',
  };
}
