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

  it('sorts groups', function () {
    $scope.groups = {
      all: function () {
        return [{
          id: 'c',
          name: 'Zebrafish Study Group'
        },{
          id: 'a',
          name: 'Antimatter Research'
        },{
          public: true
        }];
      }
    };

    var sorted = $scope.sortedGroups();
    assert.ok(sorted[0].public);
    assert.equal(sorted[1].name, 'Antimatter Research');
    assert.equal(sorted[2].name, 'Zebrafish Study Group');
  });
});

// returns true if a jQuery-like element has
// been hidden directly via an ng-show directive.
//
// This does not check whether the element is a descendant
// of a hidden element
function isElementHidden(element) {
  return element.hasClass('ng-hide');
}

describe('GroupsListDirective', function () {
  var $compile;
  var $scope;

  var GROUP_LINK = 'https://hypothes.is/groups/hdevs';

  var groups = [{
    id: 'public',
    public: true
  },{
    id: 'h-devs',
    name: 'Hypothesis Developers',
    url: GROUP_LINK
  }];

  before(function() {
    angular.module('app', [])
      .directive('groupList', groupsList.directive)
      .factory('groups', function () {
        return {
          all: function () {
            return groups;
          }
        };
      });
  });

  beforeEach(function () {
    angular.mock.module('app');
    angular.mock.module('h.templates');
  });

  beforeEach(angular.mock.inject(function (_$compile_, _$rootScope_) {
    $compile = _$compile_;
    $scope = _$rootScope_.$new();
  }));

  function createGroupsList() {
    var element = $compile('<group-list></group-list>')($scope);
    $scope.$digest();
    return element;
  }

  it('should render groups', function () {
    var element = createGroupsList();
    var groupItems = element.find('.group-item');
    assert.equal(groupItems.length, groups.length + 1);
  });

  it('should render share links', function () {
    var element = createGroupsList();
    var shareLinks = element.find('.share-link-container');
    assert.equal(shareLinks.length, 1);

    var linkField = element.find('.share-link-field');
    assert.equal(linkField.length, 1);
    assert.equal(linkField[0].value, GROUP_LINK);
  });

  it('should toggle share link on click', function () {
    var element = createGroupsList();
    var toggleLink = element.find('.share-link-toggle');
    var expander = element.find('.share-link-expander');
    assert.ok(isElementHidden(expander));
    toggleLink.click();
    assert.ok(!isElementHidden(expander));
    toggleLink.click();
    assert.ok(isElementHidden(expander));
  });
});
