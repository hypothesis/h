describe('HypothesisChromeExtension', function () {
  'use strict';

  var sandbox = sinon.sandbox.create();
  var HypothesisChromeExtension = h.HypothesisChromeExtension;
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
    fakeChromeTabs = {};
    fakeChromeBrowserAction = {};
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
    };
    fakeTabErrorCache = {
      getTabError: sandbox.stub(),
      setTabError: sandbox.stub(),
      unsetTabError: sandbox.stub(),
    };
    fakeBrowserAction = {
      setState: sandbox.spy(),
      activate: sandbox.spy(),
      deactivate: sandbox.spy(),
    };
    fakeSidebarInjector = {
      injectIntoTab: sandbox.stub().returns(Promise.resolve()),
      removeFromTab: sandbox.stub().returns(Promise.resolve()),
    };

    sandbox.stub(h, 'HelpPage').returns(fakeHelpPage);
    sandbox.stub(h, 'TabStore').returns(fakeTabStore);
    sandbox.stub(h, 'TabState').returns(fakeTabState);
    sandbox.stub(h, 'TabErrorCache').returns(fakeTabErrorCache);
    sandbox.stub(h, 'BrowserAction').returns(fakeBrowserAction);
    sandbox.stub(h, 'SidebarInjector').returns(fakeSidebarInjector);

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

      fakeTabState.isTabActive = sandbox.stub().returns(false);
      fakeTabState.activateTab = sandbox.spy();
      fakeTabState.deactivateTab = sandbox.spy();
    });

    it('sets up the state for tabs', function () {
      tabs.push({id: 1, url: 'http://example.com'});
      ext.install();
      sinon.assert.calledWith(fakeTabState.deactivateTab, 1);
    });

    it('sets up the state for existing tabs', function () {
      fakeTabState.isTabActive.returns(true);
      tabs.push({id: 1, url: 'http://example.com'});
      ext.install();
      sinon.assert.calledWith(fakeTabState.activateTab, 1);
    });
  });

  describe('.firstRun', function () {
    beforeEach(function () {
      fakeChromeTabs.create = sandbox.stub().yields({id: 1});
    });

    it('opens a new tab pointing to the welcome page', function () {
      ext.firstRun();
      sinon.assert.called(fakeChromeTabs.create);
      sinon.assert.calledWith(fakeChromeTabs.create, {
        url: 'https://hypothes.is/welcome'
      });
    });

    it('sets the browser state to active', function () {
      ext.firstRun();
      sinon.assert.called(fakeTabState.activateTab);
      sinon.assert.calledWith(fakeTabState.activateTab, 1);
    });
  });

  describe('.listen', function () {
    var onClickedHandler;
    var onCreatedHandler;
    var onUpdatedHandler;
    var onRemovedHandler;

    beforeEach(function () {
      fakeChromeBrowserAction.onClicked = {
        addListener: sandbox.spy(function (fn) {
          onClickedHandler = fn;
        })
      };
      fakeChromeTabs.onCreated = {
        addListener: sandbox.spy(function (fn) {
          onCreatedHandler = fn;
        })
      };
      fakeChromeTabs.onUpdated = {
        addListener: sandbox.spy(function (fn) {
          onUpdatedHandler = fn;
        })
      };
      fakeChromeTabs.onRemoved = {
        addListener: sandbox.spy(function (fn) {
          onRemovedHandler = fn;
        })
      };
    });

    it('sets up event listeners', function () {
      ext.listen({addEventListener: sandbox.stub()});
      sinon.assert.called(fakeChromeBrowserAction.onClicked.addListener);
      sinon.assert.called(fakeChromeTabs.onCreated.addListener);
      sinon.assert.called(fakeChromeTabs.onUpdated.addListener);
      sinon.assert.called(fakeChromeTabs.onRemoved.addListener);
    });

    describe('when a tab is created', function () {
      beforeEach(function () {
        fakeTabState.clearTab = sandbox.spy();
        ext.listen({addEventListener: sandbox.stub()});
      });

      it('clears the new tab state', function () {
        onCreatedHandler({id: 1, url: 'http://example.com/foo.html'});
        sinon.assert.calledWith(fakeTabState.clearTab, 1);
      });
    });

    describe('when a tab is updated', function () {
      function createTab() {
        return {id: 1, url: 'http://example.com/foo.html', status: 'complete'};
      }

      beforeEach(function () {
        fakeTabState.clearTab = sandbox.spy()
        fakeTabState.restorePreviousState = sandbox.spy();
        ext.listen({addEventListener: sandbox.stub()});
      });

      it('injects the sidebar if the tab is active', function () {
        var tab = createTab();
        fakeTabState.isTabActive.withArgs(1).returns(true);
        onUpdatedHandler(tab.id, {status: 'complete'}, tab);
        sinon.assert.calledWith(fakeSidebarInjector.injectIntoTab, tab);
      });

      it('clears the tab state if the sidebar is not active', function () {
        var tab = {id: 1, url: 'http://example.com/foo.html', status: 'complete'};
        fakeTabState.isTabActive.withArgs(1).returns(false);
        onUpdatedHandler(tab.id, {status: 'complete'}, tab);
        sinon.assert.calledWith(fakeTabState.clearTab, tab.id);
      });

      it('updates the browser action to the active state when active', function () {
        var tab = createTab();
        fakeTabState.isTabActive.withArgs(1).returns(true);
        onUpdatedHandler(tab.id, {status: 'complete'}, tab);
        sinon.assert.called(fakeBrowserAction.activate);
        sinon.assert.calledWith(fakeBrowserAction.activate, tab.id);
      });

      it('updates the browser action to the inactive state when inactive', function () {
        var tab = createTab();
        fakeTabState.isTabActive.withArgs(1).returns(false);
        onUpdatedHandler(tab.id, {status: 'complete'}, tab);
        sinon.assert.calledWith(fakeBrowserAction.deactivate, tab.id);
      });

      it('restores the tab state if errored', function () {
        var tab = createTab();
        fakeTabState.isTabErrored.returns(true);
        onUpdatedHandler(tab.id, {status: 'complete'}, tab);
        sinon.assert.calledWith(fakeTabState.restorePreviousState, 1);
      });

      it('does nothing until the tab status is complete', function () {
        var tab = createTab();
        fakeTabState.isTabActive.withArgs(1).returns(true);
        onUpdatedHandler(tab.id, {status: 'loading'}, tab);
        sinon.assert.notCalled(fakeSidebarInjector.injectIntoTab);
      });
    });

    describe('when a tab is removed', function () {
      beforeEach(function () {
        fakeTabState.clearTab = sandbox.spy();
        ext.listen({addEventListener: sandbox.stub()});
      });

      it('clears the tab', function () {
        onRemovedHandler(1);
        sinon.assert.calledWith(fakeTabState.clearTab, 1);
      });
    });

    describe('when the browser icon is clicked', function () {
      beforeEach(function () {
        ext.listen({addEventListener: sandbox.stub()});
      });

      it('activate the tab if the tab is inactive', function () {
        fakeTabState.isTabInactive.returns(true);
        onClickedHandler({id: 1, url: 'http://example.com/foo.html'});
        sinon.assert.called(fakeTabState.activateTab);
        sinon.assert.calledWith(fakeTabState.activateTab, 1);
      });

      it('deactivate the tab if the tab is active', function () {
        fakeTabState.isTabActive.returns(true);
        onClickedHandler({id: 1, url: 'http://example.com/foo.html'});
        sinon.assert.called(fakeTabState.deactivateTab);
        sinon.assert.calledWith(fakeTabState.deactivateTab, 1);
      });

      describe('when a tab has an local-file error', function () {
        it('puts the tab into an errored state', function () {
          var tab = {id: 1, url: 'file://foo.html'};

          fakeTabState.isTabActive.withArgs(1).returns(true);
          fakeSidebarInjector.injectIntoTab.returns(Promise.reject(new h.LocalFileError('msg')));

          // Trigger failed render.
          onUpdatedHandler(tab.id, {status: 'complete'}, tab).then(function () {
            sinon.assert.called(fakeTabState.errorTab);
            sinon.assert.calledWith(fakeTabState.errorTab, 1);
            resolve();
          });
        });

        it('shows the local file help page', function () {
          var tab = {id: 1, url: 'file://foo.html'};

          fakeTabErrorCache.getTabError.returns(new h.LocalFileError('msg'));
          fakeTabState.isTabErrored.withArgs(1).returns(true);
          onClickedHandler(tab);

          sinon.assert.called(fakeHelpPage.showHelpForError);
          sinon.assert.calledWith(fakeHelpPage.showHelpForError, tab, sinon.match.instanceOf(h.LocalFileError));
        });
      });

      describe('when a tab has an file-access error', function () {
        it('puts the tab into an errored state', function () {
          var tab = {id: 1, url: 'file://foo.html'};

          fakeTabState.isTabActive.withArgs(1).returns(true);
          fakeSidebarInjector.injectIntoTab.returns(Promise.reject(new h.NoFileAccessError('msg')));

          // Trigger failed render.
          onUpdatedHandler(tab.id, {status: 'complete'}, tab).then(function () {
            sinon.assert.called(fakeTabState.errorTab);
            sinon.assert.calledWith(fakeTabState.errorTab, 1);
          });
        });

        it('shows the local file help page', function () {
          var tab = {id: 1, url: 'file://foo.html'};

          fakeTabErrorCache.getTabError.returns(new h.NoFileAccessError('msg'));
          fakeTabState.isTabErrored.withArgs(1).returns(true);
          onClickedHandler(tab);

          sinon.assert.called(fakeHelpPage.showHelpForError);
          sinon.assert.calledWith(fakeHelpPage.showHelpForError, tab, sinon.match.instanceOf(h.NoFileAccessError));
        });
      });

      describe('when a tab has an chrome error', function () {
        it('puts the tab into an errored state', function () {
          var tab = {id: 1, url: 'file://foo.html'};

          fakeTabState.isTabActive.withArgs(1).returns(true);
          fakeSidebarInjector.injectIntoTab.returns(Promise.reject(new h.RestrictedProtocolError('msg')));

          // Trigger failed render.
          onUpdatedHandler(tab.id, {status: 'complete'}, tab).then(function () {
            sinon.assert.called(fakeTabState.errorTab);
            sinon.assert.calledWith(fakeTabState.errorTab, 1);
          });
        });

        it('shows the local file help page', function () {
          var tab = {id: 1, url: 'file://foo.html'};

          fakeTabErrorCache.getTabError.returns(new h.RestrictedProtocolError('msg'));
          fakeTabState.isTabErrored.withArgs(1).returns(true);
          onClickedHandler(tab);

          sinon.assert.called(fakeHelpPage.showHelpForError);
          sinon.assert.calledWith(fakeHelpPage.showHelpForError, tab, sinon.match.instanceOf(h.RestrictedProtocolError));
        });
      });

    });
  });

  describe('TabState.onchange', function () {
    var onChangeHandler;
    var tab;

    beforeEach(function () {
      tab = {id: 1, status: 'complete'};
      fakeChromeTabs.get = sandbox.stub().yields(tab);
      onChangeHandler = h.TabState.lastCall.args[1];
    });

    it('updates the browser icon', function () {
      onChangeHandler(1, 'active', 'inactive');
      sinon.assert.calledWith(fakeBrowserAction.setState, 1, 'active');
    });

    it('updates the TabStore if the tab has not errored', function () {
      onChangeHandler(1, 'active', 'inactive');
      sinon.assert.calledWith(fakeTabStore.set, 1, 'active');
    });

    it('does not update the TabStore if the tab has errored', function () {
      fakeTabState.isTabErrored.returns(true);
      onChangeHandler(1, 'errored', 'inactive');
      sinon.assert.notCalled(fakeTabStore.set);
    });

    it('injects the sidebar if the tab has been activated', function () {
      fakeTabState.isTabActive.returns(true);
      onChangeHandler(1, 'active', 'inactive');
      sinon.assert.calledWith(fakeSidebarInjector.injectIntoTab, tab);
    });

    it('removes the sidebar if the tab has been deactivated', function () {
      fakeTabState.isTabInactive.returns(true);
      onChangeHandler(1, 'inactive', 'active');
      sinon.assert.calledWith(fakeSidebarInjector.removeFromTab, tab);
    });

    it('does nothing with the sidebar if the tab is errored', function () {
      fakeTabState.isTabErrored.returns(true);
      onChangeHandler(1, 'errored', 'inactive');
      sinon.assert.notCalled(fakeSidebarInjector.injectIntoTab);
      sinon.assert.notCalled(fakeSidebarInjector.removeFromTab);
    });

    it('does nothing if the tab is still loading', function () {
      fakeChromeTabs.get = sandbox.stub().yields({id: 1, status: 'loading'});
      onChangeHandler(1, 'active', 'inactive');
      sinon.assert.notCalled(fakeSidebarInjector.injectIntoTab);
    });

    it('removes the tab from the store if the tab was closed', function () {
      onChangeHandler(1, null, 'inactive');
      sinon.assert.called(fakeTabStore.unset);
      sinon.assert.calledWith(fakeTabStore.unset);
    });

    describe('when a tab with an error is updated', function () {
      it('resets the tab error state when no longer errored', function () {
        var tab = {id: 1, url: 'file://foo.html', status: 'complete'};
        onChangeHandler(1, 'active', 'errored');
        sinon.assert.called(fakeTabErrorCache.unsetTabError);
        sinon.assert.calledWith(fakeTabErrorCache.unsetTabError, 1);
      });

      it('resets the tab error state when the tab is closed', function () {
        var tab = {id: 1, url: 'file://foo.html', status: 'complete'};
        onChangeHandler(1, null, 'errored');
        sinon.assert.called(fakeTabErrorCache.unsetTabError);
        sinon.assert.calledWith(fakeTabErrorCache.unsetTabError, 1);
      });
    });
  });
});
