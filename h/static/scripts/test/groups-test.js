'use strict';

var groups = require('../groups');

// Return a mock session service containing three groups.
var sessionWithThreeGroups = function() {
  return {
    state: {
      groups: [
        {name: 'Group 1', hashid: 'id1'},
        {name: 'Group 2', hashid: 'id2'},
        {name: 'Group 3', hashid: 'id3'},
      ]
    }
  };
};


describe('groups', function() {
  var fakeSession;
  var fakeLocalStorage;
  var sandbox;

  beforeEach(function () {
    sandbox = sinon.sandbox.create();

    fakeSession = sessionWithThreeGroups();
    fakeLocalStorage = {
      getItem: sandbox.stub(),
      setItem: sandbox.stub()
    };
  });

  afterEach(function () {
    sandbox.restore();
  });

  function service() {
    return groups(fakeLocalStorage, fakeSession);
  }

  describe('.all()', function() {
    it('returns no groups if there are none in the session', function() {
      fakeSession = {state: {groups: []}};

      var groups = service().all();

      assert.equal(groups.length, 0);
    });

    it('returns the groups from the session when there are some', function() {
      var groups = service().all();

      assert.equal(groups.length, 3);
      assert.deepEqual(groups, [
        {name: 'Group 1', hashid: 'id1'},
        {name: 'Group 2', hashid: 'id2'},
        {name: 'Group 3', hashid: 'id3'}
      ]);
    });
  });

  describe('.get() method', function() {
    it('returns the requested group', function() {
      var group = service().get('id2');

      assert.equal(group.hashid, 'id2');
    });

    it("returns undefined if the group doesn't exist", function() {
      var group = service().get('foobar');

      assert.isUndefined(group);
    });
  });

  describe('.focused() method', function() {
    it('returns the focused group', function() {
      var s = service();
      s.focus('id2');

      assert.equal(s.focused().hashid, 'id2');
    });

    it('returns the first group initially', function() {
      var s = service();

      assert.equal(s.focused().hashid, 'id1');
    });

    it('returns the group selected in localStorage if available', function() {
      fakeLocalStorage.getItem.returns('id3');
      var s = service();

      assert.equal(s.focused().hashid, 'id3');
    });
  });

  describe('.focus() method', function() {
    it('sets the focused group to the named group', function() {
      var s = service();
      s.focus('id2');

      assert.equal(s.focused().hashid, 'id2');
    });

    it("does nothing if the named group isn't recognised", function() {
      var s = service();
      s.focus('foobar');

      assert.equal(s.focused().hashid, 'id1');
    });

    it("stores the focused group hashid in localStorage", function() {
      var s = service();
      s.focus('id3');

      assert.calledWithMatch(fakeLocalStorage.setItem, sinon.match.any, 'id3');
    });
  });
});
