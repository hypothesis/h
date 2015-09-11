'use strict';

/**
 * @ngdoc directive
 * @name groupList
 * @restrict AE
 * @description Displays a list of groups of which the user is a member.
 */

// @ngInject
module.exports = function (groups) {
  return {
    link: function (scope, elem, attrs) {
      scope.groups = groups;
    },
    restrict: 'AE',
    scope: {},
    templateUrl: 'group_list.html'
  };
};
