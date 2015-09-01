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
        {name: 'Group 1', id: 'id1'},
        {name: 'Group 2', id: 'id2'},
        {name: 'Group 3', id: 'id3'},
      ]
    }
  };
};

describe('GroupService', function() {

  describe('.groups() method', function() {

    context("the session doesn't contain any groups", function() {
      it('returns no groups', function() {
        var session = {state: {groups: []}};

        var groups = getGroupService(session).groups();

        assert(groups.length === 0);
      });
    });

    context("the session contains some groups", function() {
      it('returns the groups from the session', function() {
        var groups = getGroupService(sessionWithThreeGroups()).groups();

        assert(groups.length === 3);
        assert(groups[0].name === 'Group 1');
        assert(groups[0].id === 'id1');
        assert(groups[1].name === 'Group 2');
        assert(groups[1].id === 'id2');
        assert(groups[2].name === 'Group 3');
        assert(groups[2].id === 'id3');
      });
    });
  });

  describe('.getGroup() method', function() {
    it('returns the requested group', function() {
      var groupService = getGroupService(sessionWithThreeGroups());

      var group = groupService.getGroup('id2');

      assert(group.id === 'id2');
    });

    it("returns undefined if the group doesn't exist", function() {
      var groupService = getGroupService(sessionWithThreeGroups());

      assert(groupService.getGroup('foobae') === undefined);
    });
  });

  describe('.focusedGroup() method', function() {
    it('returns the focused group', function() {
      var groupService = getGroupService(sessionWithThreeGroups());
      groupService.focusGroup('id2');

      assert(groupService.focusedGroup().id === 'id2');
    });

    it('returns the first group initially', function() {
      var groupService = getGroupService(sessionWithThreeGroups());

      assert(groupService.focusedGroup().id === 'id1');
    });
  });

  describe('.focusGroup() method', function() {
    it('sets .focusedGroup() to the named group', function() {
      var groupService = getGroupService(sessionWithThreeGroups());

      groupService.focusGroup('id2');

      assert(groupService.focusedGroup().id === 'id2');
    });

    it("does nothing if the named group isn't recognised", function() {
      var groupService = getGroupService(sessionWithThreeGroups());

      groupService.focusGroup('foobar');

      assert(groupService.focusedGroup().id === 'id1');
    });
  });
});
