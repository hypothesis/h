'use strict';

module.exports = function () {
  return {
    restrict: 'E',
    scope: {
      auth: '<',
      isSidebar: '<',
      onShowAboutVersionDialog: '&',
      onLogin: '&',
      onLogout: '&',
      onSharePage: '&',
      searchController: '<',
      accountDialog: '<',
      shareDialog: '<',
      sortBy: '<',
      sortOptions: '<',
      onChangeSortBy: '&',
    },
    template: require('../../../templates/client/top_bar.html'),
  };
};
