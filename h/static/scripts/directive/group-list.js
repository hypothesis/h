'use strict';

var assert = require('assert');

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

  $scope.linkForGroup = function (groupId) {
    return $scope.baseURI + 'groups/' + groupId;
  }
}

/**
 * @ngdoc directive
 * @name groupList
 * @restrict AE
 * @description Displays a list of groups of which the user is a member.
 */
// @ngInject
module.exports = function (groups) {
  return {
    controller: ['$scope', GroupsListController],
    link: function ($scope, elem, attrs) {
      $scope.groups = groups;

      // set the base URI used later to construct the sharing
      // link for the group
      $scope.baseURI = elem[0].ownerDocument.baseURI;

      $scope.$watch('expandedGroupId', function (activeGroupId) {
        if (activeGroupId) {
          // wait for the share link field to be revealed and then select
          // the link's text
          setTimeout(function() {
            var activeShareLinkField = elem[0].querySelector('.share-link-field[data-group-id=' + activeGroupId + ']');
            assert(activeShareLinkField);
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
