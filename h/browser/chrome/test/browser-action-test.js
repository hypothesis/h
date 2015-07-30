describe('BrowserAction', function () {
  'use strict';

  var BrowserAction = h.BrowserAction;
  var TabState = h.TabState;
  var action;
  var fakeChromeBrowserAction;

  beforeEach(function () {
    fakeChromeBrowserAction = {
      setIcon: sinon.spy(),
      setTitle: sinon.spy(),
      setBadgeText: sinon.spy(),
    };
    action = new BrowserAction(fakeChromeBrowserAction);
  });

  describe('.activate', function () {
    it('sets the active browser icon', function () {
      var spy = fakeChromeBrowserAction.setIcon;
      action.activate(1);
      assert.calledWith(spy, {
        tabId: 1,
        path: BrowserAction.icons[TabState.states.ACTIVE],
      });
    });

    it('sets the title of the browser icon', function () {
      var spy = fakeChromeBrowserAction.setTitle;
      action.activate(1);
      assert.calledWith(spy, {
        tabId: 1,
        title: 'Hypothesis is active'
      });
    });
  });

  describe('.deactivate', function () {
    it('sets the inactive browser icon', function () {
      var spy = fakeChromeBrowserAction.setIcon;
      action.deactivate(1);
      assert.calledWith(spy, {
        tabId: 1,
        path: BrowserAction.icons[TabState.states.INACTIVE],
      });
    });

    it('sets the title of the browser icon', function () {
      var spy = fakeChromeBrowserAction.setTitle;
      action.deactivate(1);
      assert.calledWith(spy, {
        tabId: 1,
        title: 'Hypothesis is inactive'
      });
    });
  });

  describe('.error', function () {
    it('sets the inactive browser icon', function () {
      var spy = fakeChromeBrowserAction.setIcon;
      action.error(1);
      assert.calledWith(spy, {
        tabId: 1,
        path: BrowserAction.icons[TabState.states.INACTIVE],
      });
    });

    it('sets the title of the browser icon', function () {
      var spy = fakeChromeBrowserAction.setTitle;
      action.error(1);
      assert.calledWith(spy, {
        tabId: 1,
        title: 'Hypothesis has failed to load'
      });
    });

    it('shows a badge', function () {
      var spy = fakeChromeBrowserAction.setBadgeText;
      action.error(1);
      assert.calledWith(spy, {
        tabId: 1,
        text: '!'
      });
    });
  });

  describe('.setState', function () {
    it('allows the state to be set via a constant', function () {
      var spy = fakeChromeBrowserAction.setIcon;
      action.setState(1, TabState.states.ACTIVE);
      assert.calledWith(spy, {
        tabId: 1,
        path: BrowserAction.icons[TabState.states.ACTIVE],
      });
    });
  });
});
