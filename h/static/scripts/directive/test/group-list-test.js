'use strict';

var groupsList = require('../group-list');

describe('GroupsListController', function () {
  var controller;
  var $scope;

  beforeEach(function () {
    $scope = {};
    controller = new groupsList._Controller($scope);
  });

  it('toggles share links', function () {
    $scope.toggleShareLink('group-a');
    assert.equal($scope.expandedGroupId, 'group-a');
    $scope.toggleShareLink('group-a');
    assert.equal($scope.expandedGroupId, undefined);

    $scope.toggleShareLink('group-b');
    assert.equal($scope.expandedGroupId, 'group-b');
    $scope.toggleShareLink('group-c');
    assert.equal($scope.expandedGroupId, 'group-c');
  });

  it('shows share link for selected group', function () {
    assert.equal($scope.shouldShowShareLink('group-a'), false);
    $scope.toggleShareLink('group-a');
    assert.equal($scope.shouldShowShareLink('group-a'), true);
    $scope.toggleShareLink('group-b');
    assert.equal($scope.shouldShowShareLink('group-a'), false);
    assert.equal($scope.shouldShowShareLink('group-b'), true);
  });
});


// <groups-list> directive
// - check that it renders all visible groups
// - check that share links visible for non-public groups
// - check that share link is focused after toggling share link

// TODO
// - read Angular unit testing guide
// - read Angular E2E testing guides
// - grok an existing directive test
// - get a trivial <groups-list> directive test failing, then make it work
