'use strict';

var proxyquire = require('proxyquire');

var TabState = require('../lib/tab-state');

describe('TabState', function () {
  var states = TabState.states;

  var state;
  var onChange;

  beforeEach(function () {
    onChange = sinon.spy();
    state = new TabState({
      1: {state: states.ACTIVE}
    }, onChange);
  });

  it('can be initialized without any default state', function () {
    assert.doesNotThrow(function () {
      state = new TabState(null, onChange);
      state.isTabActive(1);
    });
  });

  it('can be initialized without an onchange callback', function () {
    assert.doesNotThrow(function () {
      state = new TabState();
      state.isTabActive(1);
    });
  });

  describe('.load', function () {
    it('replaces the current tab states with a new object', function () {
      state.load({2: {state: states.INACTIVE}});
      assert.equal(state.isTabActive(1), false);
      assert.equal(state.isTabInactive(2), true);
    });
  });

  describe('.activateTab', function () {
    it('sets the state for the tab id provided', function () {
      state.activateTab(2);
      assert.equal(state.isTabActive(2), true);
    });

    it('triggers an onchange handler', function () {
      state.activateTab(2);
      assert.calledWith(onChange, 2, sinon.match({state: states.ACTIVE}));
    });
  });

  describe('.deactivateTab', function () {
    it('sets the state for the tab id provided', function () {
      state.deactivateTab(2);
      assert.equal(state.isTabInactive(2), true);
    });

    it('triggers an onchange handler', function () {
      state.deactivateTab(2);
      assert.calledWith(onChange, 2, sinon.match({state: states.INACTIVE}));
    });
  });

  describe('.errorTab', function () {
    it('sets the state for the tab id provided', function () {
      state.errorTab(2);
      assert.equal(state.isTabErrored(2), true);
    });

    it('triggers an onchange handler', function () {
      state.errorTab(2);
      assert.calledWith(onChange, 2, sinon.match({state: states.ERRORED}));
    });
  });

  describe('.clearTab', function () {
    it('removes the state for the tab id provided', function () {
      state.clearTab(1);
      assert.equal(state.isTabActive(1), false), 'expected isTabActive to return false';
      assert.equal(state.isTabInactive(1), true, 'expected isTabInactive to return true');
      assert.equal(state.isTabErrored(1), false, 'expected isTabInactive to return false');
    });

    it('triggers an onchange handler', function () {
      state.clearTab(1);
      assert.calledWith(onChange, 1, undefined);
    });
  });

  describe('.isTabActive', function () {
    it('returns true if the tab is active', function () {
      state.activateTab(1);
      assert.equal(state.isTabActive(1), true);
    });
  });

  describe('.isTabInactive', function () {
    it('returns true if the tab is inactive', function () {
      state.deactivateTab(1);
      assert.equal(state.isTabInactive(1), true);
    });
  });

  describe('.isTabErrored', function () {
    it('returns true if the tab is errored', function () {
      state.errorTab(1, new Error('Some error'));
      assert.equal(state.isTabErrored(1), true);
    });
  });

  describe('.setState', function () {
    it('clears the error when not errored', function () {
      state.errorTab(1, new Error('Some error'));
      assert.ok(state.getState(1).error instanceof Error);
      state.setState(1, {state: states.INACTIVE});
      assert.notOk(state.getState(1).error);
    });
  });

  describe('.updateAnnotationCount', function () {
    beforeEach(function () {
      sinon.stub(console, 'error');
    });

    afterEach(function () {
      console.error.restore();
    });

    it('queries the service and sets the annotation count', function () {
      var queryStub = sinon.stub().returns(Promise.resolve({total: 42}));
      var TabState = proxyquire('../lib/tab-state', {
        './uri-info': {
          query: queryStub,
        }
      });
      var tabState = new TabState({1: {state: states.ACTIVE}});
      return tabState.updateAnnotationCount(1, 'foobar.com')
        .then(function () {
          assert.called(queryStub);
          assert.equal(tabState.getState(1).annotationCount, 42);
        });
    });

    it('resets the count if an error occurred', function () {
      var queryStub = sinon.stub().returns(Promise.reject(new Error('err')));
      var TabState = proxyquire('../lib/tab-state', {
        './uri-info': {
          query: queryStub,
        }
      });
      var tabState = new TabState({1: {
        state: states.ACTIVE,
        annotationCount: 42,
      }});
      return tabState.updateAnnotationCount(1, 'foobar.com')
        .then(function () {
          assert.called(queryStub);
          assert.called(console.error);
          assert.equal(tabState.getState(1).annotationCount, 0);
        });
    });
  });
});
