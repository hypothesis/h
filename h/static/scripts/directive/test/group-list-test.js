'use strict';

var events = require('../../events');
var groupList = require('../group-list');
var util = require('./util');

describe('GroupListController', function () {
  var controller;
  var $scope;

  beforeEach(function () {
    $scope = {
      $on: sinon.stub(),
      $apply: sinon.stub(),
    };
    var fakeWindow = {};
    var fakeGroups = {
      all: sinon.stub(),
      focused: sinon.stub(),
    };
    controller = new groupList.Controller($scope, fakeWindow, fakeGroups);
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

describe('groupList', function () {
  var $rootScope;
  var $window;

  var GROUP_LINK = 'https://hypothes.is/groups/hdevs';

  var groups;
  var fakeGroups;

  before(function() {
    angular.module('app', [])
      .directive('groupList', groupList.directive)
      .factory('groups', function () {
        return fakeGroups;
      });
  });

  beforeEach(function () {
    angular.mock.module('app');
    angular.mock.module('h.templates');
  });

  beforeEach(angular.mock.inject(function (_$rootScope_, _$window_) {
    $rootScope = _$rootScope_;
    $window = _$window_;

    groups = [{
       id: 'public',
       public: true
    },{
       id: 'h-devs',
       name: 'Hypothesis Developers',
       url: GROUP_LINK
    }];

    fakeGroups = {
      all: function () {
        return groups;
      },
      get: function (id) {
        var match = this.all().filter(function (group) {
          return group.id === id;
        });
        return match.length > 0 ? match[0] : undefined;
      },
      leave: sinon.stub(),
      focus: sinon.stub(),
      focused: sinon.stub(),
    };
  }));

  function createGroupList() {
    return util.createDirective(document, 'groupList', {
      auth: {
        status: 'signed-in',
      },
    });
  }

  it('should render groups', function () {
    var element = createGroupList();
    var groupItems = element.find('.group-item');
    assert.equal(groupItems.length, groups.length + 1);
  });

  it('should render share links', function () {
    var element = createGroupList();
    var shareLinks = element.find('.share-link-container');
    assert.equal(shareLinks.length, 1);

    var link = element.find('.share-link');
    assert.equal(link.length, 1);
    assert.equal(link[0].href, GROUP_LINK);
  });

  function clickLeaveIcon(element, acceptPrompt) {
    var leaveLink = element.find('.h-icon-cancel-outline');

    // accept prompt to leave group
    $window.confirm = function () {
      return acceptPrompt;
    };
    leaveLink.click();
  }

  it('should leave group when the leave icon is clicked', function () {
    var element = createGroupList();
    clickLeaveIcon(element, true);
    assert.ok(fakeGroups.leave.calledWith('h-devs'));
  });

  it('should not leave group when confirmation is dismissed', function () {
    var element = createGroupList();
    clickLeaveIcon(element, false);
    assert.notCalled(fakeGroups.leave);
  });

  it('should not change the focused group when leaving', function () {
    var element = createGroupList();
    clickLeaveIcon(element, true);
    assert.notCalled(fakeGroups.focus);
  });
});
