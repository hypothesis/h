'use strict';

var events = require('../events');

// @ngInject
function GroupListController($scope, $window, groups) {
  $scope.leaveGroup = function (groupId) {
    var groupName = groups.get(groupId).name;
    var message = 'Are you sure you want to leave the group "' +
      groupName + '"?';
    if ($window.confirm(message)) {
      groups.leave(groupId);
    }
  }

  $scope.focusGroup = function (groupId) {
    groups.focus(groupId);
  }
}

/**
 * @ngdoc directive
 * @name groupList
 * @restrict AE
 * @description Displays a list of groups of which the user is a member.
 */
// @ngInject
function groupList(groups, $window) {
  return {
    controller: GroupListController,
    link: function ($scope, elem, attrs) {
      $scope.groups = groups;

      $scope.createNewGroup = function() {
        $window.open('/groups/new', '_blank');
      }
    },
    restrict: 'E',
    scope: {
      auth: '='
    },
    templateUrl: 'group_list.html'
  };
};

module.exports = {
  directive: groupList,
  Controller: GroupListController
};
