describe('TabState', function () {
  'use strict';

  var assert = chai.assert;
  var TabState = h.TabState;
  var state;
  var onChange;

  beforeEach(function () {
    onChange = sinon.spy();
    state = new TabState({1: 'active'}, onChange);
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
      state.load({2: 'inactive'});
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
      sinon.assert.calledWith(onChange, 2, TabState.states.ACTIVE, null);
    });

    it('options.force can be used to re-trigger the current state', function () {
      state.activateTab(2);
      state.activateTab(2, {force: true});
      sinon.assert.calledWith(onChange, 2, TabState.states.ACTIVE, null);
      sinon.assert.calledTwice(onChange);
    });
  });

  describe('.deactivateTab', function () {
    it('sets the state for the tab id provided', function () {
      state.deactivateTab(2);
      assert.equal(state.isTabInactive(2), true);
    });

    it('triggers an onchange handler', function () {
      state.deactivateTab(2);
      sinon.assert.calledWith(onChange, 2, TabState.states.INACTIVE, null);
    });

    it('options.force can be used to re-trigger the current state', function () {
      state.deactivateTab(2);
      state.deactivateTab(2, {force: true});
      sinon.assert.calledWith(onChange, 2, TabState.states.INACTIVE, null);
      sinon.assert.calledTwice(onChange);
    });
  });

  describe('.errorTab', function () {
    it('sets the state for the tab id provided', function () {
      state.errorTab(2);
      assert.equal(state.isTabErrored(2), true);
    });

    it('triggers an onchange handler', function () {
      state.errorTab(2);
      sinon.assert.calledWith(onChange, 2, TabState.states.ERRORED, null);
    });

    it('options.force can be used to re-trigger the current state', function () {
      state.errorTab(2);
      state.errorTab(2, {force: true});
      sinon.assert.calledWith(onChange, 2, TabState.states.ERRORED, null);
      sinon.assert.calledTwice(onChange);
    });
  });

  describe('.clearTab', function () {
    it('removes the state for the tab id provided', function () {
      state.clearTab(1);
      assert.equal(state.isTabActive(1), false), 'expected isTabActive to return false';
      assert.equal(state.isTabInactive(1), false, 'expected isTabInactive to return false');
      assert.equal(state.isTabErrored(1), false, 'expected isTabInactive to return false');
    });

    it('triggers an onchange handler', function () {
      state.clearTab(1);
      sinon.assert.calledWith(onChange, 1, null);
    });
  });

  describe('.restorePreviousState', function () {
    it('restores the state for the tab id provided', function () {
      state.errorTab(1);
      state.restorePreviousState(1);
      assert.equal(state.isTabErrored(1), false);
      assert.equal(state.isTabActive(1), true);
    });

    it('is not possible for the previous state to be the same as the current state', function () {
      state.errorTab(1);
      state.errorTab(1);
      state.restorePreviousState(1);
      assert.equal(state.isTabErrored(1), false, 'Expected isTabErrored to return false');
      assert.equal(state.isTabActive(1), true, 'Expected isTabActive to return true');
    });

    it('if options.force is used to set the same value it ignores the value', function () {
      state.errorTab(1);
      state.deactivateTab(1);
      state.deactivateTab(1, {force: true});
      sinon.assert.calledWith(onChange, 1, TabState.states.INACTIVE, TabState.states.ERRORED);
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
      state.errorTab(1);
      assert.equal(state.isTabErrored(1), true);
    });
  });

  describe('.onchange', function () {
    it('provides the previous value to the handler', function () {
      state.errorTab(1);
      state.deactivateTab(1);
      sinon.assert.calledWith(onChange, 1, TabState.states.INACTIVE, TabState.states.ERRORED);
    });
  });
});
