'use strict';

// @ngInject
function GroupsListController($scope) {
  $scope.expandedGroupId = undefined;

  // used to keep the dropdown from closing when the user
  // interacts with the inline link share pane within the groups list
  $scope.stopClickPropagation = function($event) {
    $event.stopPropagation();
  }

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
}

/**
 * @ngdoc directive
 * @name groupList
 * @restrict AE
 * @description Displays a list of groups of which the user is a member.
 */
// @ngInject
function groupsList(groups, $window) {
  return {
    controller: GroupsListController,
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
  directive: groupsList,
  _Controller: GroupsListController
};
