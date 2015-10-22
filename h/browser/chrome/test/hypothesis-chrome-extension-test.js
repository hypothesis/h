'use strict';

var assign = require('core-js/modules/$.assign');
var proxyquire = require('proxyquire');

var errors = require('../lib/errors');
var TabState = require('../lib/tab-state');

// Creates a constructor function which takes no arguments
// and has a given prototype.
//
// Used to mock the extension modules
function createConstructor(prototype) {
  function Constructor() {
  }
  Constructor.prototype = Object.create(prototype);
  return Constructor;
}

function FakeListener() {
  this.addListener = function (callback) {
    this.listener = callback;
  };
}

describe('HypothesisChromeExtension', function () {
  var sandbox = sinon.sandbox.create();
  var HypothesisChromeExtension;
  var ext;
  var fakeChromeTabs;
  var fakeChromeBrowserAction;
  var fakeHelpPage;
  var fakeTabStore;
  var fakeTabState;
  var fakeTabErrorCache;
  var fakeBrowserAction;
  var fakeSidebarInjector;

  function createExt() {
    return new HypothesisChromeExtension({
      chromeTabs: fakeChromeTabs,
      chromeBrowserAction: fakeChromeBrowserAction,
      extensionURL: sandbox.stub(),
      isAllowedFileSchemeAccess: sandbox.stub().yields(true)
    });
  }

  beforeEach(function () {
    fakeChromeTabs = {
      onCreated: new FakeListener(),
      onUpdated: new FakeListener(),
      onReplaced: new FakeListener(),
      onRemoved: new FakeListener(),
    };
    fakeChromeBrowserAction = {
      onClicked: new FakeListener(),
    };
    fakeHelpPage = {
      showHelpForError: sandbox.spy()
    };
    fakeTabStore = {
      all: sandbox.spy(),
      set: sandbox.spy(),
      unset: sandbox.spy(),
    };
    fakeTabState = {
      activateTab: sandbox.spy(),
      deactivateTab: sandbox.spy(),
      errorTab: sandbox.spy(),
      previousState: sandbox.spy(),
      isTabActive: sandbox.stub().returns(false),
      isTabInactive: sandbox.stub().returns(false),
      isTabErrored: sandbox.stub().returns(false),
      getState: sandbox.spy(),
      setState: sandbox.spy(),
    };
    fakeTabState.deactivateTab = sinon.spy();
    fakeTabErrorCache = {
      getTabError: sandbox.stub(),
      setTabError: sandbox.stub(),
      unsetTabError: sandbox.stub(),
    };
    fakeBrowserAction = {
      update: sandbox.spy(),
    };
    fakeSidebarInjector = {
      injectIntoTab: sandbox.stub().returns(Promise.resolve()),
      removeFromTab: sandbox.stub().returns(Promise.resolve()),
    };

    function FakeTabState(initialState, onchange) {
      fakeTabState.onChangeHandler = onchange
    }
    FakeTabState.prototype = fakeTabState;

    HypothesisChromeExtension = proxyquire('../lib/hypothesis-chrome-extension', {
      './tab-state': FakeTabState,
      './tab-store': createConstructor(fakeTabStore),
      './help-page': createConstructor(fakeHelpPage),
      './tab-error-cache': createConstructor(fakeTabErrorCache),
      './browser-action': createConstructor(fakeBrowserAction),
      './sidebar-injector': createConstructor(fakeSidebarInjector),
    });

    ext = createExt();
  });

  afterEach(function () {
    sandbox.restore();
  });

  describe('.install', function () {
    var tabs;

    beforeEach(function () {
      tabs = [];
      fakeChromeTabs.query = sandbox.stub().yields(tabs);

      fakeTabState.isTabActive.returns(false);
      fakeTabState.activateTab = sandbox.spy();
      fakeTabState.deactivateTab = sandbox.spy();
    });

    it('sets up the state for tabs', function () {
      tabs.push({id: 1, url: 'http://example.com'});
      ext.install();
      assert.calledWith(fakeTabState.deactivateTab, 1);
    });

    it('sets up the state for existing tabs', function () {
      fakeTabState.isTabActive.returns(true);
      tabs.push({id: 1, url: 'http://example.com'});
      ext.install();
      assert.calledWith(fakeTabState.activateTab, 1);
    });
  });

  describe('.firstRun', function () {
    beforeEach(function () {
      fakeChromeTabs.create = sandbox.stub().yields({id: 1});
    });

    it('opens a new tab pointing to the welcome page', function () {
      ext.firstRun();
      assert.called(fakeChromeTabs.create);
      assert.calledWith(fakeChromeTabs.create, {
        url: 'https://hypothes.is/welcome'
      });
    });

    it('sets the browser state to active', function () {
      ext.firstRun();
      assert.called(fakeTabState.activateTab);
      assert.calledWith(fakeTabState.activateTab, 1);
    });
  });

  describe('.listen', function () {
    it('sets up event listeners', function () {
      ext.listen({addEventListener: sandbox.stub()});
      assert.ok(fakeChromeBrowserAction.onClicked.listener);
      assert.ok(fakeChromeTabs.onCreated.listener);
      assert.ok(fakeChromeTabs.onUpdated.listener);
      assert.ok(fakeChromeTabs.onRemoved.listener);
    });

    describe('when a tab is created', function () {
      beforeEach(function () {
        fakeTabState.clearTab = sandbox.spy();
        ext.listen({addEventListener: sandbox.stub()});
      });

      it('clears the new tab state', function () {
        fakeChromeTabs.onCreated.listener({id: 1, url: 'http://example.com/foo.html'});
        assert.calledWith(fakeTabState.clearTab, 1);
      });
    });

    describe('when a tab is updated', function () {
      var tabState = {};
      function createTab(initialState) {
        var tabId = 1;
        tabState[tabId] = assign({
          state: TabState.states.INACTIVE,
          annotationCount: 0,
          ready: false,
        }, initialState);
        return {id: tabId, url: 'http://example.com/foo.html', status: 'complete'};
      }

      beforeEach(function () {
        fakeTabState.clearTab = sandbox.spy()
        fakeTabState.restorePreviousState = sandbox.spy();
        fakeTabState.isTabActive = function (tabId) {
          return tabState[tabId].state === TabState.states.ACTIVE;
        };
        fakeTabState.isTabErrored = function (tabId) {
          return tabState[tabId].state === TabState.states.ERRORED;
        }
        fakeTabState.getState = function (tabId) {
          return tabState[tabId];
        };
        fakeTabState.setState = function (tabId, state) {
          tabState[tabId] = assign(tabState[tabId], state);
        };
        ext.listen({addEventListener: sandbox.stub()});
      });

      it('sets the tab state to ready when loading completes', function () {
        var tab = createTab({state: TabState.states.ACTIVE});
        fakeChromeTabs.onUpdated.listener(tab.id, {status: 'complete'}, tab);
        assert.equal(tabState[tab.id].ready, true);
      });

      it('resets the tab state when loading', function () {
        var tab = createTab({
          state: TabState.states.ACTIVE,
          ready: true,
          extensionSidebarInstalled: true,
        });
        fakeChromeTabs.onUpdated.listener(tab.id, {status: 'loading'}, tab);
        assert.equal(tabState[tab.id].ready, false);
        assert.equal(tabState[tab.id].extensionSidebarInstalled, false);
      });

      it('resets the tab state to active if errored', function () {
        var tab = createTab({state: TabState.states.ERRORED});
        fakeChromeTabs.onUpdated.listener(tab.id, {status: 'loading'}, tab);
        assert.equal(tabState[tab.id].state, TabState.states.ACTIVE);
      });
    });

    describe('when a tab is removed', function () {
      beforeEach(function () {
        fakeTabState.clearTab = sandbox.spy();
        ext.listen({addEventListener: sandbox.stub()});
      });

      it('clears the tab', function () {
        fakeChromeTabs.onRemoved.listener(1);
        assert.calledWith(fakeTabState.clearTab, 1);
      });
    });

    describe('when the browser icon is clicked', function () {
      beforeEach(function () {
        ext.listen({addEventListener: sandbox.stub()});
      });

      it('activate the tab if the tab is inactive', function () {
        fakeTabState.isTabInactive.returns(true);
        fakeChromeBrowserAction.onClicked.listener({id: 1, url: 'http://example.com/foo.html'});
        assert.called(fakeTabState.activateTab);
        assert.calledWith(fakeTabState.activateTab, 1);
      });

      it('deactivate the tab if the tab is active', function () {
        fakeTabState.isTabActive.returns(true);
        fakeChromeBrowserAction.onClicked.listener({id: 1, url: 'http://example.com/foo.html'});
        assert.called(fakeTabState.deactivateTab);
        assert.calledWith(fakeTabState.deactivateTab, 1);
      });
    });
  });

  describe('when injection fails', function () {
    function triggerInstall() {
      var tab = {id: 1, url: 'file://foo.html', status: 'complete'};
      var tabState = {
        state: TabState.states.ACTIVE,
        extensionSidebarInstalled: false,
        ready: true,
      };
      fakeChromeTabs.get = function (tabId, callback) {
        callback(tab);
      };
      fakeTabState.isTabActive.withArgs(1).returns(true);
      fakeTabState.getState = sandbox.stub().returns(tabState);
      fakeTabState.onChangeHandler(tab.id, tabState, null);
    }

    beforeEach(function () {
      ext.listen({addEventListener: sandbox.stub()});
    });

    var injectErrorCases = [
      errors.LocalFileError,
      errors.NoFileAccessError,
      errors.RestrictedProtocolError
    ];

    injectErrorCases.forEach(function (ErrorType) {
      describe('with ' + ErrorType.name, function () {
        it('puts the tab into an errored state', function (done) {
          var injectError = Promise.reject(new ErrorType('msg'));
          fakeSidebarInjector.injectIntoTab.returns(injectError);

          triggerInstall();

          injectError.catch(function () {
            assert.called(fakeTabState.errorTab);
            assert.calledWith(fakeTabState.errorTab, 1);
            done();
          });
        });

        it('shows the help page for ' + ErrorType.name, function () {
          var tab = {id: 1, url: 'file://foo.html'};

          fakeTabErrorCache.getTabError.returns(new ErrorType('msg'));
          fakeTabState.isTabErrored.withArgs(1).returns(true);
          fakeChromeBrowserAction.onClicked.listener(tab);

          assert.called(fakeHelpPage.showHelpForError);
          assert.calledWith(fakeHelpPage.showHelpForError, tab,
            sinon.match.instanceOf(ErrorType));
        });
      });
    });
  });

  describe('TabState.onchange', function () {
    var tabStates = TabState.states;

    var onChangeHandler;
    var tab;

    // simulate a tab state change from 'prev' to 'current'
    function onTabStateChange(current, prev) {
      onChangeHandler(1, current ? {
        state: current,
      } : null, prev ? {
        state: prev,
      } : null);
    }

    beforeEach(function () {
      tab = {id: 1, status: 'complete'};
      fakeChromeTabs.get = sandbox.stub().yields(tab);
      onChangeHandler = ext._onTabStateChange
    });

    it('updates the browser icon', function () {
      fakeTabState.getState = sandbox.stub().returns({
        state: tabStates.ACTIVE,
      });
      onTabStateChange(tabStates.ACTIVE, tabStates.INACTIVE);
      assert.calledWith(fakeBrowserAction.update, 1, {
        state: tabStates.ACTIVE,
      });
    });

    it('updates the TabStore if the tab has not errored', function () {
      fakeTabState.getState = sandbox.stub().returns({
        state: tabStates.ACTIVE,
      });
      onTabStateChange(tabStates.ACTIVE, tabStates.INACTIVE);
      assert.calledWith(fakeTabStore.set, 1, {
        state: tabStates.ACTIVE,
      });
    });

    it('does not update the TabStore if the tab has errored', function () {
      fakeTabState.isTabErrored.returns(true);
      onTabStateChange(tabStates.ERRORED, tabStates.INACTIVE);
      assert.notCalled(fakeTabStore.set);
    });

    it('injects the sidebar if the tab has been activated', function () {
      fakeTabState.getState = sandbox.stub().returns({
        state: tabStates.ACTIVE,
      });
      fakeTabState.isTabActive.returns(true);
      onTabStateChange(tabStates.ACTIVE, tabStates.INACTIVE);
      assert.calledWith(fakeSidebarInjector.injectIntoTab, tab);
    });

    it('removes the sidebar if the tab has been deactivated', function () {
      fakeTabState.getState = sandbox.stub().returns({
        state: tabStates.INACTIVE,
        extensionSidebarInstalled: true,
      });
      fakeTabState.isTabInactive.returns(true);
      fakeChromeTabs.get = sandbox.stub().yields({
        id: 1,
        status: 'complete',
      })
      onTabStateChange(tabStates.INACTIVE, tabStates.ACTIVE);
      assert.calledWith(fakeSidebarInjector.removeFromTab, tab);
    });

    it('does nothing with the sidebar if the tab is errored', function () {
      fakeTabState.isTabErrored.returns(true);
      onTabStateChange(tabStates.ERRORED, tabStates.INACTIVE);
      assert.notCalled(fakeSidebarInjector.injectIntoTab);
      assert.notCalled(fakeSidebarInjector.removeFromTab);
    });

    it('does nothing if the tab is still loading', function () {
      fakeChromeTabs.get = sandbox.stub().yields({id: 1, status: 'loading'});
      onTabStateChange(tabStates.ACTIVE, tabStates.INACTIVE);
      assert.notCalled(fakeSidebarInjector.injectIntoTab);
    });

    it('removes the tab from the store if the tab was closed', function () {
      onTabStateChange(null, tabStates.INACTIVE);
      assert.called(fakeTabStore.unset);
      assert.calledWith(fakeTabStore.unset);
    });

    describe('when a tab with an error is updated', function () {
      beforeEach(function () {
        fakeTabState.getState = sandbox.stub().returns({
          state: tabStates.ERRORED,
          extensionSidebarInstalled: false,
        });
      });

      it('resets the tab error state when no longer errored', function () {
        var tab = {id: 1, url: 'file://foo.html', status: 'complete'};
        onTabStateChange(tabStates.ACTIVE, tabStates.ERRORED);
        assert.called(fakeTabErrorCache.unsetTabError);
        assert.calledWith(fakeTabErrorCache.unsetTabError, 1);
      });

      it('resets the tab error state when the tab is closed', function () {
        var tab = {id: 1, url: 'file://foo.html', status: 'complete'};
        onTabStateChange(null, tabStates.ERRORED);
        assert.called(fakeTabErrorCache.unsetTabError);
        assert.calledWith(fakeTabErrorCache.unsetTabError, 1);
      });
    });
  });
});
