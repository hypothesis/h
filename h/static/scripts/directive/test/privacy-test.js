'use strict';

var PrivacyController = require('../privacy').Controller;

describe('PrivacyController', function () {
  var fakeScope;
  var fakeLocalStorage;
  var sandbox;


  beforeEach(function () {
    sandbox = sinon.sandbox.create();

    fakeScope = {
      annotation: {
        group: sandbox.stub().returns({name: 'Everyone', public: true}),
        isPrivate: sandbox.stub().returns(false),
        isShared: sandbox.stub().returns(false),
        setPrivate: sandbox.spy(),
        setShared: sandbox.spy()
      }
    };

    fakeLocalStorage = {
      setItem: sandbox.stub(),
      getItem: sandbox.stub()
    };
  });

  afterEach(function () {
    sandbox.restore();
  });

  function controller() {
    return new PrivacyController(fakeScope, fakeLocalStorage);
  }

  describe('.shared()', function () {
    it('returns a correct descriptor for the public group', function () {
      var c = controller();

      var result = c.shared();

      assert.deepEqual(result, {name: 'Everyone', type: 'public'});
    });

    it('returns a correct descriptor for non-public groups', function () {
      var c = controller();
      fakeScope.annotation.group.returns({name: 'Foo'})

      var result = c.shared();

      assert.deepEqual(result, {name: 'Foo', type: 'group'});
    });
  });

  describe('.level()', function () {
    it('returns the public level if the annotation is shared', function () {
      var c = controller();
      fakeScope.annotation.isShared.returns(true);

      var result = c.level();

      assert.equal(result.type, 'public');
    });

    it('returns the private level if the annotation is private', function () {
      var c = controller();
      fakeScope.annotation.isPrivate.returns(true);

      var result = c.level();

      assert.equal(result.type, 'private');
    });

    it('falls back to localStorage if the annotation is new (shared)', function () {
      var c = controller();
      fakeLocalStorage.getItem.returns('shared');

      var result = c.level();

      assert.equal(result.type, 'public');
    });

    it('falls back to localStorage if the annotation is new (private)', function () {
      var c = controller();
      fakeLocalStorage.getItem.returns('private');

      var result = c.level();

      assert.equal(result.type, 'private');
    });

    it('calls setLevel if the annotation is new to update the model', function () {
      var c = controller();
      sandbox.spy(c, 'setLevel');

      c.level();

      assert.calledWith(c.setLevel, 'shared');
    });

    it('ignores junk data in localStorage', function () {
      var c = controller();
      fakeLocalStorage.getItem.returns('aslkdhasdug');

      var result = c.level();

      assert.equal(result.type, 'public');
    });

    it('falls back to the public level by default', function () {
      var c = controller();

      var result = c.level();

      assert.equal(result.type, 'public');
    });
  });

  describe('.setLevel()', function () {
    it('sets the controller state', function () {
      var c = controller();

      c.setLevel('shared');

      assert.equal(c.level().type, 'public');

      c.setLevel('private');

      assert.equal(c.level().type, 'private');
    });

    it('calls setShared on the annotation when setting level to shared', function () {
      var c = controller();

      c.setLevel('shared');

      assert.calledOnce(fakeScope.annotation.setShared);
    });

    it('calls setPrivate on the annotation when setting level to private', function () {
      var c = controller();

      c.setLevel('private');

      assert.calledOnce(fakeScope.annotation.setPrivate);
    });

    it('stores the last permissions state in localStorage', function () {
      var c = controller();

      c.setLevel('shared');

      assert.calledWithMatch(fakeLocalStorage.setItem,
                             sinon.match.any,
                             'shared');

      c.setLevel('private');

      assert.calledWithMatch(fakeLocalStorage.setItem,
                             sinon.match.any,
                             'private');
    });
  });
});
