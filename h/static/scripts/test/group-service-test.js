'use strict';

// Return an instance of the group service.
var getGroupService = function(session) {
  return require('../group-service')(session);
};

// Return a mock session service containing three groups.
var sessionWithThreeGroups = function() {
  return {
    state: {
      groups: [
        {name: 'Group 1', hashid: 'hashid1'},
        {name: 'Group 2', hashid: 'hashid2'},
        {name: 'Group 3', hashid: 'hashid3'},
      ]
    }
  };
};

describe('GroupService', function() {

  describe('.groups() method', function() {

    context("the session doesn't contain any groups", function() {
      it('returns just the public group', function() {
        var session = {state: {groups: []}};

        var groups = getGroupService(session).groups();

        assert(groups.length === 1);
        assert(groups[0].name === 'Public');
        assert(groups[0].hashid === '__public__');
      });
    });

    context("the session contains some groups", function() {
      it('returns the public group and the session groups', function() {
        var groups = getGroupService(sessionWithThreeGroups()).groups();

        assert(groups.length === 4);
        assert(groups[0].name === 'Public');
        assert(groups[0].hashid === '__public__');
        assert(groups[1].name === 'Group 1');
        assert(groups[1].hashid === 'hashid1');
        assert(groups[2].name === 'Group 2');
        assert(groups[2].hashid === 'hashid2');
        assert(groups[3].name === 'Group 3');
        assert(groups[3].hashid === 'hashid3');
      });
    });
  });

  describe('.getGroup() method', function() {
    it('returns the requested group', function() {
      var groupService = getGroupService(sessionWithThreeGroups());

      var group = groupService.getGroup('hashid2');

      assert(group.hashid === 'hashid2');
    });

    it("returns undefined if the group doesn't exist", function() {
      var groupService = getGroupService(sessionWithThreeGroups());

      assert(groupService.getGroup('foobae') === undefined);
    });
  });

  describe('.focusedGroup() method', function() {
    it('returns the focused group', function() {
      var groupService = getGroupService(sessionWithThreeGroups());
      groupService.focusGroup('hashid2');

      assert(groupService.focusedGroup().hashid === 'hashid2');
    });

    it('returns the public group initially', function() {
      var groupService = getGroupService(sessionWithThreeGroups());

      assert(groupService.focusedGroup().hashid === '__public__');
    });
  });

  describe('.focusGroup() method', function() {
    it('sets .focusedGroup() to the named group', function() {
      var groupService = getGroupService(sessionWithThreeGroups());

      groupService.focusGroup('hashid2');

      assert(groupService.focusedGroup().hashid === 'hashid2');
    });

    it('can set .focusedGroup() to the public group', function() {
      var groupService = getGroupService(sessionWithThreeGroups());
      groupService.focusGroup('hashid2');

      groupService.focusGroup('__public__');

      assert(groupService.focusedGroup().hashid === '__public__');
      assert(groupService.focusedGroup().name === 'Public');
    });

    it("does nothing if the named group isn't recognised", function() {
      var groupService = getGroupService(sessionWithThreeGroups());

      groupService.focusGroup('foobar');

      assert(groupService.focusedGroup().hashid === '__public__');
    });
  });
});
