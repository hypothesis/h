'use strict';

// Return the $controller service from Angular.
var getControllerService = function() {
  var $controller = null;
  angular.mock.inject(function(_$controller_) {
    $controller = _$controller_;
  });
  return $controller;
};

describe('GroupListController', function() {

  before(function() {
    angular.module('h')
      .controller('GroupListController', require('../group-list-controller'));
  });

  beforeEach(angular.mock.module('h'));

  var createExampleController = function(group) {
    var locals = {
      group: group || {}
    };
    locals.ctrl = getControllerService()('GroupListController', locals);
    return locals;
  };

  describe('groups', function() {

    it('calls group.groups() once', function() {
      var mockGroupService = {
        groups: sinon.spy()
      };
      var ctrl = createExampleController(mockGroupService).ctrl;

      ctrl.groups();

      assert(mockGroupService.groups.calledOnce);
      assert(mockGroupService.groups.firstCall.args.length === 0);
    });

    it('returns group.groups()', function() {
      var mockGroupService = {
        groups: function() { return 'sentinel'; }
      };
      var ctrl = createExampleController(mockGroupService).ctrl;

      assert.equal(ctrl.groups(), 'sentinel');
    });
  });

  describe('focusedGroup', function() {

    it('calls group.focusedGroup() once', function() {
      var mockGroupService = {
        focusedGroup: sinon.spy()
      };
      var ctrl = createExampleController(mockGroupService).ctrl;

      ctrl.focusedGroup();

      assert(mockGroupService.focusedGroup.calledOnce);
      assert(mockGroupService.focusedGroup.firstCall.args.length === 0);
    });

    it('returns group.focusedGroup()', function() {
      var mockGroupService = {
        focusedGroup: function() { return 'sentinel'; }
      };
      var ctrl = createExampleController(mockGroupService).ctrl;

      assert.equal(ctrl.focusedGroup(), 'sentinel');
    });
  });

  describe('focusGroup', function() {

    it('calls group.focusGroup() with the hashid', function() {
      var mockGroupService = {
        focusGroup: sinon.spy()
      };
      var ctrl = createExampleController(mockGroupService).ctrl;

      ctrl.focusGroup('test-hashid');

      assert(mockGroupService.focusGroup.calledOnce);
      assert(mockGroupService.focusGroup.firstCall.args.length === 1);
      assert(mockGroupService.focusGroup.firstCall.args[0] === 'test-hashid');
    });

    it('returns group.focusGroup()', function() {
      var mockGroupService = {
        focusGroup: function() { return 'sentinel'; }
      };
      var ctrl = createExampleController(mockGroupService).ctrl;

      assert.equal(ctrl.focusGroup(), 'sentinel');
    });
  });
});
