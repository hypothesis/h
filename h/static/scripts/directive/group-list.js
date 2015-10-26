'use strict';

var events = require('../events');

// @ngInject
function GroupListController($scope, $window, groups) {
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
  };

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

  $scope.allGroups = groups.all();
  $scope.$on(events.GROUPS_CHANGED, function () {
    $scope.allGroups = groups.all();
  });

  $scope.focusedGroup = groups.focused();
  $scope.$on(events.GROUP_FOCUSED, function () {
    $scope.focusedGroup = groups.focused();
  });
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
      $scope.createNewGroup = function() {
        $window.open('/groups/new', '_blank');
      }

      $scope.$watch('expandedGroupId', function (activeGroupId) {
        if (activeGroupId) {
          // wait for the share link field to be revealed and then select
          // the link's text
          setTimeout(function() {
            var shareLinkSelector = '.share-link-field[data-group-id="' +
                                    activeGroupId + '"]';
            var activeShareLinkField = elem[0].querySelector(shareLinkSelector);
            activeShareLinkField.focus();
            activeShareLinkField.select();
          }, 0);
        }
      });
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
