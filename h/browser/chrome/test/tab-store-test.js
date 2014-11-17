describe('TabStore', function () {
  'use strict';

  var assert = chai.assert;
  var TabStore = h.TabStore;
  var store;
  var fakeLocalStorage;

  beforeEach(function () {
    fakeLocalStorage = {
      getItem: sinon.spy(function (key) { return this.data[key]; }),
      setItem: sinon.spy(),
      removeItem: sinon.spy(),
      data: {},
    };
    store = new TabStore(fakeLocalStorage);
  });

  describe('.get', function () {
    beforeEach(function () {
      fakeLocalStorage.data.state = JSON.stringify({1: 'active'});
      store.reload();
    });

    it('retrieves a key from the cache', function () {
      var value = store.get(1);
      assert.equal(value, 'active');
    });

    it('raises an error if the key cannot be found', function () {
      assert.throws(function () {
        store.get(100);
      });
    });
  });

  describe('.set', function () {
    it('inserts a JSON string into the store for the tab id', function () {
      var expected = JSON.stringify({1: 'active'});
      store.set(1, 'active');
      sinon.assert.calledWith(fakeLocalStorage.setItem, 'state', expected);
    });

    it('adds new properties to the serialized object with each new call', function () {
      var expected = JSON.stringify({1: 'active', 2: 'inactive'});
      store.set(1, 'active');
      store.set(2, 'inactive');
      sinon.assert.calledWith(fakeLocalStorage.setItem, 'state', expected);
    });

    it('overrides existing properties on the serialized object', function () {
      var expected = JSON.stringify({1: 'inactive'});
      store.set(1, 'active');
      store.set(1, 'inactive');
      sinon.assert.calledWith(fakeLocalStorage.setItem, 'state', expected);
    });
  });

  describe('.unset', function () {
    beforeEach(function () {
      fakeLocalStorage.data.state = JSON.stringify({1: 'active'});
      store.reload();
    });

    it('removes a property from the serialized object', function () {
      store.unset(1);
      sinon.assert.called(fakeLocalStorage.setItem, '{}');
    });
  });

  describe('.all', function () {
    beforeEach(function () {
      fakeLocalStorage.data.state = JSON.stringify({1: 'active'});
      store.reload();
    });

    it('returns all items as an Object', function () {
      var all = store.all();
      assert.deepEqual(all, {1: 'active'});
    });
  });
});
