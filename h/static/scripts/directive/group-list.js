'use strict';

// @ngInject
function GroupListController($scope, $window) {
  $scope.expandedGroupId = undefined;

  // show the share link for the specified group or clear it if
  // null
  $scope.toggleShareLink = function (groupId) {
    if (!groupId || $scope.expandedGroupId === groupId) {
      $scope.expandedGroupId = undefined;
    } else {
      $scope.expandedGroupId = groupId;
    }
  };

  $scope.shouldShowShareLink = function (groupId) {
    return $scope.expandedGroupId === groupId;
  }

  $scope.sortedGroups = function () {
    return $scope.groups.all().concat().sort(function (a, b) {
      if (a.public !== b.public) {
        return a.public ? -1 : 1;
      }
      return a.name.localeCompare(b.name);
    });
  }

  $scope.leaveGroup = function (groupId) {
    var groupName = $scope.groups.get(groupId).name;
    var message = 'Are you sure you want to leave the group "' +
      groupName + '"?';
    if ($window.confirm(message)) {
      $scope.groups.leave(groupId);
    }
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

      $scope.$watch('expandedGroupId', function (activeGroupId) {
        if (activeGroupId) {
          // wait for the share link field to be revealed and then select
          // the link's text
          setTimeout(function() {
            var activeShareLinkField = elem[0].querySelector('.share-link-field[data-group-id=' + activeGroupId + ']');
            activeShareLinkField.focus();
            activeShareLinkField.select();
          }, 0);
        }
      });
    },
    restrict: 'AE',
    scope: {},
    templateUrl: 'group_list.html'
  };
};

module.exports = {
  directive: groupList,
  Controller: GroupListController
};
